  #include <stdio.h>
#include <stdlib.h>
#include <time.h> // 時間計測のために追加

#define N 1000

int main(void) {
  static double a[N][N], b[N][N], c[N][N];
  int i, j, k;
  struct timespec start, end; // 時間を記録する構造体

  for (i = 0; i < N; i++) {
    for (j = 0; j < N; j++) {
      a[i][j] = rand(); 
      b[i][j] = rand(); 
      c[i][j] = rand();
    }
  }

  // ==== 計測開始 ====
  clock_gettime(CLOCK_MONOTONIC, &start);

  // ループの入れ替えを適用（i -> k -> j の順）
  for (i = 0; i < N; i++) {
    for (k = 0; k < N; k++) {
      for (j = 0; j < N; j++) {
        c[i][j] += a[i][k] * b[k][j];
      }
    }
  }

  // ==== 計測終了 ====
  clock_gettime(CLOCK_MONOTONIC, &end);

  // 秒とナノ秒を組み合わせて、かかった時間（秒）を計算
  double elapsed_time = (end.tv_sec - start.tv_sec) + 
                        (end.tv_nsec - start.tv_nsec) * 1e-9;

  // 実行時間のみを標準出力（後でスクリプト等で集計しやすいように）
  printf("%f\n", elapsed_time);

  // （おまけ）コンパイラによる「計算結果の破棄」を完全に防ぐためのダミー出力
  // cの要素を1つだけ出力することで、コンパイラに「cは後で使う」と思わせる
  printf("Dummy: %f\n", c[0][0]);

  return 0;
}