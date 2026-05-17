.PHONY: all run clean

CXX := g++
CXXFLAGS := -O3 -fopenmp

all: run

solver: solver.cpp
	mkdir -p bin
	$(CXX) $(CXXFLAGS) solver.cpp -o bin/solver

run: solver
	./bin/solver

run-thrd: solver
	export OMP_NUM_THREADS=1; \
	./bin/solver; \
	export OMP_NUM_THREADS=2; \
	./bin/solver; \
	export OMP_NUM_THREADS=4; \
	./bin/solver; \
	export OMP_NUM_THREADS=8; \
	./bin/solver; \

clean:
	rm -f bin/solver out/residuals.csv
