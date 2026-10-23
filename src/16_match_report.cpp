// Giai doan 16: BAO CAO MOT LAN NHAN DANG — bang ket qua de nop cho ban giam khao.
//
// Mo phong dung mot luot truy van that: mot mau van tay di so voi toan bo co so
// du lieu, tat ca tren ban ma. Voi tung ban ghi, in ra ca hai cot de doi chieu:
//
//     khoang cach tinh tren DU LIEU GOC   vs   khoang cach tinh tren BAN MA
//
// Khong dung nguong cung. Ly do: nguong quyet dinh thuoc ve bo trich dac trung
// cua khach hang, khong phai cua lop ma hoa. Thu duoc do o day la THU TU xep
// hang — ma hoa co lam doi thu tu khong. Neu thu hang tren ban ma trung voi thu
// hang tren ban ro o moi dong, lop ma hoa khong doi mot quyet dinh nao.
//
// Chay tu thu muc device/ de phan ma hoa thiet bi tim duoc adapter_output_data:
//   cd device && ../seal_flow/build/16_match_report [ten_truy_van] [so_ban_ghi]

#include "seal/seal.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

// Thu vien thiet bi goi qua lop vo C (15_device_shim.c)
extern "C" {
size_t dev_setup(void);
bool dev_encrypt(const double *vals, size_t n, uint64_t *c0, uint64_t *c1, size_t stride);
size_t dev_last_bytes(void);
void dev_cleanup(void);
}

using namespace std;
using namespace seal;
namespace fs = std::filesystem;
using Clock  = chrono::steady_clock;

constexpr size_t FP_DIM = 512;
constexpr size_t DEGREE = 4096;

static vector<double> parse_brace_line(const string &line)
{
    vector<double> out;
    size_t l = line.find('{'), r = line.rfind('}');
    if (l == string::npos || r == string::npos) return out;
    stringstream ss(line.substr(l + 1, r - l - 1));
    string tok;
    while (getline(ss, tok, ','))
    {
        try { out.push_back(stod(tok)); } catch (...) {}
    }
    return out;
}

static string env_or(const char *key, const string &fallback)
{
    const char *v = getenv(key);
    return (v && *v) ? string(v) : fallback;
}

struct Entry
{
    string name;
    string finger;
    vector<double> plain;
    vector<vector<double>> c0, c1;
};

struct Row
{
    string name;
    string finger;
    bool same_finger;
    double d_plain, d_fhe, abs_err, rel_err;
    double t_load, t_compute, t_decrypt;
    int rank_plain, rank_fhe;
};

int main(int argc, char *argv[])
{
    string qname  = (argc > 1) ? argv[1] : "101_8";
    size_t ndb    = (argc > 2) ? (size_t)stoul(argv[2]) : 10;
    string root   = env_or("CME_ROOT", "/home/ourpi/CoreMetEncrypt");
    string ctdir  = env_or("CME_CT_DIR", root + "/seal_flow/ct_fvc");
    string bindir = env_or("CME_BIN_DIR", root + "/datasets/fvc2002_db1b/bin");
    string keydir = env_or("CME_KEY_DIR", root + "/device/adapter_output_data/");
    string csvout = env_or("CME_CSV_OUT", root + "/seal_flow/bench/match_report.csv");

    // ----------------------------------------------------------- tham so CKKS
    EncryptionParameters parms(scheme_type::ckks);
    parms.set_poly_modulus_degree(DEGREE);
    vector<seal::Modulus> moduli = {seal::Modulus(134012929), seal::Modulus(134111233),
                                    seal::Modulus(134176769),
                                    CoeffModulus::Create(DEGREE, {28})[0]};
    parms.set_coeff_modulus(moduli);
    double scale = pow(2.0, 25);

    SEALContext context(parms);
    if (!context.parameters_set()) { cout << "Tham so khong hop le\n"; return 1; }

    KeyGenerator keygen_tmp(context);
    SecretKey sk = keygen_tmp.secret_key();
    {
        ifstream f(keydir + "sk_4096_seal.dat", ios::binary);
        if (!f.is_open()) { cout << "Khong mo duoc sk\n"; return 1; }
        sk.load(context, f);
    }
    KeyGenerator keygen(context, sk);
    RelinKeys relin_keys;
    keygen.create_relin_keys(relin_keys);
    vector<int> steps;
    for (size_t s = 1; s < FP_DIM; s <<= 1) steps.push_back((int)s);
    GaloisKeys galois_keys;
    keygen.create_galois_keys(steps, galois_keys);

    Evaluator evaluator(context);
    Decryptor decryptor(context, sk);
    CKKSEncoder encoder(context);
    size_t np = context.first_context_data()->parms().coeff_modulus().size();

    // ------------------------------------------------------------ nap du lieu
    auto load_entry = [&](const string &name, Entry &e) -> bool {
        e.name   = name;
        e.finger = name.substr(0, name.find('_'));
        ifstream f(ctdir + "/" + name + ".txt");
        if (!f.is_open()) return false;
        string line;
        while (getline(f, line))
        {
            if (line.rfind("c0 :", 0) == 0) e.c0.push_back(parse_brace_line(line));
            else if (line.rfind("c1 :", 0) == 0) e.c1.push_back(parse_brace_line(line));
        }
        if (e.c0.size() < np) return false;
        ifstream b(bindir + "/" + name + ".bin", ios::binary);
        if (!b.is_open()) return false;
        e.plain.resize(FP_DIM);
        b.read((char *)e.plain.data(), FP_DIM * sizeof(double));
        return (size_t)b.gcount() == FP_DIM * sizeof(double);
    };

    Entry q;
    if (!load_entry(qname, q)) { cout << "Khong nap duoc truy van " << qname << "\n"; return 1; }

    // CSDL: toan bo mau co trong tap, tru chinh truy van. Neu so ban ghi yeu cau
    // it hon tap hien co thi lay mau dau tien cua moi ngon (*_1) de moi ngon deu
    // co dai dien — bang nho nhung van phu het so nguoi.
    vector<Entry> db;
    vector<string> names;
    for (auto &p : fs::directory_iterator(ctdir))
        if (p.path().extension() == ".txt") names.push_back(p.path().stem().string());
    sort(names.begin(), names.end());

    bool lay_het = ndb + 1 >= names.size();
    for (const auto &n : names)
    {
        if (db.size() >= ndb) break;
        if (n == qname) continue;
        if (!lay_het && (n.size() < 2 || n.substr(n.rfind('_') + 1) != "1")) continue;
        Entry e;
        if (load_entry(n, e)) db.push_back(move(e));
    }
    if (db.empty()) { cout << "CSDL rong\n"; return 1; }

    auto build = [&](const Entry &e, Ciphertext &ct) {
        ct.resize(context, context.first_parms_id(), 2);
        auto p0 = ct.data(0);
        auto p1 = ct.data(1);
        for (size_t j = 0; j < np; j++)
            for (size_t i = 0; i < DEGREE; i++)
            {
                p0[j * DEGREE + i] = (uint64_t)e.c0[j][i];
                p1[j * DEGREE + i] = (uint64_t)e.c1[j][i];
            }
        ct.is_ntt_form() = true;
        ct.scale()       = scale;
    };

    // ----------------------------- do thoi gian thiet bi ma hoa chinh truy van
    // Dung lai dung thu vien SEAL-Embedded, de con so la do that chu khong uoc tinh.
    double t_dev_encrypt = -1.0;
    size_t ct_bytes      = 0;
    if (dev_setup())
    {
        vector<uint64_t> b0(np * DEGREE, 0), b1(np * DEGREE, 0);
        dev_encrypt(q.plain.data(), FP_DIM, b0.data(), b1.data(), DEGREE);  // chay nong
        auto t0 = Clock::now();
        dev_encrypt(q.plain.data(), FP_DIM, b0.data(), b1.data(), DEGREE);
        t_dev_encrypt = chrono::duration<double, milli>(Clock::now() - t0).count();
        ct_bytes      = dev_last_bytes();
        dev_cleanup();
    }

    Ciphertext ct_q;
    build(q, ct_q);

    cout << "=================================================================\n";
    cout << " KET QUA SO KHOP VAN TAY TREN BAN MA\n";
    cout << "=================================================================\n";
    cout << " Truy van        : " << qname << "   (ngon " << q.finger << ")\n";
    cout << " Co so du lieu   : " << db.size() << " ban ghi"
         << (lay_het ? ", toan bo tap du lieu" : ", moi ngon mot mau") << "\n";
    cout << " Tham so         : CKKS degree 4096, 3 prime 27-bit, scale 2^25\n";
    if (t_dev_encrypt >= 0)
        cout << " Thiet bi ma hoa : " << fixed << setprecision(2) << t_dev_encrypt << " ms   ("
             << ct_bytes / 1024.0 << " KB gui len server)\n";
    cout << "\n";

    // ------------------------------------------------------------- so khop
    vector<Row> rows;
    for (const auto &e : db)
    {
        Row r;
        r.name        = e.name;
        r.finger      = e.finger;
        r.same_finger = (e.finger == q.finger);

        auto t0 = Clock::now();
        Ciphertext ct_e;
        build(e, ct_e);
        auto t1 = Clock::now();

        Ciphertext ct_d, ct_sq;
        evaluator.sub(ct_q, ct_e, ct_d);
        evaluator.square(ct_d, ct_sq);
        evaluator.relinearize_inplace(ct_sq, relin_keys);
        evaluator.rescale_to_next_inplace(ct_sq);
        Ciphertext ct_sum = ct_sq;
        for (size_t s = 1; s < FP_DIM; s <<= 1)
        {
            Ciphertext rot;
            evaluator.rotate_vector(ct_sum, (int)s, galois_keys, rot);
            evaluator.add_inplace(ct_sum, rot);
        }
        auto t2 = Clock::now();

        Plaintext pt;
        decryptor.decrypt(ct_sum, pt);
        vector<double> out;
        encoder.decode(pt, out);
        auto t3 = Clock::now();

        double expect = 0;
        for (size_t i = 0; i < FP_DIM; i++)
        {
            double d = q.plain[i] - e.plain[i];
            expect += d * d;
        }

        auto ms       = [](auto a, auto b) { return chrono::duration<double, milli>(b - a).count(); };
        r.d_plain     = expect;
        r.d_fhe       = out[0];
        r.abs_err     = fabs(out[0] - expect);
        r.rel_err     = expect > 0 ? r.abs_err / expect * 100.0 : 0.0;
        r.t_load      = ms(t0, t1);
        r.t_compute   = ms(t1, t2);
        r.t_decrypt   = ms(t2, t3);
        rows.push_back(r);
    }

    // Xep hang theo tung cach tinh, de xem ma hoa co lam doi thu tu khong
    auto rank_by = [&](bool use_fhe) {
        vector<size_t> idx(rows.size());
        for (size_t i = 0; i < idx.size(); i++) idx[i] = i;
        sort(idx.begin(), idx.end(), [&](size_t a, size_t b) {
            return (use_fhe ? rows[a].d_fhe : rows[a].d_plain) <
                   (use_fhe ? rows[b].d_fhe : rows[b].d_plain);
        });
        for (size_t k = 0; k < idx.size(); k++)
            (use_fhe ? rows[idx[k]].rank_fhe : rows[idx[k]].rank_plain) = (int)k + 1;
    };
    rank_by(false);
    rank_by(true);

    // ------------------------------------------------------------- in bang
    cout << left << setw(10) << "BAN GHI" << right << setw(14) << "BAN RO" << setw(14) << "BAN MA"
         << setw(12) << "SAI SO %" << setw(8) << "HANG" << setw(10) << "TINH ms" << setw(10)
         << "GIAI ms" << "  KET QUA\n";
    cout << string(90, '-') << "\n";

    vector<size_t> order(rows.size());
    for (size_t i = 0; i < order.size(); i++) order[i] = i;
    sort(order.begin(), order.end(),
         [&](size_t a, size_t b) { return rows[a].rank_fhe < rows[b].rank_fhe; });

    for (size_t k : order)
    {
        const Row &r = rows[k];
        cout << left << setw(10) << r.name << right << fixed << setprecision(3) << setw(14)
             << r.d_plain << setw(14) << r.d_fhe << setprecision(4) << setw(12) << r.rel_err
             << setw(8) << r.rank_fhe << setprecision(2) << setw(10) << r.t_compute << setw(10)
             << r.t_decrypt << "  " << (r.rank_fhe == 1 ? "GAN NHAT" : "") << "\n";
    }

    // ------------------------------------------------------------- ket luan
    size_t best_fhe = 0, best_plain = 0;
    for (size_t i = 0; i < rows.size(); i++)
    {
        if (rows[i].rank_fhe == 1) best_fhe = i;
        if (rows[i].rank_plain == 1) best_plain = i;
    }
    bool order_same = true;
    for (const auto &r : rows)
        if (r.rank_plain != r.rank_fhe) order_same = false;

    double sum_rel = 0, max_rel = 0, sum_t = 0;
    for (const auto &r : rows)
    {
        sum_rel += r.rel_err;
        max_rel = max(max_rel, r.rel_err);
        sum_t += r.t_load + r.t_compute + r.t_decrypt;
    }

    cout << "\n=================================================================\n";
    cout << " KET LUAN\n";
    cout << "=================================================================\n";
    cout << " Khop gan nhat tinh tren DU LIEU GOC : " << rows[best_plain].name << "\n";
    cout << " Khop gan nhat tinh tren BAN MA      : " << rows[best_fhe].name << "\n";
    cout << " Hai ket qua " << (best_fhe == best_plain ? "TRUNG NHAU" : "KHAC NHAU") << "\n";
    cout << " Thu tu xep hang toan bang           : "
         << (order_same ? "GIU NGUYEN (100%)" : "CO SAI LECH") << "\n";
    cout << " Truy van " << qname << " la ngon " << q.finger << ", ban ghi gan nhat la ngon "
         << rows[best_fhe].finger << (rows[best_fhe].same_finger ? "  (DUNG NGON)" : "") << "\n";
    cout << fixed << setprecision(4);
    cout << " Sai so trung binh do ma hoa         : " << sum_rel / rows.size() << " %\n";
    cout << " Sai so lon nhat                     : " << max_rel << " %\n";
    cout << setprecision(2);
    cout << " Tong thoi gian quet " << db.size() << " ban ghi      : " << sum_t << " ms\n";
    cout << "\n Server khong giai ma bat ky luc nao. Chi noi giu khoa bi mat\n";
    cout << " moi doc duoc nhung con so o cot BAN MA.\n";

    // ------------------------------------------------------------- xuat CSV
    {
        fs::create_directories(fs::path(csvout).parent_path());
        ofstream f(csvout);
        f << "idx,ban_ghi,cung_ngon,khoang_cach_ban_ro,khoang_cach_ban_ma,sai_so_tuyet_doi,"
             "sai_so_tuong_doi_pct,hang_ban_ro,hang_ban_ma,nap_ct_ms,tinh_ban_ma_ms,giai_ma_ms,"
             "tong_ms,ket_qua\n";
        int idx = 1;
        for (size_t k : order)
        {
            const Row &r = rows[k];
            f << idx++ << "," << r.name << "," << (r.same_finger ? 1 : 0) << "," << r.d_plain << ","
              << r.d_fhe << "," << r.abs_err << "," << r.rel_err << "," << r.rank_plain << ","
              << r.rank_fhe << "," << r.t_load << "," << r.t_compute << "," << r.t_decrypt << ","
              << (r.t_load + r.t_compute + r.t_decrypt) << ","
              << (r.rank_fhe == 1 ? "GAN_NHAT" : "khac") << "\n";
        }
        f << "\n#,gia_tri,don_vi\n";
        f << "truy_van," << qname << ",\n";
        f << "so_ban_ghi," << db.size() << ",\n";
        if (t_dev_encrypt >= 0) f << "thiet_bi_ma_hoa," << t_dev_encrypt << ",ms\n";
        f << "sai_so_trung_binh," << sum_rel / rows.size() << ",%\n";
        f << "sai_so_lon_nhat," << max_rel << ",%\n";
        f << "giu_thu_tu_xep_hang," << (order_same ? "100" : "khong") << ",%\n";
        cout << "\n Da ghi CSV: " << csvout << "\n";
    }
    return 0;
}
