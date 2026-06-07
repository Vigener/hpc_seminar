#include <stdio.h>
#include <stdlib.h>
#include <time.h>

// 外から指定（-DN=2000など）がなければ、デフォルトで1000にする
#ifndef N
#define N 1000
#endif

// 各ブロックサイズも外から指定がなければ、デフォルトで32にする
#ifndef B_I
#define B_I 32
#endif
#ifndef B_J
#define B_J 32
#endif
#ifndef B_K
#define B_K 32
#endif

int main(void) {
  static double a[N][N], b[N][N], c[N][N];
  int i, j, k;
  int ib, jb, kb;
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

  // 外側の3重ループ（ブロックの基準点をスライド）
  for (ib = 0; ib < N; ib += B_I) {
    for (jb = 0; jb < N; jb += B_J) {
      for (kb = 0; kb < N; kb += B_K) {

        // 配列外参照を防ぐための境界計算
        int i_max = (ib + B_I < N) ? ib + B_I : N;
        int j_max = (jb + B_J < N) ? jb + B_J : N;
        int k_max = (kb + B_K < N) ? kb + B_K : N;

        // ★ハイブリッド部分：ループ入れ替え (i -> k -> j 順)
        for (i = ib; i < i_max; i++) {
          for (k = kb; k < k_max; k++) {

            // a[i][k] は一番内側の j ループでは値が変わらないため、
            // キャッシュではなく最も高速な「レジスタ」に保持させる
            double a_ik = a[i][k];

            for (j = jb; j < j_max; j++) {
              c[i][j] += a_ik * b[k][j];
            }
          }
        }
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
