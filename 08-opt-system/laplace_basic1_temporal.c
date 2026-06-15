/*
 * Laplace equation with explicit method (Temporal Blocking 1D)
 * with Custom MPI_Wtime Profiling
 */

#include <math.h>
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

/* square region */
#ifndef XSIZE
#define XSIZE 256
#endif
#ifndef YSIZE
#define YSIZE 256
#endif
#define PI 3.1415927
#ifndef NITER
#define NITER 10000
#endif

// 配列のサイズを +4 (左右に2つずつのゴーストセル) 確保するため、ポインタで管理
double (*u)[YSIZE + 2];
double (*uu)[YSIZE + 2];
double time1, time2;

void lap_solve(MPI_Comm);

int myid, numprocs;
int namelen;
char processor_name[MPI_MAX_PROCESSOR_NAME];
int xsize;

void initialize() {
    int x, y;
    int global_x;

    /* 初期値を設定 (ローカルインデックス 2 〜 xsize+1 が実データ領域) */
    for (x = 2; x <= xsize + 1; x++) {
        global_x = (x - 1) + xsize * myid; // グローバルなx座標を計算
        for (y = 1; y <= YSIZE; y++) {
            u[x][y] = sin((global_x - 1.0) / XSIZE * PI) + cos((y - 1.0) / YSIZE * PI);
        }
    }

    /* 境界をゼロクリア (ゴーストセル2列分を含む) */
    for (x = 0; x <= xsize + 3; x++) {
        u[x][0] = u[x][YSIZE + 1] = 0.0;
        uu[x][0] = uu[x][YSIZE + 1] = 0.0;
    }

    for (y = 0; y <= YSIZE + 1; y++) {
        // 左側のゴーストセル (0, 1)
        u[0][y] = u[1][y] = 0.0;
        uu[0][y] = uu[1][y] = 0.0;
        // 右側のゴーストセル (xsize+2, xsize+3)
        u[xsize + 2][y] = u[xsize + 3][y] = 0.0;
        uu[xsize + 2][y] = uu[xsize + 3][y] = 0.0;
    }
}

#define TAG_1 100
#define TAG_2 101

#ifndef FALSE
#define FALSE 0
#endif

void lap_solve(MPI_Comm comm) {
    int x, y, k;
    double sum, t_sum;
    MPI_Request req1, req2;
    MPI_Status status1, status2;
    MPI_Comm comm1d;
    int down, up;
    int periods[1] = {FALSE};

    /* 時間計測用の変数 */
    double t_start, t_end;
    double local_comm_time = 0.0;
    double local_comp_time = 0.0;
    double max_comm_time, max_comp_time;

    /*
     * Create one dimensional cartesian topology with
     * nonperiodical boundary
     */
    MPI_Cart_create(comm, 1, &numprocs, periods, FALSE, &comm1d);

    /* calculate process ranks for 'down' and 'up' */
    MPI_Cart_shift(comm1d, 0, 1, &down, &up);

    /* NITERを2ステップずつ進める (通信回数が半減する) */
    for (k = 0; k < NITER; k += 2) {

        /* =========================================================
         * 計算フェーズ (データコピー)
         * ========================================================= */
        t_start = MPI_Wtime();

        /* old <- new (実データ領域 2 〜 xsize+1 をコピー) */
        for (x = 2; x <= xsize + 1; x++) {
            for (y = 1; y <= YSIZE; y++) {
                uu[x][y] = u[x][y];
            }
        }

        t_end = MPI_Wtime();
        local_comp_time += (t_end - t_start);

        /* =========================================================
         * 通信フェーズ (2行分まとめて送受信)
         * ========================================================= */
        t_start = MPI_Wtime();

        int send_count = 2 * (YSIZE + 2); // 2行分を連続メモリとして送受信

        /* recv from down (局所の左端ゴーストセル 0,1 へ2行分受信) */
        if (down != MPI_PROC_NULL) {
            MPI_Irecv(&uu[0][0], send_count, MPI_DOUBLE, down, TAG_1, comm1d, &req1);
        } else {
            req1 = MPI_REQUEST_NULL;
        }

        /* recv from up (局所の右端ゴーストセル xsize+2, xsize+3 へ2行分受信) */
        if (up != MPI_PROC_NULL) {
            MPI_Irecv(&uu[xsize + 2][0], send_count, MPI_DOUBLE, up, TAG_2, comm1d, &req2);
        } else {
            req2 = MPI_REQUEST_NULL;
        }

        /* send to down (局所の左端データ 2,3 を2行分送信) */
        if (down != MPI_PROC_NULL) {
            MPI_Send(&u[2][0], send_count, MPI_DOUBLE, down, TAG_2, comm1d);
        }

        /* send to up (局所の右端データ xsize, xsize+1 を2行分送信) */
        if (up != MPI_PROC_NULL) {
            MPI_Send(&u[xsize][0], send_count, MPI_DOUBLE, up, TAG_1, comm1d);
        }

        MPI_Wait(&req1, &status1);
        MPI_Wait(&req2, &status2);

        t_end = MPI_Wtime();
        local_comm_time += (t_end - t_start);

        /* =========================================================
         * 計算フェーズ (境界を超えた広域計算 ＋ 本来の領域計算)
         * ========================================================= */
        t_start = MPI_Wtime();

        /* 1反復目 (広め) */
        int x_start_wide = (down != MPI_PROC_NULL) ? 1 : 2;
        int x_end_wide   = (up != MPI_PROC_NULL) ? xsize + 2 : xsize + 1;

        for (x = x_start_wide; x <= x_end_wide; x++) {
            for (y = 1; y <= YSIZE; y++) {
                u[x][y] = 0.25 * (uu[x - 1][y] + uu[x + 1][y] + uu[x][y - 1] + uu[x][y + 1]);
            }
        }

        /* 2反復目 (通常サイズ) */
        for (x = 2; x <= xsize + 1; x++) {
            for (y = 1; y <= YSIZE; y++) {
                uu[x][y] = 0.25 * (u[x - 1][y] + u[x + 1][y] + u[x][y - 1] + u[x][y + 1]);
            }
        }

        /* 次のループのために uu の結果を u に書き戻す (ただし最後のステップ以外) */
        if (k < NITER - 2) {
            for (x = 2; x <= xsize + 1; x++) {
                for (y = 1; y <= YSIZE; y++) {
                    u[x][y] = uu[x][y];
                }
            }
        }

        t_end = MPI_Wtime();
        local_comp_time += (t_end - t_start);
    }

    /* * 計測結果を全プロセスから収集し、最大の通信・計算時間を割り出す
     */
    MPI_Reduce(&local_comm_time, &max_comm_time, 1, MPI_DOUBLE, MPI_MAX, 0, comm1d);
    MPI_Reduce(&local_comp_time, &max_comp_time, 1, MPI_DOUBLE, MPI_MAX, 0, comm1d);

    if (myid == 0) {
        printf("--- Profiling Results ---\n");
        printf("Max Communication Time = %g sec (%g sec/iter)\n", max_comm_time, max_comm_time / NITER);
        printf("Max Computation Time   = %g sec (%g sec/iter)\n", max_comp_time, max_comp_time / NITER);
        printf("-------------------------\n");
    }

    /* check sum */
    sum = 0.0;
    for (x = 2; x <= xsize + 1; x++) {
        for (y = 1; y <= YSIZE; y++) {
            sum += u[x][y] - uu[x][y];
        }
    }

    MPI_Reduce(&sum, &t_sum, 1, MPI_DOUBLE, MPI_SUM, 0, comm1d);

    if (myid == 0) {
        printf("sum = %g\n", t_sum);
    }

    MPI_Comm_free(&comm1d);
}

int main(int argc, char *argv[]) {
    MPI_Init(&argc, &argv);

    MPI_Comm_size(MPI_COMM_WORLD, &numprocs);
    MPI_Comm_rank(MPI_COMM_WORLD, &myid);
    MPI_Get_processor_name(processor_name, &namelen);

    if (myid == 0) {
        fprintf(stderr, "Process %d on %s\n", myid, processor_name);
    }

    xsize = XSIZE / numprocs;
    if ((XSIZE % numprocs) != 0) {
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    /* 局所領域 + ゴーストセル(片側2列分 = 計+4列) のメモリを動的確保 */
    u = malloc((xsize + 4) * sizeof(*u));
    uu = malloc((xsize + 4) * sizeof(*uu));
    if (u == NULL || uu == NULL) {
        fprintf(stderr, "Process %d: Memory allocation failed.\n", myid);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    initialize();

    MPI_Barrier(MPI_COMM_WORLD);
    time1 = MPI_Wtime();

    lap_solve(MPI_COMM_WORLD);

    MPI_Barrier(MPI_COMM_WORLD);
    time2 = MPI_Wtime();

    if (myid == 0) {
        printf("time = %g\n", time2 - time1);
        printf("time_per_iter = %g\n", (time2 - time1) / NITER);
    }

    free(u);
    free(uu);

    MPI_Finalize();
    return (0);
}
