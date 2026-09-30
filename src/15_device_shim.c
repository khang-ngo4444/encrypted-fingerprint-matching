// Lop vo C cho thu vien thiet bi, de phia C++ goi duoc.
//
// Ly do phai tach file: header cua SEAL-Embedded (ckks_common.h, rng.h) dung
// cu phap chi hop le trong C — truong ten `complex`, gan void* sang uint8*
// khong ep kieu. Bien chung bang trinh bien dich C++ se loi. Nen gom phan cham
// vao thu vien thiet bi vao day, bien bang C, roi chi lo ra bon ham don gian.

#include <fcntl.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#include "defines.h"
#include "seal_embedded.h"

static SE_PARMS *g_parms = NULL;
static flpt *g_v         = NULL;
static size_t g_vlen     = 0;

// Dich ban ma vao hai mang phang do phia C++ cap phat
static uint64_t *g_c0 = NULL, *g_c1 = NULL;
static size_t g_stride = 0;  // so he so moi da thuc
static size_t g_poly   = 0;  // dem so lan ham thu duoc goi
static size_t g_bytes  = 0;

static size_t collect(void *v, size_t vlen_bytes)
{
    size_t vlen = vlen_bytes / sizeof(ZZ);
    ZZ *data    = (ZZ *)v;
    // Thu tu goi: c0, c1 cua prime 0; roi c0, c1 cua prime 1; ...
    size_t prime  = g_poly / 2;
    uint64_t *dst = (g_poly % 2 == 0) ? g_c0 : g_c1;
    if (dst && vlen <= g_stride)
        for (size_t i = 0; i < vlen; i++) dst[prime * g_stride + i] = (uint64_t)data[i];
    g_poly++;
    g_bytes += vlen_bytes;
    return vlen_bytes;
}

// Tra ve so slot, hoac 0 neu that bai.
//
// se_setup_default in ra ban do bo nho va dia chi mempool — huu ich khi go loi
// tren vi dieu khien, nhung lam ban ket qua khi chay bao cao. Tam cat stdout
// trong luc goi roi noi lai, khong dong vao thu vien.
size_t dev_setup(void)
{
    fflush(stdout);
    int saved = dup(STDOUT_FILENO);
    int devnull = open("/dev/null", O_WRONLY);
    if (devnull >= 0) { dup2(devnull, STDOUT_FILENO); close(devnull); }

    g_parms = se_setup_default(SE_ASYM_ENCR);

    fflush(stdout);
    if (saved >= 0) { dup2(saved, STDOUT_FILENO); close(saved); }

    if (!g_parms) return 0;
    g_vlen = g_parms->parms->coeff_count / 2;
    g_v    = (flpt *)calloc(g_vlen, sizeof(flpt));
    return g_v ? g_vlen : 0;
}

// Ma hoa `n` gia tri dau tien, viet ket qua vao c0/c1 (np * stride phan tu moi mang).
// Tra ve true neu thanh cong.
bool dev_encrypt(const double *vals, size_t n, uint64_t *c0, uint64_t *c1, size_t stride)
{
    if (!g_parms || !g_v) return false;
    for (size_t i = 0; i < g_vlen; i++) g_v[i] = (flpt)(i < n ? vals[i] : 0.0);
    g_c0     = c0;
    g_c1     = c1;
    g_stride = stride;
    g_poly   = 0;
    g_bytes  = 0;
    return se_encrypt(&collect, g_v, g_vlen * sizeof(flpt), false, g_parms);
}

size_t dev_last_bytes(void) { return g_bytes; }

void dev_cleanup(void)
{
    if (g_v) free(g_v);
    g_v = NULL;
    if (g_parms) se_cleanup(g_parms);
    g_parms = NULL;
}
