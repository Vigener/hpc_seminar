.PHONY: all run clean

CXX := g++
CXXFLAGS := -O3 -fopenmp

all: run

solver: solver.cpp
	mkdir -p bin
	$(CXX) $(CXXFLAGS) solver.cpp -o bin/solver

run: solver
	./bin/solver

clean:
	rm -f bin/solver out/residuals.csv
