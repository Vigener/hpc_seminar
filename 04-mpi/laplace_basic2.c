/*
 * Laplace equation with explicit method (2D Decomposition)
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

/* グローバル変数を「ポインタのポインタ」に変更し、2D動的確保に対応 */
double **u, **uu;
double *u_data, *uu_data; // 実データが入る連続メモリ領域
double time1, time2;

void lap_solve(MPI_Comm);

int myid, numprocs;
int namelen;
char processor_name[MPI_MAX_PROCESSOR_NAME];

/* 2次元分割用の変数群 */
int xsize, ysize;
int dims[2] = {0, 0};
int coords[2];
MPI_Comm comm2d;

void initialize() {
    int x, y;
    int global_x, global_y;

    /* 初期値を設定 (ローカルインデックスから2Dのグローバル座標を計算して代入) */
    for (x = 1; x <= xsize; x++) {
        global_x = x + coords[0] * xsize; 
        for (y = 1; y <= ysize; y++) {
            global_y = y + coords[1] * ysize; 
            u[x][y] = sin((global_x - 1.0) / XSIZE * PI) + cos((global_y - 1.0) / YSIZE * PI);
        }
    }

    /* X方向（行）の境界をゼロクリア */
    for (x = 0; x <= xsize + 1; x++) {
        u[x][0] = u[x][ysize + 1] = 0.0;
        uu[x][0] = uu[x][ysize + 1] = 0.0;
    }

    /* Y方向（列）の境界をゼロクリア */
    for (y = 0; y <= ysize + 1; y++) {
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
    MPI_Request reqs[4];
    MPI_Status stats[4];
    
    int left_x, right_x; // X方向の隣接プロセス
    int left_y, right_y; // Y方向の隣接プロセス

    /* X方向（行の移動）、Y方向（列の移動）の隣接ランクを計算 */
    MPI_Cart_shift(comm, 0, 1, &left_x, &right_x);
    MPI_Cart_shift(comm, 1, 1, &left_y, &right_y);

    /* Y方向（列）の非連続データ送受信用に派生データ型を作成 */
    MPI_Datatype col_type;
    MPI_Type_vector(xsize, 1, ysize + 2, MPI_DOUBLE, &col_type);
    MPI_Type_commit(&col_type);

    for (k = 0; k < NITER; k++) {
        /* old <- new */
        for (x = 1; x <= xsize; x++) {
            for (y = 1; y <= ysize; y++) {
                uu[x][y] = u[x][y];
            }
        }
        
        /* === X方向 (行: 連続データ) の通信 === */
        /* 受信: 自分の上下のゴーストセルへ */
        MPI_Irecv(&uu[0][1], ysize, MPI_DOUBLE, left_x, TAG_1, comm, &reqs[0]);
        MPI_Irecv(&uu[xsize + 1][1], ysize, MPI_DOUBLE, right_x, TAG_2, comm, &reqs[1]);
        /* 送信: 自分の上下の計算領域端から */
        MPI_Send(&u[1][1], ysize, MPI_DOUBLE, left_x, TAG_2, comm);
        MPI_Send(&u[xsize][1], ysize, MPI_DOUBLE, right_x, TAG_1, comm);
        
        MPI_Waitall(2, reqs, stats);

        /* === Y方向 (列: 非連続データ) の通信 === */
        /* 受信: 自分の左右のゴーストセルへ (col_typeを使用) */
        MPI_Irecv(&uu[1][0], 1, col_type, left_y, TAG_1, comm, &reqs[2]);
        MPI_Irecv(&uu[1][ysize + 1], 1, col_type, right_y, TAG_2, comm, &reqs[3]);
        /* 送信: 自分の左右の計算領域端から (col_typeを使用) */
        MPI_Send(&u[1][1], 1, col_type, left_y, TAG_2, comm);
        MPI_Send(&u[1][ysize], 1, col_type, right_y, TAG_1, comm);

        MPI_Waitall(2, &reqs[2], stats);

        /* update */
        for (x = 1; x <= xsize; x++) {
            for (y = 1; y <= ysize; y++) {
                u[x][y] = .25 * (uu[x - 1][y] + uu[x + 1][y] + uu[x][y - 1] + uu[x][y + 1]);
            }
        }
    }

    /* 使用したデータ型を解放 */
    MPI_Type_free(&col_type);

    /* check sum */
    sum = 0.0;
    for (x = 1; x <= xsize; x++) {
        for (y = 1; y <= ysize; y++) {
            sum += uu[x][y] - u[x][y];
        }
    }

    MPI_Reduce(&sum, &t_sum, 1, MPI_DOUBLE, MPI_SUM, 0, comm);

    if (myid == 0) {
        printf("sum = %g\n", t_sum);
    }
}

int main(int argc, char *argv[]) {
    MPI_Init(&argc, &argv);

    MPI_Comm_size(MPI_COMM_WORLD, &numprocs);
    MPI_Comm_rank(MPI_COMM_WORLD, &myid);
    MPI_Get_processor_name(processor_name, &namelen);

    /* 2次元トポロジーの分割数を自動決定 (例: 4プロセスなら 2x2) */
    MPI_Dims_create(numprocs, 2, dims);

    /* 周期境界なしの2次元Cartesianコミュニケータを作成 */
    int periods[2] = {FALSE, FALSE};
    MPI_Cart_create(MPI_COMM_WORLD, 2, dims, periods, FALSE, &comm2d);
    
    /* 自分のプロセス座標を取得 */
    MPI_Cart_coords(comm2d, myid, 2, coords);

    if (myid == 0) {
        fprintf(stderr, "Grid Size: %d x %d\n", dims[0], dims[1]);
    }

    /* 各プロセスの担当サイズを計算 */
    xsize = XSIZE / dims[0];
    ysize = YSIZE / dims[1];

    if ((XSIZE % dims[0]) != 0 || (YSIZE % dims[1]) != 0) {
        if (myid == 0) fprintf(stderr, "Error: Grid cannot evenly divide region.\n");
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    /* 実データ領域 (連続した1D配列) を確保 */
    u_data = malloc((xsize + 2) * (ysize + 2) * sizeof(double));
    uu_data = malloc((xsize + 2) * (ysize + 2) * sizeof(double));

    /* ポインタ配列 (2Dアクセスのための行ポインタ) を確保 */
    u = malloc((xsize + 2) * sizeof(double*));
    uu = malloc((xsize + 2) * sizeof(double*));

    if (u_data == NULL || uu_data == NULL || u == NULL || uu == NULL) {
        fprintf(stderr, "Process %d: Memory allocation failed.\n", myid);
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    /* 行ポインタに連続メモリのアドレスをセット */
    for (int i = 0; i < xsize + 2; i++) {
        u[i]  = &u_data[i * (ysize + 2)];
        uu[i] = &uu_data[i * (ysize + 2)];
    }

    /* 全プロセスの座標・設定が完了してから初期化 */
    initialize();

    MPI_Barrier(comm2d);
    time1 = MPI_Wtime();

    lap_solve(comm2d);

    MPI_Barrier(comm2d);
    time2 = MPI_Wtime();

    if (myid == 0) {
        printf("time = %g\n", time2 - time1);
    }

    /* 動的に確保したメモリを解放 */
    free(u);
    free(uu);
    free(u_data);
    free(uu_data);

    /* 独自のコミュニケータを解放 */
    MPI_Comm_free(&comm2d);

    MPI_Finalize();
    return (0);
}