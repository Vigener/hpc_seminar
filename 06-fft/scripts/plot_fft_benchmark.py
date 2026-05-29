#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ALGORITHM_ORDER = ["dft", "fft"]
ALGORITHM_LABELS = {
    "dft": "DFT",
    "fft": "FFT",
}
ALGORITHM_COLORS = {
    "dft": "#c0392b",
    "fft": "#2980b9",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read a DFT/FFT benchmark CSV and create a comparison plot."
    )
    parser.add_argument("input_file", type=Path, help="CSV output path from the benchmark job.")
    parser.add_argument("output_file", type=Path, help="PNG output path.")
    return parser.parse_args()


def load_rows(input_file: Path) -> list[dict[str, str]]:
    with input_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        expected_fields = {"algorithm", "n", "elapsed_sec", "max_abs_error"}
        if set(reader.fieldnames or ()) != expected_fields:
            raise ValueError(f"Unexpected CSV header: {reader.fieldnames}")
        return list(reader)


def parse_elapsed(rows: list[dict[str, str]]) -> tuple[int, dict[str, float], dict[str, float]]:
    n_value: int | None = None
    elapsed_by_algorithm: dict[str, float] = {}
    error_by_algorithm: dict[str, float] = {}

    for row in rows:
        algorithm = row["algorithm"]
        if algorithm not in ALGORITHM_ORDER:
            continue

        current_n = int(row["n"])
        elapsed = float(row["elapsed_sec"])
        error = float(row["max_abs_error"])

        if n_value is None:
            n_value = current_n
        elif n_value != current_n:
            raise ValueError("CSV contains mixed n values")

        elapsed_by_algorithm[algorithm] = elapsed
        error_by_algorithm[algorithm] = error

    missing = [algorithm for algorithm in ALGORITHM_ORDER if algorithm not in elapsed_by_algorithm]
    if missing:
        raise ValueError(f"Missing algorithms in CSV: {missing}")

    if n_value is None:
        raise ValueError("CSV is empty")

    return n_value, elapsed_by_algorithm, error_by_algorithm


def plot(output_file: Path, n_value: int, elapsed_by_algorithm: dict[str, float], error_by_algorithm: dict[str, float]) -> None:
    algorithms = ALGORITHM_ORDER
    labels = [ALGORITHM_LABELS[algorithm] for algorithm in algorithms]
    times = [elapsed_by_algorithm[algorithm] for algorithm in algorithms]

    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.bar(labels, times, color=[ALGORITHM_COLORS[algorithm] for algorithm in algorithms], width=0.55)
    ax.set_yscale("log")
    ax.set_ylabel("Execution time [sec] (log scale)")
    ax.set_title(f"DFT vs FFT benchmark at N={n_value}")
    ax.grid(True, axis="y", linestyle="--", alpha=0.35)

    for bar, algorithm, elapsed in zip(bars, algorithms, times, strict=True):
        ax.annotate(
            f"{elapsed:.3e} s\nerr={error_by_algorithm[algorithm]:.2e}",
            xy=(bar.get_x() + bar.get_width() / 2.0, elapsed),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    output_file.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_file, dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    rows = load_rows(args.input_file)
    n_value, elapsed_by_algorithm, error_by_algorithm = parse_elapsed(rows)
    plot(args.output_file, n_value, elapsed_by_algorithm, error_by_algorithm)


if __name__ == "__main__":
    main()