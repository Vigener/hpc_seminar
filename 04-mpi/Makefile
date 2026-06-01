.PHONY: build build-ppx benchmark-ppx release debug run run-basic clean

PYTHON ?= python3
BENCHMARK_SIZES ?= 128 256 512 1024
BENCHMARK_PROCS ?= 1 2 4
BENCHMARK_REPEATS ?= 3
BENCHMARK_NITER ?= 1000
BENCHMARK_DIR ?= results
BENCHMARK_CSV ?= $(BENCHMARK_DIR)/laplace_benchmark.csv
BENCHMARK_PLOT ?= $(BENCHMARK_DIR)/laplace_speedup.png

CC := mpicc
CFLAGS_BASE := -Wall
CFLAGS_DEBUG := $(CFLAGS_BASE) -g -O0
CFLAGS_RELEASE := $(CFLAGS_BASE) -O3

# PPX で 112 プロセスまで回すため、既定のビルドサイズは 896 にする。
PPX_XSIZE ?= 896
PPX_NITER ?= 1000
PPX_DEFINE_FLAGS := -DXSIZE=$(PPX_XSIZE) -DYSIZE=$(PPX_XSIZE) -DNITER=$(PPX_NITER)

# プロセス数（デフォルト: 4）
NPROCS ?= 4

# --- ビルドターゲット ---

build: laplace laplace_basic1 laplace_basic2 laplace_advanced

# PPX 用の実行バイナリは通常の build で揃う。
build-ppx: build

release: CFLAGS := $(CFLAGS_RELEASE)
release: laplace laplace_basic1 laplace_basic2 laplace_advanced

debug: CFLAGS := $(CFLAGS_DEBUG)
debug: laplace laplace_basic1

laplace: laplace.c
	@$(CC) $(CFLAGS) $(PPX_DEFINE_FLAGS) -o bin/laplace laplace.c -lm

laplace_basic1: laplace_basic1.c
	@$(CC) $(CFLAGS) $(PPX_DEFINE_FLAGS) -o bin/laplace_basic1 laplace_basic1.c -lm

laplace_basic2: laplace_basic2.c
	@$(CC) $(CFLAGS) $(PPX_DEFINE_FLAGS) -o bin/laplace_basic2 laplace_basic2.c -lm

laplace_advanced: laplace_advanced.c
	@$(CC) $(CFLAGS) $(PPX_DEFINE_FLAGS) -o bin/laplace_advanced laplace_advanced.c -lm

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

benchmark: release
	@mkdir -p $(BENCHMARK_DIR)
	@$(PYTHON) scripts/benchmark_laplace.py \
		--sizes $(BENCHMARK_SIZES) \
		--processes $(BENCHMARK_PROCS) \
		--repeats $(BENCHMARK_REPEATS) \
		--niter $(BENCHMARK_NITER) \
		--output $(BENCHMARK_CSV)

plot-benchmark:
	@$(PYTHON) scripts/plot_laplace_speedup.py $(BENCHMARK_CSV) $(BENCHMARK_PLOT)

# PPX 実行用のジョブを投入する。
benchmark-ppx:
	@sbatch run.sh