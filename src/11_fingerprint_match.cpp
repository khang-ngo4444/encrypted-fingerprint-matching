// Giai đoạn 11 (Phase 2): SERVER so khớp vân tay trên bản mã.
//
// Nhan ciphertext do thiet bi sinh (bai 10), tinh khoang cach Euclidean giua
// truy van va tung mau trong CSDL — TOAN BO tren ban ma, server khong bao gio
// thay du lieu tho. Chi noi giu sk moi giai duoc ket qua.
//
//   d = q - e  ->  d^2  ->  relinearize  ->  rescale  ->  rotation-sum 9 tang
//
// Doi chieu voi khoang cach tinh chay tu file .bin goc de danh gia sai so.

#include "seal/seal.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using namespace std;
using namespace seal;

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

struct CtFile
{
    vector<double> values;
    vector<vector<double>> c0, c1;
    bool ok = false;
};

static CtFile read_ct(const string &path)
{
    CtFile r;
    ifstream f(path);
    if (!f.is_open()) return r;
    string line;
    while (getline(f, line))
    {
        if (line.rfind("v (cleartext)", 0) == 0)
            r.values = parse_brace_line(line);
        else if (line.rfind("c0 :", 0) == 0)
            r.c0.push_back(parse_brace_line(line));
        else if (line.rfind("c1 :", 0) == 0)
            r.c1.push_back(parse_brace_line(line));
    }
    r.ok = !r.c0.empty() && r.c0.size() == r.c1.size();
    return r;
}

// Doc mau van tay tho (512 byte uint8) va chuan hoa giong phia thiet bi
static vector<double> read_fp(const string &path)
{
    vector<double> v;
    ifstream f(path, ios::binary);
    if (!f.is_open()) return v;
    vector<unsigned char> raw(FP_DIM);
    f.read((char *)raw.data(), FP_DIM);
    if ((size_t)f.gcount() != FP_DIM) return v;
    v.resize(FP_DIM);
    for (size_t i = 0; i < FP_DIM; i++) v[i] = raw[i] / 255.0;
    return v;
}

int main(int argc, char *argv[])
{
    string ctdir  = CME_ROOT "/ct/";
    string fpdir  = CME_ROOT "/data/";
    string keydir = CME_ROOT "/device/adapter_output_data/";
    string qname  = (argc > 1) ? argv[1] : "query";
    // Ten file .bin goc cua truy van, de tinh chay doi chieu
    string qsrc   = (argc > 4) ? argv[4] : "enroll_1";
    size_t ndb    = (argc > 2) ? (size_t)stoul(argv[2]) : 11;
    // Nguong quyet dinh khop. Chua hieu chinh tren du lieu that — xem ghi chu cuoi.
    double threshold = (argc > 3) ? stod(argv[3]) : 1.0;

    size_t degree = 4096;
    EncryptionParameters parms(scheme_type::ckks);
    parms.set_poly_modulus_degree(degree);
    vector<Modulus> moduli;
    moduli.push_back(Modulus(134012929));
    moduli.push_back(Modulus(134111233));
    moduli.push_back(Modulus(134176769));
    moduli.push_back(CoeffModulus::Create(degree, {28})[0]);
    parms.set_coeff_modulus(moduli);
    double scale = pow(2.0, 25);

    SEALContext context(parms);
    if (!context.parameters_set())
    {
        cout << "Tham so khong hop le: " << context.parameter_error_message() << endl;
        return 1;
    }

    // -- Khoa: sk do adapter sinh; relin/galois sinh tu chinh sk do
    KeyGenerator keygen_tmp(context);
    SecretKey sk = keygen_tmp.secret_key();
    {
        ifstream f(keydir + "sk_4096_seal.dat", ios::binary);
        if (!f.is_open()) { cout << "Khong mo duoc sk" << endl; return 1; }
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

    auto build = [&](const CtFile &cf, Ciphertext &ct) -> bool {
        if (cf.c0.size() < np) return false;
        ct.resize(context, context.first_parms_id(), 2);
        auto p0 = ct.data(0);
        auto p1 = ct.data(1);
        for (size_t j = 0; j < np; j++)
            for (size_t i = 0; i < degree; i++)
            {
                p0[j * degree + i] = (uint64_t)cf.c0[j][i];
                p1[j * degree + i] = (uint64_t)cf.c1[j][i];
            }
        ct.is_ntt_form() = true;
        ct.scale()       = scale;
        return true;
    };

    // -- Nap truy van
    CtFile qf = read_ct(ctdir + qname + ".txt");
    if (!qf.ok) { cout << "Khong doc duoc truy van " << qname << ".txt" << endl; return 1; }
    Ciphertext ct_q;
    if (!build(qf, ct_q)) { cout << "Truy van thieu du lieu" << endl; return 1; }

    // -- Ban ro truy van de tinh chay (doc thang tu file .bin goc)
    vector<double> q_plain = read_fp(fpdir + qsrc + ".bin");

    cout << "=== So khop van tay tren ban ma ===" << endl;
    cout << "truy van : " << qname << ".txt  (goc: " << qsrc << ".bin)" << endl;
    cout << "CSDL     : " << ndb << " mau" << endl;
    cout << "nguong   : " << threshold << endl << endl;

    cout << left << setw(12) << "mau" << setw(16) << "tinh chay" << setw(16) << "tren ban ma"
         << setw(14) << "sai so" << "ket qua" << endl;
    cout << string(70, '-') << endl;

    double best_dist = 1e300;
    size_t best_idx  = 0;

    for (size_t k = 1; k <= ndb; k++)
    {
        string name = "enroll_" + to_string(k);
        CtFile ef   = read_ct(ctdir + name + ".txt");
        if (!ef.ok) { cout << name << "  [khong doc duoc]" << endl; continue; }
        Ciphertext ct_e;
        if (!build(ef, ct_e)) { cout << name << "  [thieu du lieu]" << endl; continue; }

        // -- Tinh chay de doi chieu
        vector<double> e_plain = read_fp(fpdir + name + ".bin");
        double expected        = 0.0;
        for (size_t i = 0; i < FP_DIM && i < e_plain.size(); i++)
        {
            double d = q_plain[i] - e_plain[i];
            expected += d * d;
        }

        // -- Toan bo phan nay chay tren ban ma
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

        Plaintext pt;
        decryptor.decrypt(ct_sum, pt);
        vector<double> res;
        encoder.decode(pt, res);
        double got = res[0];

        double abs_err = fabs(got - expected);
        cout << left << setw(12) << name << setw(16) << fixed << setprecision(4) << expected
             << setw(16) << got << setw(14) << scientific << setprecision(2) << abs_err
             << (got < threshold ? "KHOP" : "khong") << endl;

        if (got < best_dist)
        {
            best_dist = got;
            best_idx  = k;
        }
    }

    cout << "\n=== Ket luan ===" << endl;
    cout << fixed << setprecision(4);
    cout << "  Khop tot nhat : enroll_" << best_idx << "  (khoang cach " << best_dist << ")" << endl;
    size_t want = (size_t)stoul(qsrc.substr(qsrc.rfind('_') + 1));
    cout << "  Ky vong       : " << qsrc << " (truy van la ban sao cua no)" << endl;
    cout << "  " << (best_idx == want ? "DUNG" : "SAI") << endl;

    cout << "\nGhi chu: nguong " << threshold << " chua duoc hieu chinh tren tap du lieu that."
         << "\nMuon dat nguong co can cu phai do phan bo khoang cach cung-nguoi va khac-nguoi,"
         << "\nma bo mau hien co (11 mau, moi nguoi 1 mau) khong du de lam viec do." << endl;
    return (best_idx == want) ? 0 : 2;
}
