#include <stdio.h>
#include <stdlib.h>
#include <time.h>

#define N 1000

#define B_I 4
#define B_J 4
#define B_K 4

int main(void) {
  static double a[N][N], b[N][N], c[N][N];
  int i, j, k;
  int ib, jb, kb; // ブロックの基準点を動かすための変数
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

  // 外側の3重ループで、ブロックの左上の座標 (ib, jb, kb) をスライドさせる
  for (ib = 0; ib < N; ib += B_I) {
    for (jb = 0; jb < N; jb += B_J) {
      for (kb = 0; kb < N; kb += B_K) {

        // N=1000がブロックサイズで割り切れない場合の配列外参照を防ぐ安全処理
        int i_max = (ib + B_I < N) ? ib + B_I : N;
        int j_max = (jb + B_J < N) ? jb + B_J : N;
        int k_max = (kb + B_K < N) ? kb + B_K : N;

        // ブロック内部の計算（matvec_original.c と全く同じ i -> j -> k 順）
        for (i = ib; i < i_max; i++) {
          for (j = jb; j < j_max; j++) {
            for (k = kb; k < k_max; k++) {
              c[i][j] += a[i][k] * b[k][j];
            }
          }
        }

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