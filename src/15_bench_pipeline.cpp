// Giai đoạn 15: benchmark TOÀN BỘ pipeline, từ thiết bị tới kết quả.
//
// Khac voi bai 12 (chi do phan tinh toan phia server) va bai 13 (chi do phia
// thiet bi), bai nay noi ca hai dau lai trong MOT tien trinh de do duoc tong
// thoi gian that su cua mot lan so khop:
//
//   [THIET BI]  se_encrypt                 -> ban ma trong bo nho
//   [MANG]      nap ban ma vao doi tuong SEAL
//   [SERVER]    sub -> square -> relin -> rescale -> rotation-sum
//   [GIU KHOA]  decrypt + decode
//
// Ban ma cua mau da dang ky duoc sinh mot lan truoc vong do, vi trong he that
// CSDL da nam san o dang ma — chi truy van moi phai ma hoa moi lan.
//
// Chay tu thu muc device/ vi SE_DATA_PATH la duong dan tuong doi:
//   cd device && ../seal_flow/build/15_bench_pipeline [so_lan_lap]

#include "seal/seal.h"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <random>
#include <string>
#include <vector>

// Thu vien thiet bi duoc goi qua lop vo C (15_device_shim.c) — header goc cua
// no khong bien duoc bang trinh bien dich C++.
extern "C" {
size_t dev_setup(void);
bool dev_encrypt(const double *vals, size_t n, uint64_t *c0, uint64_t *c1, size_t stride);
size_t dev_last_bytes(void);
void dev_cleanup(void);
}

using namespace std;
using namespace seal;

using Clock = chrono::steady_clock;

constexpr size_t FP_DIM = 512;
constexpr size_t DEGREE = 4096;

struct Stat
{
    double mean, sd, min, max;
};

static Stat summarize(vector<double> v)
{
    Stat s{0, 0, 0, 0};
    if (v.empty()) return s;
    s.mean = accumulate(v.begin(), v.end(), 0.0) / v.size();
    double acc = 0;
    for (double x : v) acc += (x - s.mean) * (x - s.mean);
    s.sd  = v.size() > 1 ? sqrt(acc / (v.size() - 1)) : 0.0;
    s.min = *min_element(v.begin(), v.end());
    s.max = *max_element(v.begin(), v.end());
    return s;
}

static void row(const string &name, const Stat &s)
{
    cout << "  " << left << setw(36) << name << right << fixed << setprecision(3) << setw(9)
         << s.mean << " ms   +-" << setw(7) << s.sd << "   [" << setw(8) << s.min << " .. "
         << setw(8) << s.max << "]\n";
}

int main(int argc, char *argv[])
{
    size_t REPEAT   = (argc > 1) ? (size_t)stoul(argv[1]) : 30;
    string csv_path = (argc > 2)
                          ? argv[2]
                          : CME_ROOT "/bench/pipeline_benchmark.csv";
    string keydir = CME_ROOT "/device/adapter_output_data/";

    // ----------------------------------------------------- tham so chung
    EncryptionParameters parms(scheme_type::ckks);
    parms.set_poly_modulus_degree(DEGREE);
    // seal::Modulus phai ghi day du: thu vien thiet bi cung co mot struct ten
    // Modulus, de nguyen se nhap nhang.
    vector<seal::Modulus> moduli = {seal::Modulus(134012929), seal::Modulus(134111233),
                                    seal::Modulus(134176769),
                                    CoeffModulus::Create(DEGREE, {28})[0]};
    parms.set_coeff_modulus(moduli);
    double scale = pow(2.0, 25);

    SEALContext context(parms);
    if (!context.parameters_set())
    {
        cout << "Tham so khong hop le: " << context.parameter_error_message() << endl;
        return 1;
    }

    cout << "===============================================================\n";
    cout << " BENCHMARK — toan bo pipeline (thiet bi -> server -> giai ma)\n";
    cout << "===============================================================\n";
    cout << " degree=" << DEGREE << "  n=" << FP_DIM << "  scale=2^25  so lan lap=" << REPEAT
         << "\n\n";

    // -- Khoa: sk do adapter sinh (dung cap voi pk nam trong thiet bi)
    KeyGenerator keygen_tmp(context);
    SecretKey sk = keygen_tmp.secret_key();
    {
        ifstream f(keydir + "sk_4096_seal.dat", ios::binary);
        if (!f.is_open())
        {
            cout << "Khong mo duoc " << keydir << "sk_4096_seal.dat" << endl;
            return 1;
        }
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

    // -- Thiet lap thu vien phia thiet bi (mot lan duy nhat luc khoi dong)
    auto t_boot0       = Clock::now();
    size_t slots       = dev_setup();
    double t_setup_dev = chrono::duration<double, milli>(Clock::now() - t_boot0).count();
    if (!slots)
    {
        cout << "dev_setup that bai" << endl;
        return 1;
    }

    // Ban ma thiet bi tra ve: np da thuc moi phia (np = so prime cua tang du
    // lieu dau tien = 3; special prime khong nam trong ban ma).
    vector<uint64_t> buf_c0(np * DEGREE, 0), buf_c1(np * DEGREE, 0);

    auto device_encrypt = [&](const vector<double> &vals) {
        return dev_encrypt(vals.data(), FP_DIM, buf_c0.data(), buf_c1.data(), DEGREE);
    };

    // -- Nap ban ma thiet bi vua sinh vao doi tuong Ciphertext cua SEAL
    auto build = [&](Ciphertext &ct) -> bool {
        ct.resize(context, context.first_parms_id(), 2);
        auto p0 = ct.data(0);
        auto p1 = ct.data(1);
        for (size_t j = 0; j < np; j++)
            for (size_t i = 0; i < DEGREE; i++)
            {
                p0[j * DEGREE + i] = buf_c0[j * DEGREE + i];
                p1[j * DEGREE + i] = buf_c1[j * DEGREE + i];
            }
        ct.is_ntt_form() = true;
        ct.scale()       = scale;
        return true;
    };

    // ------------------------------------------- mau da dang ky: ma hoa 1 lan
    // Trong he that, CSDL da nam san o dang ma nen khong tinh vao thoi gian
    // moi truy van.
    mt19937 rng(20261016);
    uniform_real_distribution<double> dist(0.0, 1.0);
    vector<double> enroll(FP_DIM), query(FP_DIM);
    for (size_t i = 0; i < FP_DIM; i++) enroll[i] = dist(rng);

    if (!device_encrypt(enroll))
    {
        cout << "se_encrypt (mau dang ky) that bai" << endl;
        return 1;
    }
    size_t bytes_per_ct = dev_last_bytes();
    Ciphertext ct_e;
    if (!build(ct_e))
    {
        cout << "Khong dung duoc ciphertext mau dang ky" << endl;
        return 1;
    }

    // -- Mot vong chay nong, khong tinh vao so do
    for (size_t i = 0; i < FP_DIM; i++) query[i] = dist(rng);
    device_encrypt(query);

    // ------------------------------------------------------- vong do that
    vector<double> t_enc, t_load, t_match, t_dec, t_total;

    for (size_t r = 0; r < REPEAT; r++)
    {
        for (size_t i = 0; i < FP_DIM; i++) query[i] = dist(rng);

        auto t0 = Clock::now();
        if (!device_encrypt(query))
        {
            cout << "se_encrypt that bai o vong " << r << endl;
            return 1;
        }
        auto t1 = Clock::now();

        Ciphertext ct_q;
        if (!build(ct_q))
        {
            cout << "Khong dung duoc ciphertext truy van o vong " << r << endl;
            return 1;
        }
        auto t2 = Clock::now();

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
        auto t3 = Clock::now();

        Plaintext pt;
        decryptor.decrypt(ct_sum, pt);
        vector<double> out;
        encoder.decode(pt, out);
        auto t4 = Clock::now();

        // Kiem tra ket qua van dung — benchmark ma sai so thi vo nghia
        if (r == 0)
        {
            double expect = 0;
            for (size_t i = 0; i < FP_DIM; i++)
            {
                double d = query[i] - enroll[i];
                expect += d * d;
            }
            double rel = fabs(out[0] - expect) / expect * 100.0;
            cout << "--- [0] Kiem tra dung dan ---\n";
            cout << "  Khoang cach tinh chay             " << fixed << setprecision(6) << expect
                 << "\n";
            cout << "  Khoang cach qua pipeline          " << out[0] << "\n";
            cout << "  Sai so tuong doi                  " << scientific << setprecision(3) << rel
                 << " %\n\n";
        }

        auto ms = [](auto a, auto b) { return chrono::duration<double, milli>(b - a).count(); };
        t_enc.push_back(ms(t0, t1));
        t_load.push_back(ms(t1, t2));
        t_match.push_back(ms(t2, t3));
        t_dec.push_back(ms(t3, t4));
        t_total.push_back(ms(t0, t4));
    }

    Stat s_enc = summarize(t_enc), s_load = summarize(t_load), s_match = summarize(t_match),
         s_dec = summarize(t_dec), s_tot = summarize(t_total);

    cout << "--- [1] Thiet lap (mot lan duy nhat luc khoi dong) ---\n";
    cout << "  " << left << setw(36) << "se_setup_default (thiet bi)" << right << fixed
         << setprecision(3) << setw(9) << t_setup_dev << " ms\n\n";

    cout << "--- [2] Mot lan so khop, tung chang ---\n";
    row("[THIET BI]  ma hoa truy van", s_enc);
    row("[MANG]      nap ban ma vao SEAL", s_load);
    row("[SERVER]    tinh tren ban ma", s_match);
    row("[GIU KHOA]  giai ma + giai nen", s_dec);
    cout << "  " << string(36, '-') << "\n";
    row("TONG PIPELINE", s_tot);

    cout << "\n--- [3] Ti trong tung chang ---\n";
    auto pct = [&](const char *n, double x) {
        cout << "  " << left << setw(36) << n << right << fixed << setprecision(1) << setw(6)
             << x / s_tot.mean * 100.0 << " %\n";
    };
    pct("ma hoa phia thiet bi", s_enc.mean);
    pct("nap ban ma", s_load.mean);
    pct("tinh toan phia server", s_match.mean);
    pct("giai ma", s_dec.mean);

    cout << "\n--- [4] Du lieu truyen di ---\n";
    cout << "  " << left << setw(36) << "Van tay goc (512 x uint8)" << right << fixed
         << setprecision(2) << setw(9) << FP_DIM / 1024.0 << " KB\n";
    cout << "  " << left << setw(36) << "Ciphertext gui len server" << right << setw(9)
         << bytes_per_ct / 1024.0 << " KB   (phinh " << setprecision(0)
         << (double)bytes_per_ct / FP_DIM << "x)\n";

    cout << "\n--- [5] Thong luong ---\n";
    cout << "  " << left << setw(36) << "Mot nhan" << right << fixed << setprecision(1) << setw(9)
         << 1000.0 / s_tot.mean << " truy van/giay\n";
    cout << "  " << left << setw(36) << "Bon nhan (uoc tinh)" << right << setw(9)
         << 4000.0 / s_tot.mean << " truy van/giay\n";

    // ------------------------------------------------------------- xuat CSV
    {
        ofstream f(csv_path);
        if (f.is_open())
        {
            f << "chang,trung_binh_ms,do_lech_chuan_ms,min_ms,max_ms\n";
            auto w = [&](const string &n, const Stat &s) {
                f << n << "," << s.mean << "," << s.sd << "," << s.min << "," << s.max << "\n";
            };
            w("thiet_bi_ma_hoa", s_enc);
            w("nap_ban_ma", s_load);
            w("server_tinh_toan", s_match);
            w("giai_ma", s_dec);
            w("tong_pipeline", s_tot);
            f << "\n#,gia_tri,don_vi\n";
            f << "thiet_lap_thiet_bi," << t_setup_dev << ",ms\n";
            f << "kich_thuoc_ciphertext," << bytes_per_ct / 1024.0 << ",KB\n";
            f << "thong_luong_1_nhan," << 1000.0 / s_tot.mean << ",truy_van/giay\n";
            cout << "\nDa ghi CSV: " << csv_path << endl;
        }
    }

    dev_cleanup();
    return 0;
}
