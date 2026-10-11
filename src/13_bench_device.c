// Benchmark phía THIẾT BỊ — thời gian mã hóa một mẫu vân tay.
//
// Lien ket thang libseal_embedded.a, dung dung API ma mot thiet bi nhung dung.
// Ham "gui mang" la ham rong chi dem byte, de thoi gian ghi file khong lan vao
// so do.
//
// Chay tu thu muc device/ vi SE_DATA_PATH la duong dan tuong doi.
//   cd device && ../seal_flow/build/13_bench_device [so_lan_lap]

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include "defines.h"
#include "seal_embedded.h"
#include "util_print.h"

#define FP_DIM 512

static size_t g_bytes = 0;

// Ham gui gia: khong ghi file, chi dem so byte se phai truyen di
static size_t count_only(void *v, size_t vlen_bytes)
{
    (void)v;
    g_bytes += vlen_bytes;
    return vlen_bytes;
}

static double now_ms(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
}

static int cmp_double(const void *a, const void *b)
{
    double x = *(const double *)a, y = *(const double *)b;
    return (x > y) - (x < y);
}

int main(int argc, char *argv[])
{
    size_t repeat = (argc > 1) ? (size_t)strtoul(argv[1], NULL, 10) : 20;

    // -- Du lieu thu: gia tri bat ky trong [0,1]. Thoi gian ma hoa khong phu
    //    thuoc noi dung, nen dung so sinh san la hop le.
    srand(20261016);

    printf("=================================================\n");
    printf(" BENCHMARK — ma hoa phia thiet bi (SEAL-Embedded)\n");
    printf("=================================================\n");
    printf(" n=%d  so lan lap=%zu\n\n", FP_DIM, repeat);

    // -- Thoi gian thiet lap (mot lan duy nhat khi thiet bi khoi dong)
    double t0 = now_ms();
    SE_PARMS *se_parms = se_setup_default(SE_ASYM_ENCR);
    double t_setup = now_ms() - t0;
    if (!se_parms) { fprintf(stderr, "se_setup_default that bai\n"); return 1; }

    size_t n    = se_parms->parms->coeff_count;
    size_t vlen = n / 2;
    flpt *v     = (flpt *)calloc(vlen, sizeof(flpt));
    if (!v) return 1;

    double *t = (double *)malloc(repeat * sizeof(double));
    if (!t) return 1;

    // -- Mot lan chay nong de khong tinh chi phi nap trang bo nho lan dau
    for (size_t i = 0; i < FP_DIM; i++) v[i] = (flpt)((rand() % 256) / 255.0);
    g_bytes = 0;
    se_encrypt(&count_only, v, vlen * sizeof(flpt), false, se_parms);
    size_t bytes_per_ct = g_bytes;

    // -- Do that
    for (size_t r = 0; r < repeat; r++)
    {
        for (size_t i = 0; i < FP_DIM; i++) v[i] = (flpt)((rand() % 256) / 255.0);
        g_bytes   = 0;
        double a  = now_ms();
        se_encrypt(&count_only, v, vlen * sizeof(flpt), false, se_parms);
        t[r] = now_ms() - a;
    }

    qsort(t, repeat, sizeof(double), cmp_double);
    double sum = 0;
    for (size_t r = 0; r < repeat; r++) sum += t[r];
    double mean = sum / repeat;
    double acc = 0;
    for (size_t r = 0; r < repeat; r++) acc += (t[r] - mean) * (t[r] - mean);
    double sd = repeat > 1 ? sqrt(acc / (repeat - 1)) : 0.0;

    printf("--- Thiet lap (mot lan khi khoi dong) ---\n");
    printf("  se_setup_default              %9.3f ms\n\n", t_setup);

    printf("--- Ma hoa mot mau van tay ---\n");
    printf("  trung binh                    %9.3f ms  (do lech chuan %.3f)\n", mean, sd);
    printf("  nhanh nhat                    %9.3f ms\n", t[0]);
    printf("  cham nhat                     %9.3f ms\n", t[repeat - 1]);
    printf("  trung vi                      %9.3f ms\n\n", t[repeat / 2]);

    printf("--- Du lieu truyen di ---\n");
    printf("  Van tay goc                   %9.2f KB\n", FP_DIM / 1024.0);
    printf("  Ciphertext gui len server     %9.2f KB  (phinh %.0fx)\n",
           bytes_per_ct / 1024.0, (double)bytes_per_ct / FP_DIM);

    printf("\n--- Thong luong ---\n");
    printf("  %.1f mau/giay tren mot nhan\n", 1000.0 / mean);

    free(v); free(t);
    se_cleanup(se_parms);
    return 0;
}
