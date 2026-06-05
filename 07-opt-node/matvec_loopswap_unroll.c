#include <stdio.h>
#include <stdlib.h>
#include <time.h>

// 外から指定（-DN=2000など）がなければ、デフォルトで1000にする
#ifndef N
#define N 1000
#endif

int main(void) {
  static double a[N][N], b[N][N], c[N][N];
  int i, j, k;
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

  // ループ入れ替え (i -> k -> j) + 内側ループの2展開
  for (i = 0; i < N; i++) {
    for (k = 0; k < N; k++) {

      // 最内ループ(j)が回っている間、a[i][k] の値は変化しないため、
      // 毎回メモリから読まずにレジスタ(a_ik)に保持しておく
      double a_ik = a[i][k];

      for (j = 0; j < N; j += 4) {
        c[i][j] += a_ik * b[k][j];
        c[i][j + 1] += a_ik * b[k][j + 1];
        c[i][j + 2] += a_ik * b[k][j + 2];
        c[i][j + 3] += a_ik * b[k][j + 3];
      }
    }
  }

  // ==== 計測終了 ====
  clock_gettime(CLOCK_MONOTONIC, &end);

  double elapsed_time =
      (end.tv_sec - start.tv_sec) + (end.tv_nsec - start.tv_nsec) * 1e-9;

  printf("%f\n", elapsed_time);
  printf("Dummy: %f\n", c[0][0]);

  return 0;
}
