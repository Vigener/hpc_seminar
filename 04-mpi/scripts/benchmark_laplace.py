#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import statistics
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from shutil import which

METHOD_ORDER = ["laplace", "laplace_basic1", "laplace_basic2", "laplace_advanced"]
TIME_RE = re.compile(r"^time\s*=\s*([0-9.eE+-]+)\s*$")


@dataclass(frozen=True)
class TimingSummary:
    samples: list[float]

    @property
    def mean(self) -> float:
        return statistics.mean(self.samples)

    @property
    def stdev(self) -> float:
        if len(self.samples) < 2:
            return 0.0
        return statistics.stdev(self.samples)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Laplace benchmark runner that compiles size-specific binaries and writes a summary CSV."
    )
    parser.add_argument(
        "--sources",
        nargs="*",
        default=["laplace.c", "laplace_basic1.c", "laplace_basic2.c", "laplace_advanced.c"],
        help="C source files to benchmark relative to the script directory.",
    )
    parser.add_argument(
        "--sizes",
        nargs="+",
        type=int,
        required=True,
        help="Square grid sizes N to compile and benchmark (XSIZE=YSIZE=N).",
    )
    parser.add_argument(
        "--processes",
        nargs="+",
        type=int,
        required=True,
        help="MPI process counts to run for each compiled binary.",
    )
    parser.add_argument(
        "--repeats",
        type=int,
        default=3,
        help="Number of measurement repeats for each method/configuration.",
    )
    parser.add_argument(
        "--niter",
        type=int,
        default=10000,
        help="Iteration count compiled into each binary.",
    )
    parser.add_argument(
        "--mpicc",
        default="mpicc",
        help="MPI C compiler command.",
    )
    parser.add_argument(
        "--mpirun",
        default="mpirun",
        help="MPI launcher command.",
    )
    parser.add_argument(
        "--build-dir",
        type=Path,
        default=Path("build/laplace-bench"),
        help="Directory used to store compiled benchmark binaries.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="CSV output path.",
    )
    return parser.parse_args()


def require_command(command: str) -> None:
    if which(command) is None:
        raise SystemExit(f"Required command not found: {command}")


def compile_binary(mpicc: str, source: Path, output: Path, size: int, niter: int) -> None:
    command = [
        mpicc,
        str(source),
        f"-DXSIZE={size}",
        f"-DYSIZE={size}",
        f"-DNITER={niter}",
        "-O3",
        "-Wall",
        "-lm",
        "-o",
        str(output),
    ]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(
            "Compilation failed for %s\nSTDOUT:\n%s\nSTDERR:\n%s"
            % (source.name, completed.stdout, completed.stderr)
        )


def extract_elapsed(stdout: str) -> float:
    for raw_line in stdout.splitlines():
        match = TIME_RE.match(raw_line.strip())
        if match:
            return float(match.group(1))
    raise RuntimeError(f"Could not find 'time =' line in program output:\n{stdout}")


def run_binary(mpirun: str, binary: Path, nprocs: int) -> float:
    command = [mpirun, "-np", str(nprocs), str(binary)]
    completed = subprocess.run(command, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError(
            "Execution failed for %s with %d processes\nSTDOUT:\n%s\nSTDERR:\n%s"
            % (binary.name, nprocs, completed.stdout, completed.stderr)
        )
    return extract_elapsed(completed.stdout)


def method_key(path: Path) -> str:
    return path.stem


def main() -> int:
    args = parse_args()
    require_command(args.mpicc)
    require_command(args.mpirun)

    script_dir = Path(__file__).resolve().parent
    source_dir = script_dir.parent
    build_dir = args.build_dir if args.build_dir.is_absolute() else (source_dir / args.build_dir)
    build_dir.mkdir(parents=True, exist_ok=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    methods = [Path(source) for source in args.sources]
    missing_sources = [str(source) for source in methods if not (source_dir / source).exists()]
    if missing_sources:
        raise SystemExit(f"Missing source files: {', '.join(missing_sources)}")

    compiled_binaries: dict[tuple[str, int], Path] = {}
    for size in args.sizes:
        for source in methods:
            binary_path = build_dir / f"{source.stem}_n{size}_i{args.niter}"
            compile_binary(args.mpicc, source_dir / source, binary_path, size, args.niter)
            compiled_binaries[(source.stem, size)] = binary_path

    raw_samples: dict[tuple[str, int, int], list[float]] = defaultdict(list)
    for size in args.sizes:
        for nprocs in args.processes:
            for repeat_index in range(1, args.repeats + 1):
                for source in methods:
                    binary_path = compiled_binaries[(source.stem, size)]
                    elapsed = run_binary(args.mpirun, binary_path, nprocs)
                    raw_samples[(source.stem, size, nprocs)].append(elapsed)
                    print(
                        f"size={size} procs={nprocs} repeat={repeat_index} method={source.stem} time={elapsed:.6f}s",
                        file=sys.stderr,
                    )

    summaries: dict[tuple[str, int, int], TimingSummary] = {
        key: TimingSummary(samples=value) for key, value in raw_samples.items()
    }

    baseline_lookup = {
        (size, nprocs): summaries[("laplace", size, nprocs)].mean
        for size in args.sizes
        for nprocs in args.processes
    }

    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "source",
                "size",
                "nprocs",
                "niter",
                "repeat_count",
                "mean_sec",
                "stdev_sec",
                "speedup_vs_laplace",
            ],
        )
        writer.writeheader()
        for size in args.sizes:
            for nprocs in args.processes:
                baseline_mean = baseline_lookup[(size, nprocs)]
                for source in methods:
                    summary = summaries[(source.stem, size, nprocs)]
                    writer.writerow(
                        {
                            "source": source.stem,
                            "size": size,
                            "nprocs": nprocs,
                            "niter": args.niter,
                            "repeat_count": len(summary.samples),
                            "mean_sec": f"{summary.mean:.9f}",
                            "stdev_sec": f"{summary.stdev:.9f}",
                            "speedup_vs_laplace": f"{baseline_mean / summary.mean:.9f}",
                        }
                    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
