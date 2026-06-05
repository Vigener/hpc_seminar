#include <stdio.h>
#include <stdlib.h>
#include <time.h>

// 外から指定（-DN=2000など）がなければ、デフォルトで1000にする
#ifndef N
#define N 1000
#endif
// パディング用マクロ（列のサイズをずらす）
#define PADDED_N (N + 16)

int main(void) {
  // パディングを適用した配列宣言
  static double a[N][PADDED_N], b[N][PADDED_N], c[N][PADDED_N];
  int i, j, k;
  struct timespec start, end;

  // 初期化ループ（回す回数は元の N のまま）
  for (i = 0; i < N; i++) {
    for (j = 0; j < N; j++) {
      a[i][j] = rand(); 
      b[i][j] = rand(); 
      c[i][j] = rand();
    }
  }

  // ==== 計測開始 ====
  clock_gettime(CLOCK_MONOTONIC, &start);

  // ループ順は元のまま（i -> j -> k）
  for (i = 0; i < N; i++) {
    for (j = 0; j < N; j++) {
      for (k = 0; k < N; k++) {
        c[i][j] += a[i][k] * b[k][j];
      }
    }
  }

  // ==== 計測終了 ====
  clock_gettime(CLOCK_MONOTONIC, &end);

  double elapsed_time = (end.tv_sec - start.tv_sec) + 
                        (end.tv_nsec - start.tv_nsec) * 1e-9;

  printf("%f\n", elapsed_time);
  
  // デッドコード削除を防ぐダミー出力
  printf("Dummy: %f\n", c[0][0]);

  return 0;
}