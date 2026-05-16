/*
 * Laplace equation with explicit method (2D Decomposition + One-Sided Communication)
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

/* グローバル変数 */
double **u, **uu;
double *u_data, *uu_data;
double time1, time2;

/* RMA用のウィンドウオブジェクト */
MPI_Win win;

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

    /* 初期値を設定 */
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

#ifndef FALSE
#define FALSE 0
#endif

void lap_solve(MPI_Comm comm) {
    int x, y, k;
    double sum;
    double t_sum;
    
    int left_x, right_x;
    int left_y, right_y;

    /* X方向、Y方向の隣接ランクを計算 */
    MPI_Cart_shift(comm, 0, 1, &left_x, &right_x);
    MPI_Cart_shift(comm, 1, 1, &left_y, &right_y);

    /* Y方向（列）送受信用データ型 */
    MPI_Datatype col_type;
    MPI_Type_vector(xsize, 1, ysize + 2, MPI_DOUBLE, &col_type);
    MPI_Type_commit(&col_type);

    for (k = 0; k < NITER; k++) {
        /* old <- new (ローカルデータの退避) */
        for (x = 1; x <= xsize; x++) {
            for (y = 1; y <= ysize; y++) {
                uu[x][y] = u[x][y];
            }
        }
        
        /* === 片方向通信 (RMA) の開始 === */
        /* RMAエポックの開始：これ以降、リモートメモリへのPutが実行される */
        MPI_Win_fence(0, win);

        /* 
         * 【X方向 (行) のPUT】
         * - 左の隣接プロセス (left_x) の "右端ゴーストセル" へ直接書き込む
         *   相手の uu[xsize+1][1] へのオフセット: (xsize + 1) * (ysize + 2) + 1
         * - 右の隣接プロセス (right_x) の "左端ゴーストセル" へ直接書き込む
         *   相手の uu[0][1] へのオフセット: 0 * (ysize + 2) + 1
         */
        MPI_Put(&u[1][1], ysize, MPI_DOUBLE, left_x, 
                (MPI_Aint)((xsize + 1) * (ysize + 2) + 1), ysize, MPI_DOUBLE, win);
                
        MPI_Put(&u[xsize][1], ysize, MPI_DOUBLE, right_x, 
                (MPI_Aint)(1), ysize, MPI_DOUBLE, win);

        /* 
         * 【Y方向 (列) のPUT】
         * - 上の隣接プロセス (left_y) の "下端ゴーストセル" へ書き込む
         *   相手の uu[1][ysize+1] へのオフセット: 1 * (ysize + 2) + (ysize + 1)
         * - 下の隣接プロセス (right_y) の "上端ゴーストセル" へ書き込む
         *   相手の uu[1][0] へのオフセット: 1 * (ysize + 2) + 0
         */
        MPI_Put(&u[1][1], 1, col_type, left_y, 
                (MPI_Aint)(1 * (ysize + 2) + (ysize + 1)), 1, col_type, win);
                
        MPI_Put(&u[1][ysize], 1, col_type, right_y, 
                (MPI_Aint)(1 * (ysize + 2)), 1, col_type, win);

        /* RMAエポックの終了：全プロセスのPutが完了するまで待機（同期） */
        MPI_Win_fence(0, win);
        /* ============================== */

        /* update (隣接プロセスから書き込まれた最新のゴーストセル uu を使って更新) */
        for (x = 1; x <= xsize; x++) {
            for (y = 1; y <= ysize; y++) {
                u[x][y] = .25 * (uu[x - 1][y] + uu[x + 1][y] + uu[x][y - 1] + uu[x][y + 1]);
            }
        }
    }

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

    /* 2次元トポロジーの分割数を自動決定 */
    MPI_Dims_create(numprocs, 2, dims);

    int periods[2] = {FALSE, FALSE};
    MPI_Cart_create(MPI_COMM_WORLD, 2, dims, periods, FALSE, &comm2d);
    MPI_Cart_coords(comm2d, myid, 2, coords);

    if (myid == 0) {
        fprintf(stderr, "Grid Size: %d x %d\n", dims[0], dims[1]);
    }

    xsize = XSIZE / dims[0];
    ysize = YSIZE / dims[1];

    if ((XSIZE % dims[0]) != 0 || (YSIZE % dims[1]) != 0) {
        if (myid == 0) fprintf(stderr, "Error: Grid cannot evenly divide region.\n");
        MPI_Abort(MPI_COMM_WORLD, 1);
    }

    /* === メモリ確保の変更 (MPI_Win_allocateの導入) === */
    /* u_data はローカル作業用なので通常の malloc で確保 */
    u_data = malloc((xsize + 2) * (ysize + 2) * sizeof(double));
    
    /* uu_data の確保とウィンドウ作成を MPIライブラリに一任する */
    MPI_Aint win_size = (MPI_Aint)((xsize + 2) * (ysize + 2) * sizeof(double));
    MPI_Win_allocate(win_size, sizeof(double), MPI_INFO_NULL, comm2d, (void *)&uu_data, &win);

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

    initialize();

    MPI_Barrier(comm2d);
    time1 = MPI_Wtime();

    lap_solve(comm2d);

    MPI_Barrier(comm2d);
    time2 = MPI_Wtime();

    if (myid == 0) {
        printf("time = %g\n", time2 - time1);
    }

    /* === メモリ解放の変更 === */
    /* ウィンドウを破棄する。このとき uu_data も自動的に解放される */
    MPI_Win_free(&win);
    
    free(u);
    free(uu);
    free(u_data);
    /* free(uu_data); <- MPI_Win_freeで解放済みのため削除 */

    MPI_Comm_free(&comm2d);

    MPI_Finalize();
    return (0);
}