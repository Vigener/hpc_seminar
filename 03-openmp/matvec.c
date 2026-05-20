#include <stdio.h>
#include <stdlib.h>
#include <omp.h>

#define M 4096
#define N 4096

double A[M][N], x[N], y[M];

// 計測用の補助関数
void run_calculation(int use_parallel, int use_simd, const char *label) {
    double start_time, end_time;

    // ウォームアップ1（イニシャルゼーション）：全スレッドでメモリアクセスを初期化
    #pragma omp parallel for
    for (int i = 0; i < M; i++) {
        double sum = 0.0;
        #pragma omp simd reduction(+:sum)
        for (int j = 0; j < N; j++) {
            sum += A[i][j] * x[j];
        }
        y[i] = sum;
    }

    // ウォームアップ2（モード別）：計測対象のモードに合わせたウォームアップ
    if (use_parallel) {
        #pragma omp parallel for
        for (int i = 0; i < M; i++) {
            double sum = 0.0;
            if (use_simd) {
                #pragma omp simd reduction(+:sum)
                for (int j = 0; j < N; j++) {
                    sum += A[i][j] * x[j];
                }
            } else {
                for (int j = 0; j < N; j++) {
                    sum += A[i][j] * x[j];
                }
            }
            y[i] = sum;
        }
    } else {
        for (int i = 0; i < M; i++) {
            double sum = 0.0;
            if (use_simd) {
                #pragma omp simd reduction(+:sum)
                for (int j = 0; j < N; j++) {
                    sum += A[i][j] * x[j];
                }
            } else {
                for (int j = 0; j < N; j++) {
                    sum += A[i][j] * x[j];
                }
            }
            y[i] = sum;
        }
    }

    // 計測開始
    start_time = omp_get_wtime();

    // 本番の行列ベクトル積の計算 (y = A * x)
    if (use_parallel) {
        #pragma omp parallel for
        for (int i = 0; i < M; i++) {
            double sum = 0.0;
            if (use_simd) {
                #pragma omp simd reduction(+:sum)
                for (int j = 0; j < N; j++) {
                    sum += A[i][j] * x[j];
                }
            } else {
                for (int j = 0; j < N; j++) {
                    sum += A[i][j] * x[j];
                }
            }
            y[i] = sum;
        }
    } else {
        for (int i = 0; i < M; i++) {
            double sum = 0.0;
            if (use_simd) {
                #pragma omp simd reduction(+:sum)
                for (int j = 0; j < N; j++) {
                    sum += A[i][j] * x[j];
                }
            } else {
                for (int j = 0; j < N; j++) {
                    sum += A[i][j] * x[j];
                }
            }
            y[i] = sum;
        }
    }

    // 計測終了
    end_time = omp_get_wtime();

    printf("%s: Execution Time: %f sec\n", label, end_time - start_time);
    printf("y[0] = %f, y[M-1] = %f\n", y[0], y[M-1]);
}

int main() {
    // 1. データの初期化
    #pragma omp parallel for
    for (int i = 0; i < M; i++) {
        for (int j = 0; j < N; j++) {
            A[i][j] = (double)(i + j) / N;
        }
        y[i] = 0.0;
    }

    #pragma omp parallel for
    for (int j = 0; j < N; j++) {
        x[j] = 1.0;
    }

    // 3パターンを比較する
    printf("[Serial]\n");
    run_calculation(0, 0, "Serial");

    printf("\n");

    printf("[Parallel]\n");
    run_calculation(1, 0, "Parallel");

    printf("\n");

    printf("[Parallel with SIMD]\n");
    run_calculation(1, 1, "Parallel with SIMD");

    return 0;
}
