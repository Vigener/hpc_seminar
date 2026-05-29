SHELL := /usr/bin/env bash

CC ?= gcc
CFLAGS ?= -O3 -fopenmp -std=c11

BIN_DIR := bin
OUT_DIR := out
RESULT_DIR := results

BINS := \
	$(BIN_DIR)/matvec_serial \
	$(BIN_DIR)/matvec_parallel \
	$(BIN_DIR)/matvec_simd_reduction \
	$(BIN_DIR)/matvec_no_simd

.PHONY: all build bench plot clean

all: build

build: $(BINS)

$(BIN_DIR):
	mkdir -p $@

$(BIN_DIR)/matvec_serial: matvec_serial.c | $(BIN_DIR)
	$(CC) $(CFLAGS) $< -o $@

$(BIN_DIR)/matvec_parallel: matvec_parallel.c | $(BIN_DIR)
	$(CC) $(CFLAGS) $< -o $@

$(BIN_DIR)/matvec_simd_reduction: matvec_simd_reduction.c | $(BIN_DIR)
	$(CC) $(CFLAGS) $< -o $@

$(BIN_DIR)/matvec_no_simd: matvec_no_simd.c | $(BIN_DIR)
	$(CC) $(CFLAGS) $< -o $@

bench: build
	./scripts/run_matvec_bench.sh

plot: bench
	python3 scripts/plot_graph.py results/matvec_bench.csv out/matvec_bench.png

clean:
	rm -f $(BINS)
	rm -f $(OUT_DIR)/run.out
	rm -f $(RESULT_DIR)/matvec_bench.csv
	rm -f $(OUT_DIR)/matvec_bench.png