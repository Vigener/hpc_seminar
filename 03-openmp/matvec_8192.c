#include <stdio.h>
#include <stdlib.h>
#include <omp.h>

// サイズを大きくして測定精度を上げます（実行時間が長すぎる場合は調整してください）
#define M 8192
#define N 8192

// 計測用の補助関数
void run_calculation(double **A, double *x, double *y, int use_parallel, int use_simd, const char *label) {
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
    // ------------------------------------------------

    // 計測開始
    start_time = omp_get_wtime();

    // 本番の行列ベクトル積の計算
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
    // macOS等でのスタックオーバーフローや巨大なグローバル変数によるエラーを防ぐため、ヒープメモリ(malloc)を使用します
    double **A = (double **)malloc(M * sizeof(double *));
    for (int i = 0; i < M; i++) {
        A[i] = (double *)malloc(N * sizeof(double));
    }
    double *x = (double *)malloc(N * sizeof(double));
    double *y = (double *)malloc(M * sizeof(double));

    // 1. データの初期化 (First-touchポリシー適用のため並列化)
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
    run_calculation(A, x, y, 0, 0, "Serial");

    printf("\n");

    printf("[Parallel]\n");
    run_calculation(A, x, y, 1, 0, "Parallel");

    printf("\n");

    printf("[Parallel with SIMD]\n");
    run_calculation(A, x, y, 1, 1, "Parallel with SIMD");

    // メモリ解放
    for (int i = 0; i < M; i++) {
        free(A[i]);
    }
    free(A);
    free(x);
    free(y);

    return 0;
}