// Giai đoạn 10 (Phase 2): ứng dụng THIẾT BỊ mã hóa mẫu vân tay thật.
//
// Khac voi bai 09 (dung vector test co dinh cua thu vien), bai nay lien ket thang
// libseal_embedded.a vao mot ung dung rieng — dung cach mot thiet bi IoT that su
// dung thu vien, khong phai hack file test.
//
// Dinh dang mau van tay: 512 byte = 512 gia tri uint8 (0..255), moi byte mot chieu.
// Chuan hoa ve [0,1] bang cach chia 255 truoc khi ma hoa. Ly do: gia tri tho toi
// 255 thi tong Euclidean toi 512*255^2 = 3.3e7 ~ 2^25; voi scale 2^23 sau rescale
// thi ban ro cham 2^48, trong khi modulus con lai chi 2^54 — qua sat tran.
// Chuan hoa dua tong ve toi da 512 = 2^9, an toan va giu duoc do chinh xac.
//
// Chay tu thu muc device/ vi SE_DATA_PATH la duong dan tuong doi.
//
// Dung:  10_fingerprint_encrypt <file_van_tay.bin> <file_ciphertext_ra.txt>

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "defines.h"
#include "seal_embedded.h"
#include "util_print.h"

#define FP_DIM 512  // so chieu cua mau van tay

static FILE *g_out = NULL;
static int g_idx   = 0;  // luan phien c0 / c1

// Ham "gui qua mang" gia: thay vi gui di, ghi ra file text theo dung dinh dang
// ma phia server doc lai (giong device/test/api_tests.c:30).
static size_t write_ciphertext(void *v, size_t vlen_bytes)
{
    size_t vlen  = vlen_bytes / sizeof(ZZ);
    ZZ *data     = (ZZ *)v;
    const char *name = g_idx ? "c1" : "c0";

    fprintf(g_out, "%s : { ", name);
    for (size_t i = 0; i < vlen; i++)
        fprintf(g_out, "%" PRIuZZ "%s", data[i], (i + 1 < vlen) ? ", " : "");
    fprintf(g_out, " }\n");

    g_idx = g_idx ? 0 : 1;
    return vlen_bytes;
}

int main(int argc, char *argv[])
{
    if (argc < 3)
    {
        fprintf(stderr, "Dung: %s <file_van_tay.bin> <file_ciphertext_ra.txt>\n", argv[0]);
        return 1;
    }
    const char *fp_path  = argv[1];
    const char *out_path = argv[2];

    // -- Doc mau van tay. Nhan dang dinh dang theo kich thuoc file:
    //      512 byte            -> 512 gia tri uint8 (0..255), chia 255 de chuan hoa
    //      512*8 = 4096 byte   -> 512 gia tri double, da chuan hoa L2 san
    //    Dinh dang thu hai dung cho vector sinh tu bo trich dac trung.
    double vals[FP_DIM];
    {
        FILE *f = fopen(fp_path, "rb");
        if (!f)
        {
            fprintf(stderr, "Khong mo duoc %s\n", fp_path);
            return 1;
        }
        fseek(f, 0, SEEK_END);
        long fsize = ftell(f);
        fseek(f, 0, SEEK_SET);

        if (fsize == (long)(FP_DIM * sizeof(double)))
        {
            if (fread(vals, sizeof(double), FP_DIM, f) != FP_DIM)
            {
                fprintf(stderr, "Doc hong %s\n", fp_path);
                fclose(f); return 1;
            }
        }
        else if (fsize == FP_DIM)
        {
            uint8_t raw[FP_DIM];
            if (fread(raw, 1, FP_DIM, f) != FP_DIM)
            {
                fprintf(stderr, "Doc hong %s\n", fp_path);
                fclose(f); return 1;
            }
            for (size_t i = 0; i < FP_DIM; i++) vals[i] = raw[i] / 255.0;
        }
        else
        {
            fprintf(stderr, "%s co %ld byte, can %d (uint8) hoac %zu (double)\n",
                    fp_path, fsize, FP_DIM, FP_DIM * sizeof(double));
            fclose(f); return 1;
        }
        fclose(f);
    }

    // -- Khoi tao thu vien o che do bat doi xung (thiet bi giu khoa cong khai)
    SE_PARMS *se_parms = se_setup_default(SE_ASYM_ENCR);
    if (!se_parms)
    {
        fprintf(stderr, "se_setup_default that bai\n");
        return 1;
    }

    size_t n    = se_parms->parms->coeff_count;
    size_t vlen = n / 2;  // so slot

    // -- Nap vao vector slot, phan con lai de 0
    flpt *v = (flpt *)calloc(vlen, sizeof(flpt));
    if (!v) { fprintf(stderr, "calloc that bai\n"); return 1; }
    for (size_t i = 0; i < FP_DIM; i++) v[i] = (flpt)vals[i];

    g_out = fopen(out_path, "w");
    if (!g_out)
    {
        fprintf(stderr, "Khong mo duoc %s de ghi\n", out_path);
        return 1;
    }

    // -- Ghi ban ro ra truoc de phia server doi chieu (dung dinh dang cu)
    fprintf(g_out, "v (cleartext) : { ");
    for (size_t i = 0; i < vlen; i++)
        fprintf(g_out, "%.6f%s", (double)v[i], (i + 1 < vlen) ? ", " : "");
    fprintf(g_out, " }\n");

    // -- Ma hoa. Ham write_ciphertext se duoc goi lan luot cho c0, c1 moi prime.
    g_idx    = 0;
    bool ret = se_encrypt(&write_ciphertext, v, vlen * sizeof(flpt), false, se_parms);

    fclose(g_out);
    free(v);
    se_cleanup(se_parms);

    if (!ret)
    {
        fprintf(stderr, "se_encrypt that bai\n");
        return 1;
    }
    printf("Da ma hoa %s -> %s\n", fp_path, out_path);
    return 0;
}
