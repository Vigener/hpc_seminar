.PHONY: build release debug run run-basic clean

CC := mpicc
CFLAGS_BASE := -Wall
CFLAGS_DEBUG := $(CFLAGS_BASE) -g -O0
CFLAGS_RELEASE := $(CFLAGS_BASE) -O3

# プロセス数（デフォルト: 4）
NPROCS ?= 4

# --- ビルドターゲット ---

build: laplace laplace_basic1

release: CFLAGS := $(CFLAGS_RELEASE)
release: laplace laplace_basic1

debug: CFLAGS := $(CFLAGS_DEBUG)
debug: laplace laplace_basic1

laplace: laplace.c
	$(CC) $(CFLAGS) -o laplace laplace.c -lm

laplace_basic1: laplace_basic1.c
	$(CC) $(CFLAGS) -o laplace_basic1 laplace_basic1.c -lm

# --- 実行ターゲット（コンパイル済みで実行） ---
# Mac環境での OpenMPI 互換性フラグを使用

MPIRUN_ENV := PRTE_LAUNCHER=local

run: release
	$(MPIRUN_ENV) mpirun -np $(NPROCS) ./laplace

run-basic: release
	$(MPIRUN_ENV) mpirun -np $(NPROCS) ./laplace_basic1

# --- クリーン ---

clean:
	rm -f laplace laplace_basic1
