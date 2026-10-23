// Workflow day du: mau van tay -> ma hoa tren thiet bi -> server so khop tren
// ban ma -> tra ve client giai ma va ra quyet dinh.
//
// Chay tu thu muc device/:
//   cd device && ../seal_flow/build/17_workflow [ten_truy_van] [so_ban_ghi]

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

extern "C" {
size_t dev_setup(void);
bool dev_encrypt(const double *vals, size_t n, uint64_t *c0, uint64_t *c1, size_t stride);
size_t dev_last_bytes(void);
void dev_cleanup(void);
}

#ifndef CME_ROOT
#define CME_ROOT "/home/ourpi/CoreMetEncrypt"
#endif

using namespace std;
using namespace seal;
namespace fs = std::filesystem;
using Clock = chrono::steady_clock;

constexpr size_t FP_DIM = 512;
constexpr size_t DEGREE = 4096;

static string env_or(const char *key, const string &fallback)
{
    const char *v = getenv(key);
    return (v && *v) ? string(v) : fallback;
}

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
    double d_fhe, d_plain, rel_err, ms;
    int rank_fhe, rank_plain;
};

static void banner(const string &tag, const string &who, const string &what)
{
    cout << "\n[" << tag << "] " << who << " - " << what << "\n";
    cout << string(70, '-') << "\n";
}

int main(int argc, char *argv[])
{
    string qname = (argc > 1) ? argv[1] : "04d3-103_5";
    size_t ndb   = (argc > 2) ? (size_t)stoul(argv[2]) : 10;

    string root   = env_or("CME_ROOT", CME_ROOT);
    string ctdir  = env_or("CME_CT_DIR", root + "/ct_demo");
    string bindir = env_or("CME_BIN_DIR", root + "/data");
    string keydir = env_or("CME_KEY_DIR", root + "/device/adapter_output_data/");
    string csvout = env_or("CME_CSV_OUT", root + "/bench/workflow.csv");

    EncryptionParameters parms(scheme_type::ckks);
    parms.set_poly_modulus_degree(DEGREE);
    vector<seal::Modulus> moduli = {seal::Modulus(134012929), seal::Modulus(134111233),
                                    seal::Modulus(134176769),
                                    CoeffModulus::Create(DEGREE, {28})[0]};
    parms.set_coeff_modulus(moduli);
    double scale = pow(2.0, 25);

    SEALContext context(parms);
    if (!context.parameters_set()) { cout << "Tham so khong hop le\n"; return 1; }

    SecretKey sk = KeyGenerator(context).secret_key();
    {
        ifstream f(keydir + "sk_4096_seal.dat", ios::binary);
        if (!f.is_open()) { cout << "Khong mo duoc khoa bi mat\n"; return 1; }
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

    auto load_entry = [&](const string &name, Entry &e) -> bool {
        e.name   = name;
        e.finger = name.substr(0, name.rfind('_'));
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

    cout << "==================================================================\n";
    cout << " HE THONG BAO MAT DU LIEU VAN TAY - MOT LUOT XAC THUC\n";
    cout << "==================================================================\n";

    // ---------------------------------------------------- 1. client doc mau
    banner("1", "CLIENT", "doc mau van tay can so khop");

    Entry q;
    if (!load_entry(qname, q)) { cout << "Khong nap duoc truy van " << qname << "\n"; return 1; }

    cout << " Mau can so khop    : " << qname << "\n";
    cout << " Vector dac trung   : " << FP_DIM << " chieu, " << FP_DIM * sizeof(double)
         << " byte\n";
    cout << " Trang thai         : ban ro, dang nam tren thiet bi\n";

    // ------------------------------------------------- 2. client ma hoa
    banner("2", "CLIENT", "ma hoa truoc khi roi thiet bi");

    double t_enc    = -1.0;
    size_t ct_bytes = 0;
    if (dev_setup())
    {
        vector<uint64_t> b0(np * DEGREE, 0), b1(np * DEGREE, 0);
        dev_encrypt(q.plain.data(), FP_DIM, b0.data(), b1.data(), DEGREE);
        auto t0 = Clock::now();
        dev_encrypt(q.plain.data(), FP_DIM, b0.data(), b1.data(), DEGREE);
        t_enc    = chrono::duration<double, milli>(Clock::now() - t0).count();
        ct_bytes = dev_last_bytes();
        dev_cleanup();
    }

    cout << " Thu vien           : SEAL-Embedded, CKKS degree " << DEGREE
         << ", scale 2^25\n";
    if (t_enc >= 0)
    {
        cout << fixed << setprecision(2);
        cout << " Thoi gian ma hoa   : " << t_enc << " ms\n";
        cout << " Goi gui len server : " << ct_bytes / 1024.0 << " KB\n";
    }
    cout << " Khoa bi mat        : O LAI tren thiet bi, khong gui di\n";

    Ciphertext ct_q;
    build(q, ct_q);

    // --------------------------------------------- 3. server so khop
    banner("3", "SERVER", "so khop tren ban ma");

    vector<Entry> db;
    {
        vector<string> names;
        for (auto &p : fs::directory_iterator(ctdir))
            if (p.path().extension() == ".txt") names.push_back(p.path().stem().string());
        sort(names.begin(), names.end());

        bool lay_het = ndb + 1 >= names.size();
        for (const auto &n : names)
        {
            if (db.size() >= ndb) break;
            if (n == qname) continue;
            if (!lay_het && n.substr(n.rfind('_') + 1) != "1") continue;
            Entry e;
            if (load_entry(n, e)) db.push_back(move(e));
        }
    }
    if (db.empty()) { cout << "Co so du lieu rong\n"; return 1; }

    cout << " Co so du lieu      : " << db.size() << " ban ghi, cung o dang ban ma\n";
    cout << " Phep tinh          : tru -> binh phuong -> cong don " << FP_DIM
         << " chieu (" << steps.size() << " vong xoay)\n";
    cout << " Server giu khoa?   : KHONG - khong giai ma duoc bat ky gi\n\n";

    vector<Row> rows;
    vector<Ciphertext> results;
    auto t_server0 = Clock::now();
    for (const auto &e : db)
    {
        Ciphertext ct_e, ct_d, ct_sq;
        build(e, ct_e);

        auto t0 = Clock::now();
        evaluator.sub(ct_q, ct_e, ct_d);
        evaluator.square(ct_d, ct_sq);
        evaluator.relinearize_inplace(ct_sq, relin_keys);
        evaluator.rescale_to_next_inplace(ct_sq);
        for (size_t s = 1; s < FP_DIM; s <<= 1)
        {
            Ciphertext rot;
            evaluator.rotate_vector(ct_sq, (int)s, galois_keys, rot);
            evaluator.add_inplace(ct_sq, rot);
        }
        double ms = chrono::duration<double, milli>(Clock::now() - t0).count();

        Row r;
        r.name   = e.name;
        r.finger = e.finger;
        r.ms     = ms;
        rows.push_back(r);
        results.push_back(move(ct_sq));
    }
    double t_server = chrono::duration<double, milli>(Clock::now() - t_server0).count();

    cout << " Da tinh xong " << db.size() << " phep so khop trong " << t_server
         << " ms\n";
    cout << " Server tra ve " << db.size() << " ket qua, tat ca VAN O DANG BAN MA\n";

    // ------------------------------------------ 4. client giai ma
    banner("4", "CLIENT", "giai ma ket qua va ra quyet dinh");

    auto t_dec0 = Clock::now();
    for (size_t i = 0; i < rows.size(); i++)
    {
        Plaintext pt;
        decryptor.decrypt(results[i], pt);
        vector<double> out;
        encoder.decode(pt, out);
        rows[i].d_fhe = out[0];
    }
    double t_dec = chrono::duration<double, milli>(Clock::now() - t_dec0).count();

    for (size_t i = 0; i < rows.size(); i++)
    {
        double expect = 0;
        for (size_t k = 0; k < FP_DIM; k++)
        {
            double d = q.plain[k] - db[i].plain[k];
            expect += d * d;
        }
        rows[i].d_plain = expect;
        rows[i].rel_err = expect > 0 ? fabs(rows[i].d_fhe - expect) / expect * 100.0 : 0.0;
    }

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
    rank_by(true);
    rank_by(false);

    vector<size_t> order(rows.size());
    for (size_t i = 0; i < order.size(); i++) order[i] = i;
    sort(order.begin(), order.end(),
         [&](size_t a, size_t b) { return rows[a].rank_fhe < rows[b].rank_fhe; });

    cout << " Thoi gian giai ma  : " << t_dec << " ms cho " << rows.size() << " ket qua\n\n";
    cout << left << setw(14) << " BAN GHI" << right << setw(14) << "KHOANG CACH" << setw(10)
         << "HANG" << setw(12) << "SERVER ms" << "\n";
    cout << string(52, '-') << "\n";
    for (size_t k : order)
    {
        const Row &r = rows[k];
        cout << left << setw(14) << (" " + r.name) << right << fixed << setprecision(3)
             << setw(14) << r.d_fhe << setw(10) << r.rank_fhe << setprecision(2) << setw(12)
             << r.ms << "\n";
    }

    const Row &best = rows[order[0]];
    bool same       = (best.finger == q.finger);

    cout << "\n==================================================================\n";
    cout << " KET QUA\n";
    cout << "==================================================================\n";
    cout << " Ban ghi gan nhat   : " << best.name << "\n";
    cout << fixed << setprecision(3);
    cout << " Khoang cach        : " << best.d_fhe << "\n";
    cout << " Ket luan           : " << (same ? "TRUNG KHOP - dung ngon " + q.finger
                                              : "KHONG TRUNG KHOP") << "\n";
    cout << fixed << setprecision(2);
    cout << " Tong mot luot      : " << t_enc + t_server + t_dec << " ms"
         << "  (ma hoa " << t_enc << " + so khop " << t_server << " + giai ma " << t_dec
         << ")\n";

    cout << "\n Server khong giai ma o bat ky buoc nao. Moi con so trong bang\n";
    cout << " chi doc duoc sau khi client dung khoa bi mat cua minh.\n";

    fs::create_directories(fs::path(csvout).parent_path());
    ofstream f(csvout);
    f << "ban_ghi,khoang_cach_ban_ma,khoang_cach_ban_ro,sai_so_pct,hang_ban_ma,hang_ban_ro,"
         "server_ms\n";
    for (size_t k : order)
    {
        const Row &r = rows[k];
        f << r.name << "," << r.d_fhe << "," << r.d_plain << "," << r.rel_err << ","
          << r.rank_fhe << "," << r.rank_plain << "," << r.ms << "\n";
    }
    cout << "\n CSV: " << csvout << "\n";
    return 0;
}
