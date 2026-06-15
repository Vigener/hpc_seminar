#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <sys/time.h>

// =====================================================================
// コンパイルオプション（-DN=2000等）とヘッダ内部の引数名の衝突を回避
// =====================================================================
#pragma push_macro("N")
#undef N
#include <Accelerate/Accelerate.h>
#pragma pop_macro("N")

#ifndef N
#define N 2000
#endif

double get_time() {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec + tv.tv_usec * 1e-6;
}

int main(void) {
    // メモリの確保
    double *A = (double *)malloc(sizeof(double) * N * N);
    double *x = (double *)malloc(sizeof(double) * N);
    double *y = (double *)malloc(sizeof(double) * N);

    if (A == NULL || x == NULL || y == NULL) {
        fprintf(stderr, "Memory allocation failed.\n");
        return 1;
    }

    // 初期化
    for (int i = 0; i < N * N; i++) {
        A[i] = 1.0;
    }
    for (int i = 0; i < N; i++) {
        x[i] = 1.0;
        y[i] = 0.0;
    }

    // 計測開始
    double start = get_time();

    // Mac純正のAccelerateフレームワークを使用した行列ベクトル積 (y = alpha*A*x + beta*y)
    // dgemv (Double precision General Matrix-Vector multiplication) または
    // dgemm (Double precision General Matrix-Matrix multiplication) を使用
    cblas_dgemv(CblasRowMajor, CblasNoTrans, N, N, 1.0, A, N, x, 1, 0.0, y, 1);

    // 計測終了
    double end = get_time();
    double exec_time = end - start;

    // 実行時間の出力
    printf("%f\n", exec_time);

    // 最適化による計算の省略を防ぐためのダミー出力
    printf("Dummy: %f\n", y[0]);

    // メモリの解放
    free(A);
    free(x);
    free(y);

    return 0;
}
