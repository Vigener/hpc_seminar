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

  for (i = 0; i < N; i++) {
    for (j = 0; j < N; j++) {
      a[i][j] = rand(); 
      b[i][j] = rand(); 
      c[i][j] = rand();
    }
  }

  // ==== 計測開始 ====
  clock_gettime(CLOCK_MONOTONIC, &start);

  // ループ入れ替え (i -> k -> j) + SIMD
  for (i = 0; i < N; i++) {
    for (k = 0; k < N; k++) {
      #pragma GCC ivdep
      for (j = 0; j < N; j++) {
        c[i][j] += a[i][k] * b[k][j];
      }
    }
  }

  // ==== 計測終了 ====
  clock_gettime(CLOCK_MONOTONIC, &end);

  double elapsed_time = (end.tv_sec - start.tv_sec) + 
                        (end.tv_nsec - start.tv_nsec) * 1e-9;

  printf("%f\n", elapsed_time);
  printf("Dummy: %f\n", c[0][0]);

  return 0;
}