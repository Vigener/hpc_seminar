#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#pragma push_macro("N")
#undef N
// フルパスをやめて、通常のインクルードに戻す
#include <cblas.h>
#pragma pop_macro("N")

#ifndef N
#define N 1000
#endif

int main(void) {
  static double a[N][N], b[N][N], c[N][N];
  int i, j;
  struct timespec start, end;

  // 初期化ループ
  for (i = 0; i < N; i++) {
    for (j = 0; j < N; j++) {
      a[i][j] = rand();
      b[i][j] = rand();
      c[i][j] = rand();
    }
  }

  // ==== 計測開始 ====
  clock_gettime(CLOCK_MONOTONIC, &start);

  // 3重ループの代わりに、DGEMM関数を1行だけ呼び出す
  // 数式: C = 1.0 * A * B + 1.0 * C
  cblas_dgemm(
      CblasRowMajor, // C言語の2次元配列は「行優先(RowMajor)」
      CblasNoTrans,  // 行列Aは転置しない
      CblasNoTrans,  // 行列Bは転置しない
      N,             // M (行列Cの行数)
      N,             // N (行列Cの列数)
      N,             // K (行列Aの列数 = 行列Bの行数)
      1.0,           // alpha
      (double *)a,   // 行列Aのポインタ
      N,             // lda
      (double *)b,   // 行列Bのポインタ
      N,             // ldb
      1.0,           // beta (+= なので 1.0)
      (double *)c,   // 行列Cのポインタ
      N              // ldc
  );

  // ==== 計測終了 ====
  clock_gettime(CLOCK_MONOTONIC, &end);

  double elapsed_time = (end.tv_sec - start.tv_sec) +
                        (end.tv_nsec - start.tv_nsec) * 1e-9;

  printf("%f\n", elapsed_time);
  printf("Dummy: %f\n", c[0][0]);

  return 0;
}
