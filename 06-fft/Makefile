SHELL := /usr/bin/env bash

CC ?= gcc
CXX ?= g++
CFLAGS ?= -O3 -std=c11 -Wall -Wextra -pedantic
CXXFLAGS ?= -O3 -std=c++17 -Wall -Wextra -pedantic
LDLIBS ?= -lm

BIN_DIR := bin
OUT_DIR := out
SCRIPT_DIR := scripts

TARGET := $(BIN_DIR)/fft_benchmark
TARGET_CPP := $(BIN_DIR)/fft_benchmark_cpp
CSV_OUT := $(OUT_DIR)/fft_benchmark.csv
PNG_OUT := $(OUT_DIR)/fft_benchmark.png

.PHONY: all build bench plot clean

all: build

build: | $(OUT_DIR)
build: $(TARGET) $(TARGET_CPP)

$(BIN_DIR):
	mkdir -p $@

$(OUT_DIR):
	mkdir -p $@

$(TARGET): fft_benchmark.c | $(BIN_DIR)
	$(CC) $(CFLAGS) $< -o $@ $(LDLIBS)

$(TARGET_CPP): fft_benchmark.cpp | $(BIN_DIR)
	$(CXX) $(CXXFLAGS) $< -o $@ $(LDLIBS)

bench: build | $(OUT_DIR)
	./$(TARGET_CPP) --size $${FFT_SIZE:-65536} > $(CSV_OUT)

plot: bench
	python3 $(SCRIPT_DIR)/plot_fft_benchmark.py $(CSV_OUT) $(PNG_OUT)

clean:
	rm -f $(TARGET) $(TARGET_CPP) $(CSV_OUT) $(PNG_OUT)