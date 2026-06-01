#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N 1000

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

  // 手動ループアンローリング単体 (jを2展開)
  for (i = 0; i < N; i++) {
    // 2つずつ進めるため j += 2 (N=1000は2で割り切れるので端数処理は不要)
    for (j = 0; j < N; j += 2) {
      // メモリから c の初期値をレジスタ (s0, s1) に読み込む
      double s0 = c[i][j];
      double s1 = c[i][j+1];
      
      for (k = 0; k < N; k++) {
        // メモリ(c)にはアクセスせず、最速のレジスタ上で計算を回す
        s0 += a[i][k] * b[k][j];
        s1 += a[i][k] * b[k][j+1];
      }
      
      // 計算が終わったら、最後に1回だけメモリに書き戻す
      c[i][j]   = s0;
      c[i][j+1] = s1;
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