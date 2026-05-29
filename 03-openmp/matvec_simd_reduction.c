#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <omp.h>

#define DEFAULT_M 4096
#define DEFAULT_N 4096

// 計測用の補助関数
void run_calculation(double *A, double *x, double *y, int M, int N, const char *label) {
    double start_time, end_time;

    // 計測開始
    start_time = omp_get_wtime();

    // 行列ベクトル積の計算 (y = A * x)
    #pragma omp parallel for
    for (int i = 0; i < M; i++) {
        double sum = 0.0;
        #pragma omp simd reduction(+:sum)
        for (int j = 0; j < N; j++) {
            sum += A[(size_t)i * (size_t)N + (size_t)j] * x[j];
        }
        y[i] = sum;
    }

    // 計測終了
    end_time = omp_get_wtime();

    printf("%s: Execution Time: %f sec\n", label, end_time - start_time);
    printf("y[0] = %f, y[M-1] = %f\n", y[0], y[M-1]);
}

static int parse_size(int argc, char **argv) {
    int size = DEFAULT_M;

    for (int i = 1; i < argc; i++) {
        if ((strcmp(argv[i], "--size") == 0 || strcmp(argv[i], "-n") == 0) && i + 1 < argc) {
            size = atoi(argv[++i]);
        }
    }

    return size;
}

int main(int argc, char **argv) {
    int M = parse_size(argc, argv);
    int N = M;

    double *A = (double *)malloc((size_t)M * (size_t)N * sizeof(double));
    double *x = (double *)malloc((size_t)N * sizeof(double));
    double *y = (double *)malloc((size_t)M * sizeof(double));

    if (A == NULL || x == NULL || y == NULL) {
        fprintf(stderr, "malloc failed\n");
        free(A);
        free(x);
        free(y);
        return 1;
    }

    // 1. データの初期化
    #pragma omp parallel for
    for (int i = 0; i < M; i++) {
        for (int j = 0; j < N; j++) {
            A[(size_t)i * (size_t)N + (size_t)j] = (double)(i + j) / N;
        }
        y[i] = 0.0;
    }

    #pragma omp parallel for
    for (int j = 0; j < N; j++) {
        x[j] = 1.0;
    }

    printf("[Parallel with SIMD Reduction]\n");
    run_calculation(A, x, y, M, N, "Parallel with SIMD Reduction");

    free(A);
    free(x);
    free(y);

    return 0;
}