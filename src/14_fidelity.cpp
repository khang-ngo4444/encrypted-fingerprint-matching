// Độ trung thực: kết quả trên bản mã có làm lệch quyết định so với bản rõ không?
//
// Day la chi so dung cho mot he thong BAO MAT (khong phai he thong NHAN DANG).
// Cau hoi khong phai "he nhan dang dung bao nhieu phan tram" — dieu do phu
// thuoc bo trich dac trung cua khach hang. Cau hoi la:
//
//     Cam bat ky bo trich nao vao, ket qua co doi khong khi chay qua ma hoa?
//
// Do tren TOAN BO cap cua tap anh dua vao: 80 anh -> C(80,2) = 3160 cap.
// Voi moi cap, so khoang cach Euclidean tinh tren ban ma voi tinh tren ban ro.

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
#include <map>
#include <sstream>
#include <string>
#include <vector>

#ifndef CME_ROOT
#define CME_ROOT "/home/ourpi/CoreMetEncrypt"
#endif

using namespace std;
using namespace seal;
namespace fs = std::filesystem;
using Clock  = chrono::steady_clock;

constexpr size_t FP_DIM = 512;

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
    string finger;                  // ma ngon, de biet cap cung hay khac ngon
    vector<double> plain;           // vector goc, doc tu .bin
    vector<vector<double>> c0, c1;  // ciphertext theo tung prime
};

int main(int argc, char *argv[])
{
    const char *root_env = getenv("CME_ROOT");
    string root   = (root_env && *root_env) ? string(root_env) : string(CME_ROOT);
    string ctdir  = (argc > 1) ? argv[1] : root + "/ct_demo";
    string bindir = (argc > 2) ? argv[2] : root + "/data";
    string tapds  = (argc > 3) ? argv[3] : "FVC2004 DB3_B";
    string keydir = root + "/device/adapter_output_data/";
    string csvout = root + "/bench/fidelity.csv";

    size_t degree = 4096;
    EncryptionParameters parms(scheme_type::ckks);
    parms.set_poly_modulus_degree(degree);
    vector<Modulus> moduli = {Modulus(134012929), Modulus(134111233), Modulus(134176769),
                              CoeffModulus::Create(degree, {28})[0]};
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

    // ------------------------------------------------------------- nap du lieu
    vector<Entry> E;
    for (auto &p : fs::directory_iterator(ctdir))
    {
        if (p.path().extension() != ".txt") continue;
        Entry e;
        e.name   = p.path().stem().string();
        e.finger = e.name.substr(0, e.name.find('_'));

        ifstream f(p.path());
        string line;
        while (getline(f, line))
        {
            if (line.rfind("c0 :", 0) == 0) e.c0.push_back(parse_brace_line(line));
            else if (line.rfind("c1 :", 0) == 0) e.c1.push_back(parse_brace_line(line));
        }
        if (e.c0.size() < np) continue;

        ifstream b(bindir + "/" + e.name + ".bin", ios::binary);
        if (!b.is_open()) continue;
        e.plain.resize(FP_DIM);
        b.read((char *)e.plain.data(), FP_DIM * sizeof(double));
        if ((size_t)b.gcount() != FP_DIM * sizeof(double)) continue;

        E.push_back(move(e));
    }
    sort(E.begin(), E.end(), [](const Entry &a, const Entry &b) { return a.name < b.name; });

    cout << "=================================================================\n";
    cout << " DO TRUNG THUC — ban ma so voi ban ro, tren du lieu van tay THAT\n";
    cout << "=================================================================\n";
    cout << " Tap du lieu : " << tapds << "\n";
    cout << " So anh      : " << E.size() << "\n";
    cout << " So cap      : " << E.size() * (E.size() - 1) / 2 << "\n\n";
    if (E.size() < 2) { cout << "Khong du du lieu\n"; return 1; }

    auto build = [&](const Entry &e, Ciphertext &ct) {
        ct.resize(context, context.first_parms_id(), 2);
        auto p0 = ct.data(0);
        auto p1 = ct.data(1);
        for (size_t j = 0; j < np; j++)
            for (size_t i = 0; i < degree; i++)
            {
                p0[j * degree + i] = (uint64_t)e.c0[j][i];
                p1[j * degree + i] = (uint64_t)e.c1[j][i];
            }
        ct.is_ntt_form() = true;
        ct.scale()       = scale;
    };

    vector<Ciphertext> CT(E.size());
    for (size_t i = 0; i < E.size(); i++) build(E[i], CT[i]);

    // ------------------------------------------------- duyet toan bo cap
    struct Pair { double plain, fhe; bool genuine; const string *a, *b; };
    vector<Pair> P;
    P.reserve(E.size() * (E.size() - 1) / 2);

    auto t_start = Clock::now();
    for (size_t a = 0; a < E.size(); a++)
    {
        for (size_t b = a + 1; b < E.size(); b++)
        {
            double expect = 0;
            for (size_t i = 0; i < FP_DIM; i++)
            {
                double d = E[a].plain[i] - E[b].plain[i];
                expect += d * d;
            }

            Ciphertext d, sq, sum;
            evaluator.sub(CT[a], CT[b], d);
            evaluator.square(d, sq);
            evaluator.relinearize_inplace(sq, relin_keys);
            evaluator.rescale_to_next_inplace(sq);
            sum = sq;
            for (size_t s = 1; s < FP_DIM; s <<= 1)
            {
                Ciphertext rot;
                evaluator.rotate_vector(sum, (int)s, galois_keys, rot);
                evaluator.add_inplace(sum, rot);
            }
            Plaintext pt;
            decryptor.decrypt(sum, pt);
            vector<double> out;
            encoder.decode(pt, out);

            P.push_back({expect, out[0], E[a].finger == E[b].finger, &E[a].name, &E[b].name});
        }
        if ((a + 1) % 10 == 0)
            cout << "  ...da xu ly " << a + 1 << "/" << E.size() << " anh\n" << flush;
    }
    double total_s = chrono::duration<double>(Clock::now() - t_start).count();

    // ------------------------------------------------------------- sai so
    double max_abs = 0, sum_abs = 0, max_rel = 0, sum_rel = 0;
    for (auto &p : P)
    {
        double ae = fabs(p.fhe - p.plain);
        max_abs = max(max_abs, ae);
        sum_abs += ae;
        if (p.plain > 1e-9)
        {
            double re = ae / p.plain;
            max_rel = max(max_rel, re);
            sum_rel += re;
        }
    }
    cout << "\n--- Sai so cua ket qua tren ban ma ---\n";
    cout << fixed;
    cout << "  sai so tuyet doi trung binh   " << scientific << setprecision(3)
         << sum_abs / P.size() << "\n";
    cout << "  sai so tuyet doi lon nhat     " << max_abs << "\n";
    cout << "  sai so tuong doi trung binh   " << sum_rel / P.size() << "\n";
    cout << "  sai so tuong doi lon nhat     " << max_rel << "\n";

    // ------------------------------------- quyet dinh co doi khong, quet nguong
    cout << "\n--- Quyet dinh khop/khong-khop co bi doi khong ---\n";
    vector<double> ths;
    for (auto &p : P) ths.push_back(p.plain);
    sort(ths.begin(), ths.end());
    size_t worst_flips = 0;
    double worst_th = 0;
    size_t total_checks = 0;
    for (size_t k = 0; k < ths.size(); k += max<size_t>(1, ths.size() / 200))
    {
        double th = ths[k];
        size_t flips = 0;
        for (auto &p : P)
            if ((p.plain <= th) != (p.fhe <= th)) flips++;
        total_checks++;
        if (flips > worst_flips) { worst_flips = flips; worst_th = th; }
    }
    cout << "  quet " << total_checks << " nguong khac nhau tren " << P.size() << " cap\n";
    cout << "  so quyet dinh bi doi, truong hop xau nhat: " << worst_flips;
    if (worst_flips) cout << "  (tai nguong " << fixed << setprecision(6) << worst_th << ")";
    cout << "\n";
    cout << "  ty le nhat quan: " << fixed << setprecision(4)
         << 100.0 * (1.0 - (double)worst_flips / P.size()) << "%\n";

    // --------------------------------------------------------- thu tu xep hang
    size_t rank_mismatch = 0, rank_total = 0;
    for (size_t i = 0; i + 1 < P.size(); i += 97)  // lay mau thua de khoi O(n^2)
        for (size_t j = i + 1; j < P.size(); j += 97)
        {
            bool lp = P[i].plain < P[j].plain, lf = P[i].fhe < P[j].fhe;
            rank_total++;
            if (lp != lf) rank_mismatch++;
        }
    cout << "\n--- Thu tu xep hang giua cac cap ---\n";
    cout << "  so cap-cua-cap da so sanh    " << rank_total << "\n";
    cout << "  so lan dao thu tu            " << rank_mismatch << "\n";
    cout << "  ty le giu dung thu tu        " << fixed << setprecision(4)
         << 100.0 * (1.0 - (double)rank_mismatch / max<size_t>(1, rank_total)) << "%\n";

    // ---------------------------------------------------------------- toc do
    cout << "\n--- Toc do thuc do tren du lieu that ---\n";
    cout << "  tong thoi gian               " << fixed << setprecision(1) << total_s << " giay\n";
    cout << "  moi cap                      " << setprecision(3) << total_s * 1000 / P.size()
         << " ms\n";
    cout << "  thong luong                  " << setprecision(1) << P.size() / total_s
         << " cap/giay (1 nhan)\n";

    // ------------------------------------------------------------------ CSV
    {
        fs::create_directories(fs::path(csvout).parent_path());
        ofstream f(csvout);
        f << "anh_a,anh_b,ban_ro,ban_ma,sai_so_tuyet_doi,cung_ngon\n";
        for (auto &p : P)
            f << *p.a << "," << *p.b << "," << p.plain << "," << p.fhe << ","
              << fabs(p.fhe - p.plain) << "," << (p.genuine ? 1 : 0) << "\n";
        cout << "\nDa ghi CSV: " << csvout << "\n";
    }
    return 0;
}
