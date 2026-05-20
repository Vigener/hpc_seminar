#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

METHOD_ORDER = ["laplace", "laplace_basic1", "laplace_basic2", "laplace_advanced"]
METHOD_LABELS = {
    "laplace": "laplace (baseline)",
    "laplace_basic1": "basic1",
    "laplace_basic2": "basic2",
    "laplace_advanced": "advanced",
}
METHOD_COLORS = {
    "laplace": "#444444",
    "laplace_basic1": "#1f77b4",
    "laplace_basic2": "#ff7f0e",
    "laplace_advanced": "#2ca02c",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plot absolute execution time for Laplace benchmark CSV.")
    parser.add_argument("input_csv", type=Path, help="CSV produced by benchmark_laplace.py")
    parser.add_argument("output_path", type=Path, help="Output image path (PNG/PDF)")
    parser.add_argument("--show-error-bars", action="store_true", help="Show stdev error bars if available")
    return parser.parse_args()


def load_rows(input_csv: Path) -> list[dict[str, str]]:
    with input_csv.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def group_times(rows: list[dict[str, str]]):
    grouped = defaultdict(lambda: defaultdict(list))  # grouped[nprocs][(source,size)] -> list of mean_sec
    for r in rows:
        source = r["source"]
        size = int(r["size"])
        nprocs = int(r["nprocs"])
        mean_sec = float(r["mean_sec"]) if r.get("mean_sec") else None
        stdev = float(r.get("stdev_sec", 0.0)) if r.get("stdev_sec") else 0.0
        grouped[nprocs][(source, size)].append((mean_sec, stdev))
    return grouped


def summarize_series(items: list[tuple[float, float]]):
    means = [m for m, s in items]
    stdevs = [s for m, s in items]
    mean_value = statistics.mean(means)
    stdev_value = statistics.mean(stdevs) if len(stdevs) > 0 else 0.0
    return mean_value, stdev_value


def plot_time(grouped, output_path: Path, show_error_bars: bool):
    nprocs_list = sorted(grouped.keys())
    if not nprocs_list:
        raise SystemExit("No data found in CSV")

    fig, axes = plt.subplots(nrows=len(nprocs_list), ncols=1, figsize=(10, 4 * len(nprocs_list)), sharex=True)
    if len(nprocs_list) == 1:
        axes = [axes]

    for ax, nprocs in zip(axes, nprocs_list):
        series_by_method = defaultdict(lambda: defaultdict(list))
        # collect sizes
        sizes = set()
        for (source, size), items in grouped[nprocs].items():
            sizes.add(size)
            series_by_method[source][size] = items
        sizes = sorted(sizes)

        for source in METHOD_ORDER:
            y_means = []
            y_errs = []
            x_vals = []
            for size in sizes:
                items = series_by_method.get(source, {}).get(size)
                if not items:
                    continue
                mean_value, stdev_value = summarize_series(items)
                x_vals.append(size)
                y_means.append(mean_value)
                y_errs.append(stdev_value)

            if not x_vals:
                continue

            color = METHOD_COLORS.get(source, None)
            label = METHOD_LABELS.get(source, source)
            if show_error_bars:
                ax.errorbar(x_vals, y_means, yerr=y_errs, marker="o", label=label, color=color, capsize=4)
            else:
                ax.plot(x_vals, y_means, marker="o", label=label, color=color)

            for xv, yv in zip(x_vals, y_means):
                ax.annotate(f"{yv:.3f}s", xy=(xv, yv), xytext=(0, 6), textcoords="offset points", ha="center", fontsize=8)

        ax.set_xscale("log", base=2)
        ax.set_xlabel("Grid size N")
        ax.set_ylabel("Execution Time [s]")
        ax.set_title(f"Execution time (MPI processes: {nprocs})")
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend()

    fig.suptitle("Laplace: Absolute execution time by method and grid size", fontsize=14)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    args = parse_args()
    rows = load_rows(args.input_csv)
    grouped = group_times(rows)
    plot_time(grouped, args.output_path, args.show_error_bars)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
