// Benchmark hiệu năng phía SERVER — đo thời gian tính toán đồng cấu.
//
// Luu y ve tinh trung thuc cua so lieu:
//   Thoi gian cua moi phep CKKS KHONG phu thuoc noi dung du lieu. Mot vector
//   512 chieu tu van tay that va mot vector sinh ngau nhien cho ra thoi gian
//   giong het nhau, kich thuoc ciphertext giong het nhau. Vi vay benchmark
//   hieu nang o day dung duoc o moi quy mo, khong can dataset that.
//   Do CHINH XAC nhan dang thi khac — can du lieu that, xem muc 11 REPORT.md.
//
// Ket qua in ra dang bang va dang CSV (ghi ra file) de dung cho slide.

#include "seal/seal.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <sstream>
#include <string>
#include <vector>

using namespace std;
using namespace seal;
using Clock = chrono::steady_clock;

constexpr size_t FP_DIM = 512;

// ---------------------------------------------------------------- do thoi gian
struct Stat
{
    double mean = 0, sd = 0, min = 0, max = 0, median = 0;
};

static Stat summarize(vector<double> v)
{
    Stat s;
    if (v.empty()) return s;
    sort(v.begin(), v.end());
    s.min    = v.front();
    s.max    = v.back();
    s.median = v[v.size() / 2];
    s.mean   = accumulate(v.begin(), v.end(), 0.0) / v.size();
    double acc = 0;
    for (double x : v) acc += (x - s.mean) * (x - s.mean);
    s.sd = v.size() > 1 ? sqrt(acc / (v.size() - 1)) : 0.0;
    return s;
}

static void row(const string &name, const Stat &s, const string &unit = "ms")
{
    cout << "  " << left << setw(34) << name << right << fixed << setprecision(3) << setw(10)
         << s.mean << " ± " << setw(7) << s.sd << "   [" << setw(9) << s.min << " .. " << setw(9)
         << s.max << "]  " << unit << endl;
}

int main(int argc, char *argv[])
{
    size_t REPEAT = (argc > 1) ? (size_t)stoul(argv[1]) : 30;
    string csv_path =
        (argc > 2) ? argv[2] : CME_ROOT "/bench/server_benchmark.csv";

    size_t degree = 4096;
    EncryptionParameters parms(scheme_type::ckks);
    parms.set_poly_modulus_degree(degree);
    vector<Modulus> moduli = {Modulus(134012929), Modulus(134111233), Modulus(134176769),
                              CoeffModulus::Create(degree, {28})[0]};
    parms.set_coeff_modulus(moduli);
    double scale = pow(2.0, 25);

    cout << "===============================================================\n";
    cout << " BENCHMARK — tinh toan dong cau phia server\n";
    cout << "===============================================================\n";
    cout << " degree=" << degree << "  n=" << FP_DIM << "  scale=2^25"
         << "  so lan lap=" << REPEAT << "\n\n";

    // ------------------------------------------------- 1. Dung context + khoa
    vector<double> t_ctx, t_relin, t_galois;
    SEALContext context(parms);
    if (!context.parameters_set())
    {
        cout << "Tham so khong hop le\n";
        return 1;
    }

    KeyGenerator keygen(context);
    SecretKey sk = keygen.secret_key();

    RelinKeys relin_keys;
    GaloisKeys galois_keys;
    vector<int> steps;
    for (size_t s = 1; s < FP_DIM; s <<= 1) steps.push_back((int)s);

    for (size_t r = 0; r < 3; r++)  // khoa sinh cham, lap it
    {
        auto t0 = Clock::now();
        keygen.create_relin_keys(relin_keys);
        auto t1 = Clock::now();
        keygen.create_galois_keys(steps, galois_keys);
        auto t2 = Clock::now();
        t_relin.push_back(chrono::duration<double, milli>(t1 - t0).count());
        t_galois.push_back(chrono::duration<double, milli>(t2 - t1).count());
    }

    // Kich thuoc khoa
    auto ser_size = [](const auto &obj) {
        stringstream ss;
        obj.save(ss, compr_mode_type::none);
        return (double)ss.str().size();
    };
    double sz_relin  = ser_size(relin_keys) / 1024.0 / 1024.0;
    double sz_galois = ser_size(galois_keys) / 1024.0 / 1024.0;

    cout << "--- [1] Sinh khoa danh gia (mot lan duy nhat luc thiet lap) ---\n";
    row("Relinearization key", summarize(t_relin));
    row("Galois key (9 buoc xoay)", summarize(t_galois));
    cout << "  " << left << setw(34) << "Kich thuoc relin key" << right << setw(10) << fixed
         << setprecision(2) << sz_relin << " MB\n";
    cout << "  " << left << setw(34) << "Kich thuoc galois key" << right << setw(10) << sz_galois
         << " MB\n\n";

    PublicKey pk;
    keygen.create_public_key(pk);
    Encryptor encryptor(context, pk);
    Evaluator evaluator(context);
    Decryptor decryptor(context, sk);
    CKKSEncoder encoder(context);
    size_t slot_count = encoder.slot_count();

    // ------------------------------------------- 2. Chuan bi du lieu thu nghiem
    mt19937 rng(20261016);
    uniform_real_distribution<double> dist(0.0, 1.0);
    auto make_vec = [&]() {
        vector<double> v(slot_count, 0.0);
        for (size_t i = 0; i < FP_DIM; i++) v[i] = dist(rng);
        return v;
    };

    vector<double> va = make_vec(), vb = make_vec();
    Plaintext pa, pb;
    encoder.encode(va, scale, pa);
    encoder.encode(vb, scale, pb);
    Ciphertext ct_a, ct_b;
    encryptor.encrypt(pa, ct_a);
    encryptor.encrypt(pb, ct_b);

    // Kich thuoc ciphertext
    double sz_ct_seal = ser_size(ct_a) / 1024.0;
    // Dinh dang tho cua thiet bi: 2 da thuc x 3 prime x 4096 he so x 4 byte
    double sz_ct_dev = (2.0 * 3.0 * degree * 4.0) / 1024.0;

    cout << "--- [2] Kich thuoc du lieu ---\n";
    cout << "  " << left << setw(34) << "Van tay goc (512 x uint8)" << right << setw(10) << fixed
         << setprecision(2) << 0.5 << " KB\n";
    cout << "  " << left << setw(34) << "Ciphertext (dinh dang thiet bi)" << right << setw(10)
         << sz_ct_dev << " KB   (he so phinh " << setprecision(0) << sz_ct_dev / 0.5 << "x)\n";
    cout << "  " << left << setw(34) << "Ciphertext (SEAL serialize)" << right << setw(10)
         << setprecision(2) << sz_ct_seal << " KB\n\n";

    // ------------------------------------------- 3. Do tung buoc cua phep khop
    vector<double> t_sub, t_square, t_relinop, t_rescale, t_rotsum, t_decrypt, t_total;

    for (size_t r = 0; r < REPEAT; r++)
    {
        Ciphertext d, sq, sum;
        auto t0 = Clock::now();
        evaluator.sub(ct_a, ct_b, d);
        auto t1 = Clock::now();
        evaluator.square(d, sq);
        auto t2 = Clock::now();
        evaluator.relinearize_inplace(sq, relin_keys);
        auto t3 = Clock::now();
        evaluator.rescale_to_next_inplace(sq);
        auto t4 = Clock::now();
        sum = sq;
        for (size_t s = 1; s < FP_DIM; s <<= 1)
        {
            Ciphertext rot;
            evaluator.rotate_vector(sum, (int)s, galois_keys, rot);
            evaluator.add_inplace(sum, rot);
        }
        auto t5 = Clock::now();
        Plaintext pt;
        decryptor.decrypt(sum, pt);
        vector<double> out;
        encoder.decode(pt, out);
        auto t6 = Clock::now();

        auto ms = [](auto a, auto b) { return chrono::duration<double, milli>(b - a).count(); };
        t_sub.push_back(ms(t0, t1));
        t_square.push_back(ms(t1, t2));
        t_relinop.push_back(ms(t2, t3));
        t_rescale.push_back(ms(t3, t4));
        t_rotsum.push_back(ms(t4, t5));
        t_decrypt.push_back(ms(t5, t6));
        t_total.push_back(ms(t0, t5));  // phan tinh toan, chua ke giai ma
    }

    cout << "--- [3] Mot phep so khop, chia nho tung buoc ---\n";
    row("sub        (q - e)", summarize(t_sub));
    row("square     (d^2)", summarize(t_square));
    row("relinearize", summarize(t_relinop));
    row("rescale", summarize(t_rescale));
    row("rotation-sum (9 vong)", summarize(t_rotsum));
    cout << "  " << string(34, '-') << endl;
    row("TONG mot phep khop", summarize(t_total));
    row("giai ma (chi lam 1 lan cuoi)", summarize(t_decrypt));

    Stat st = summarize(t_total);
    double per_match_s = st.mean / 1000.0;
    cout << "\n  Thong luong 1 nhan : " << fixed << setprecision(1) << 1.0 / per_match_s
         << " phep khop/giay\n";
    cout << "  Thong luong 4 nhan : " << 4.0 / per_match_s << " phep khop/giay  (uoc tinh)\n\n";

    // ------------------------------------------- 4. Quy mo CSDL
    cout << "--- [4] Thoi gian quet toan bo CSDL (ngoai suy tu so do tren) ---\n";
    cout << "  " << left << setw(16) << "So nguoi" << right << setw(14) << "1 nhan" << setw(14)
         << "4 nhan" << endl;
    for (size_t n : {10UL, 100UL, 1000UL, 10000UL, 100000UL})
    {
        double s1 = n * per_match_s, s4 = s1 / 4.0;
        auto fmt = [](double s) {
            char buf[64];
            if (s < 60) snprintf(buf, sizeof buf, "%.2f s", s);
            else if (s < 3600) snprintf(buf, sizeof buf, "%.1f phut", s / 60);
            else snprintf(buf, sizeof buf, "%.1f gio", s / 3600);
            return string(buf);
        };
        cout << "  " << left << setw(16) << n << right << setw(14) << fmt(s1) << setw(14)
             << fmt(s4) << endl;
    }

    // ------------------------------------------- 5. So sanh voi ban ro
    // Phep tinh ban ro nhanh hon do phan giai dong ho, nen phai lap nhieu lan
    // trong MOT lan bam gio roi chia ra. Do tung lan rieng se ra 0.000 ms va
    // moi ti so tinh tu do deu vo nghia.
    const size_t INNER = 100000;
    vector<double> t_plain;
    volatile double sink = 0;
    for (size_t r = 0; r < 10; r++)
    {
        auto t0 = Clock::now();
        double acc = 0;
        for (size_t k = 0; k < INNER; k++)
            for (size_t i = 0; i < FP_DIM; i++)
            {
                double dd = va[i] - vb[i];
                acc += dd * dd;
            }
        auto t1 = Clock::now();
        sink    = acc;
        t_plain.push_back(chrono::duration<double, milli>(t1 - t0).count() / INNER);
    }
    (void)sink;
    Stat sp = summarize(t_plain);
    cout << "\n--- [5] So sanh voi tinh tren ban ro ---\n";
    Stat sp_us = sp;  // doi sang micro-giay cho de doc
    sp_us.mean *= 1000; sp_us.sd *= 1000; sp_us.min *= 1000; sp_us.max *= 1000;
    row("Euclidean tren ban ro", sp_us, "us");
    cout << "  " << left << setw(34) << "Euclidean tren ban ma" << right << fixed
         << setprecision(3) << setw(10) << st.mean * 1000 << "                             us\n";
    cout << "  " << left << setw(34) << "He so cham hon" << right << setw(10) << fixed
         << setprecision(0) << st.mean / sp.mean << "x\n";

    // ------------------------------------------------------------- xuat CSV
    {
        ofstream f(csv_path);
        if (f.is_open())
        {
            f << "hang_muc,trung_binh_ms,do_lech_chuan_ms,min_ms,max_ms\n";
            auto w = [&](const string &n, const Stat &s) {
                f << n << "," << s.mean << "," << s.sd << "," << s.min << "," << s.max << "\n";
            };
            w("relin_key_gen", summarize(t_relin));
            w("galois_key_gen", summarize(t_galois));
            w("sub", summarize(t_sub));
            w("square", summarize(t_square));
            w("relinearize", summarize(t_relinop));
            w("rescale", summarize(t_rescale));
            w("rotation_sum", summarize(t_rotsum));
            w("tong_mot_phep_khop", st);
            w("giai_ma", summarize(t_decrypt));
            w("ban_ro_doi_chung", sp);
            f << "\n#,gia_tri,don_vi\n";
            f << "kich_thuoc_ciphertext," << sz_ct_dev << ",KB\n";
            f << "kich_thuoc_relin_key," << sz_relin << ",MB\n";
            f << "kich_thuoc_galois_key," << sz_galois << ",MB\n";
            f << "thong_luong_1_nhan," << 1.0 / per_match_s << ",khop/giay\n";
            cout << "\nDa ghi CSV: " << csv_path << endl;
        }
    }
    return 0;
}
