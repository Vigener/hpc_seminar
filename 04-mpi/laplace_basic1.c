/*
 * Laplace equation with explicit method
 */

#include <math.h>
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

/* square region */
#define XSIZE 256
#define YSIZE 256
#define PI 3.1415927
#define NITER 10000

// グローバル変数を静的配列からポインタに変更(これで、必要に応じてxsizeに応じたメモリを動的に確保できるようになる)
double (*u)[YSIZE + 2];
double (*uu)[YSIZE + 2];
// double u[XSIZE + 2][YSIZE + 2], uu[XSIZE + 2][YSIZE + 2];
double time1, time2;

void lap_solve(MPI_Comm);

int myid, numprocs;
int namelen;
char processor_name[MPI_MAX_PROCESSOR_NAME];
int xsize;

void initialize() {
    int x, y;
    int global_x; // xは各プロセスのローカルなインデックス、global_xは全体のインデックス

    /* 初期値を設定 (ローカルインデックスからグローバル座標を計算して代入する)*/
    for (x = 1; x < xsize; x++) {
        global_x = x + xsize * myid; // グローバルなx座標を計算
        for (y = 1; y < YSIZE + 1; y++) {
            u[x][y] = sin((global_x - 1.0) / XSIZE * PI) + cos((y - 1.0) / YSIZE * PI);
        }
    }

    /* 境界をゼロクリア */
    for (x = 0; x < xsize + 1; x++) {
        u[x][0] = u[x][YSIZE + 1] = 0.0;
        uu[x][0] = uu[x][YSIZE + 1] = 0.0;
    }

    for (y = 0; y < YSIZE + 2; y++) {
        u[0][y] = u[xsize + 1][y] = 0.0;
        uu[0][y] = uu[xsize + 1][y] = 0.0;
    }
}

#define TAG_1 100
#define TAG_2 101

#ifndef FALSE
#define FALSE 0
#endif

void lap_solve(MPI_Comm comm) {
    int x, y, k;
    double sum;
    double t_sum;
    // int x_start, x_end;
    MPI_Request req1, req2;
    MPI_Status status1, status2;
    MPI_Comm comm1d;
    int down, up;
    int periods[1] = {FALSE};

    /*
     * Create one dimensional cartesian topology with
     * nonperiodical boundary
     */
    MPI_Cart_create(comm, 1, &numprocs, periods, FALSE, &comm1d);

    /* calculate process ranks for 'down' and 'up' */
    MPI_Cart_shift(comm1d, 0, 1, &down, &up);

    // int x_start, x_end;
    // x_start = 1 + xsize * myid;
    // x_end = 1 + xsize * (myid + 1);

    for (k = 0; k < NITER; k++) {
        /* old <- new */
        for (x = 1; x < xsize; x++) {
            for (y = 1; y < YSIZE + 1; y++) {
                uu[x][y] = u[x][y];
            }
        }
        
        /* recv from down (局所の左端ゴーストセル 0 へ受信) */
        MPI_Irecv(&uu[0][1], YSIZE, MPI_DOUBLE, down, TAG_1, comm1d, &req1);

        /* recv from up (局所の右端ゴーストセル xsize+1 へ受信) */
        MPI_Irecv(&uu[xsize + 1][1], YSIZE, MPI_DOUBLE, up, TAG_2, comm1d, &req2);

        /* send to down (局所の左端データ 1 を送信) */
        MPI_Send(&u[1][1], YSIZE, MPI_DOUBLE, down, TAG_2, comm1d);

        /* send to up (局所の右端データ xsize を送信) */
        MPI_Send(&u[xsize][1], YSIZE, MPI_DOUBLE, up, TAG_1, comm1d);

        MPI_Wait(&req1, &status1);
        MPI_Wait(&req2, &status2);

        /* update (局所インデックスを使用)*/
        for (x = 1; x < xsize; x++) {
            for (y = 1; y < YSIZE + 1; y++) {
                u[x][y] = .25 * (uu[x - 1][y] + uu[x + 1][y] + uu[x][y - 1] + uu[x][y + 1]);
            }
        }
    }

    /* check sum */
    sum = 0.0;
    for (x = 1; x < xsize; x++) {
        for (y = 1; y < YSIZE + 1; y++) {
            sum += uu[x][y] - u[x][y];
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

    fprintf(stderr, "Process %d on %s\n", myid, processor_name);

    xsize = XSIZE / numprocs;
    if ((XSIZE % numprocs) != 0) {
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    // 局所領域+ゴーストセル分のメモリを動的確保
    u = malloc((xsize + 2) * sizeof(*u));
    uu = malloc((xsize + 2) * sizeof(*uu));
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
    }

    // 動的に確保したメモリを解放
    free(u);
    free(uu);

    MPI_Finalize();
    return (0);
}