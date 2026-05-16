.PHONY: build release debug run run-basic clean

CC := mpicc
CFLAGS_BASE := -Wall
CFLAGS_DEBUG := $(CFLAGS_BASE) -g -O0
CFLAGS_RELEASE := $(CFLAGS_BASE) -O3

# プロセス数（デフォルト: 4）
NPROCS ?= 4

# --- ビルドターゲット ---

build: laplace laplace_basic1 laplace_basic2 laplace_advanced

release: CFLAGS := $(CFLAGS_RELEASE)
release: laplace laplace_basic1 laplace_basic2 laplace_advanced

debug: CFLAGS := $(CFLAGS_DEBUG)
debug: laplace laplace_basic1

laplace: laplace.c
	@$(CC) $(CFLAGS) -o bin/laplace laplace.c -lm

laplace_basic1: laplace_basic1.c
	@$(CC) $(CFLAGS) -o bin/laplace_basic1 laplace_basic1.c -lm

laplace_basic2: laplace_basic2.c
	@$(CC) $(CFLAGS) -o bin/laplace_basic2 laplace_basic2.c -lm

laplace_advanced: laplace_advanced.c
	@$(CC) $(CFLAGS) -o bin/laplace_advanced laplace_advanced.c -lm

# --- 実行ターゲット（コンパイル済みで実行） ---
# Mac環境での OpenMPI 互換性フラグを使用

MPIRUN_ENV := PRTE_LAUNCHER=local

run: release
	@echo "=> mpirun -np $(NPROCS) ./bin/laplace"
	@$(MPIRUN_ENV) mpirun -np $(NPROCS) ./bin/laplace

run-basic: release
	@echo "=> mpirun -np $(NPROCS) ./bin/laplace_basic1"
	@$(MPIRUN_ENV) mpirun -np $(NPROCS) ./bin/laplace_basic1

run-basic2: release
	@echo "=> mpirun -np $(NPROCS) ./bin/laplace_basic2"
	@$(MPIRUN_ENV) mpirun -np $(NPROCS) ./bin/laplace_basic2

run-advanced: release
	@echo "=> mpirun -np $(NPROCS) ./bin/laplace_advanced"
	@$(MPIRUN_ENV) mpirun -np $(NPROCS) ./bin/laplace_advanced

# パターンルール: make run-4, make run-8 などで実行可能に
run-%: release
	@echo "=> mpirun -np $* ./bin/laplace"
	@$(MPIRUN_ENV) mpirun -np $* ./bin/laplace

run-basic-%: release
	@echo "=> mpirun -np $* ./bin/laplace_basic1"
	@$(MPIRUN_ENV) mpirun -np $* ./bin/laplace_basic1

run-basic2-%: release
	@echo "=> mpirun -np $* ./bin/laplace_basic2"
	@$(MPIRUN_ENV) mpirun -np $* ./bin/laplace_basic2

run-advanced-%: release
	@echo "=> mpirun -np $* ./bin/laplace_advanced"
	@$(MPIRUN_ENV) mpirun -np $* ./bin/laplace_advanced

# --- クリーン ---

clean:
	rm -f bin/laplace bin/laplace_basic1 bin/laplace_basic2 bin/laplace_advanced