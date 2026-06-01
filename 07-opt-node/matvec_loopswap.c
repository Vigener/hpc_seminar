#include <stdio.h>
#define N 1000
int main(void) {
  static double a[N][N], b[N][N], c[N][N];
  int i, j, k;
  for (i = 0; i < N; i++) {
    for (j = 0; j < N; j++) {
      a[i][j] = rand(); b[i][j] = rand(); c[i][j] = rand();
    }
  }
  // ループの入れ替えを適用（i -> k -> j の順）
  for (i = 0; i < N; i++) {
    for (k = 0; k < N; k++) {
        for (j = 0; j < N; j++) {
        c[i][j] += a[i][k] * b[k][j];
      }
    }
  }
  return 0;
}