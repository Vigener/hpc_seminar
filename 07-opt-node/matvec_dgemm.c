#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <cblas.h> // BLASライブラリのヘッダ

// 外から指定（-DN=20'cblas.h' file not found00など）がなければ、デフォルトで1000にする
#ifndef N
#define N 1000
#endif

int main(void) {
  static double a[N][N], b[N][N], c[N][N];
  int i, j; // kはBLAS内で処理されるため不要
  struct timespec start, end;

  for (i = 0; i < N; i++) {
    for (j = 0; j < N; j++) {
      a[i][j] = rand();
      b[i][j] = rand();
      c[i][j] = rand();
    }
  }

  // ==== 計測開始 ====
  clock_gettime(CLOCK_MONOTONIC, &start);

  // c[i][j] += a[i][k] * b[k][j] をDGEMMで実行 (C = 1.0 * A*B + 1.0 * C)
  cblas_dgemm(
      CblasRowMajor, // C言語の配列は「行優先(RowMajor)」
      CblasNoTrans,  // Aは転置しない
      CblasNoTrans,  // Bは転置しない
      N,             // 行列Aの行数 M
      N,             // 行列Bの列数 N
      N,             // 行列Aの列数（=Bの行数） K
      1.0,           // alpha (A*Bにかける係数)
      (double *)a,   // 行列Aのポインタ
      N,             // lda (Aの1行の要素数)
      (double *)b,   // 行列Bのポインタ
      N,             // ldb (Bの1行の要素数)
      1.0,           // beta (Cにかける係数。今回は += なので 1.0)
      (double *)c,   // 行列Cのポインタ
      N              // ldc (Cの1行の要素数)
  );

  // ==== 計測終了 ====
  clock_gettime(CLOCK_MONOTONIC, &end);

  double elapsed_time = (end.tv_sec - start.tv_sec) +
                        (end.tv_nsec - start.tv_nsec) * 1e-9;

  printf("%f\n", elapsed_time);
  printf("Dummy: %f\n", c[0][0]);

  return 0;
}
