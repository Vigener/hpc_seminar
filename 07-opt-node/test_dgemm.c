#include <stdio.h>

#pragma push_macro("N")
#undef N
#include <cblas.h>
#pragma pop_macro("N")

#define N 2

int main(void) {
    // 2x2行列 A と B
    double a[N*N] = {1.0, 2.0, 3.0, 4.0};
    double b[N*N] = {5.0, 6.0, 7.0, 8.0};
    double c[N*N] = {0.0, 0.0, 0.0, 0.0};

    printf("=== DGEMM Test Start ===\n");

    // cblas_dgemm の呼び出し
    cblas_dgemm(
        CblasRowMajor, CblasNoTrans, CblasNoTrans,
        N, N, N, 1.0, a, N, b, N, 1.0, c, N
    );

    // 結果の出力 (正解は C = {19, 22, 43, 50} になるはず)
    printf("Result C:\n");
    printf("%f, %f\n", c[0], c[1]);
    printf("%f, %f\n", c[2], c[3]);

    printf("=== DGEMM Test Success! ===\n");
    return 0;
}
