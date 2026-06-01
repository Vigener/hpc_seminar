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
    "laplace": "laplace",
    "laplace_basic1": "laplace_basic1",
    "laplace_basic2": "laplace_basic2",
    "laplace_advanced": "laplace_advanced",
}
METHOD_COLORS = {
    "laplace": "#444444",
    "laplace_basic1": "#1f77b4",
    "laplace_basic2": "#ff7f0e",
    "laplace_advanced": "#2ca02c",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create 4-line plots (x=nprocs, y=mean time) from PPX raw CSV."
    )
    parser.add_argument("--input", type=Path, required=True, help="Raw CSV path (copied into out/).")
    parser.add_argument("--summary-output", type=Path, required=True, help="Summary CSV output path.")
    parser.add_argument("--figure-output", type=Path, required=True, help="Figure output path.")
    parser.add_argument(
        "--zoom-figure-output",
        type=Path,
        default=None,
        help="Zoomed figure output path. If omitted, '_zoom' is appended to figure-output.",
    )
    parser.add_argument("--title", default="Laplace MPI: Mean time vs process count", help="Figure title.")
    parser.add_argument("--show-error-bars", action="store_true", help="Show standard deviation error bars.")
    return parser.parse_args()


def load_rows(input_path: Path) -> list[dict[str, str]]:
    with input_path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def aggregate(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[tuple[str, int], list[float]] = defaultdict(list)
    for row in rows:
        if row.get("status", "").lower() != "ok":
            continue
        source = row["source"]
        nprocs = int(row["nprocs"])
        elapsed = float(row["elapsed_sec"])
        grouped[(source, nprocs)].append(elapsed)

    summary_rows: list[dict[str, str]] = []
    for source in METHOD_ORDER:
        nprocs_values = sorted({np for (s, np) in grouped.keys() if s == source})
        for nprocs in nprocs_values:
            samples = grouped[(source, nprocs)]
            mean_sec = statistics.mean(samples)
            stdev_sec = statistics.stdev(samples) if len(samples) >= 2 else 0.0
            summary_rows.append(
                {
                    "source": source,
                    "nprocs": str(nprocs),
                    "repeat_count": str(len(samples)),
                    "mean_sec": f"{mean_sec:.9f}",
                    "stdev_sec": f"{stdev_sec:.9f}",
                }
            )
    return summary_rows


def write_summary(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["source", "nprocs", "repeat_count", "mean_sec", "stdev_sec"],
        )
        writer.writeheader()
        writer.writerows(rows)


def plot(
    summary_rows: list[dict[str, str]],
    output_path: Path,
    title: str,
    show_error_bars: bool,
    x_max: int | None = None,
    subtitle: str | None = None,
    figsize: tuple[float, float] = (9, 5.5),
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    by_source: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in summary_rows:
        by_source[row["source"]].append(row)

    plt.figure(figsize=figsize)

    for source in METHOD_ORDER:
        rows = by_source.get(source, [])
        if not rows:
            continue
        rows.sort(key=lambda r: int(r["nprocs"]))
        xs = [int(r["nprocs"]) for r in rows]
        ys = [float(r["mean_sec"]) for r in rows]
        es = [float(r["stdev_sec"]) for r in rows]

        if x_max is not None:
            filtered = [(x, y, e) for x, y, e in zip(xs, ys, es) if x <= x_max]
            if not filtered:
                continue
            xs = [item[0] for item in filtered]
            ys = [item[1] for item in filtered]
            es = [item[2] for item in filtered]

        if show_error_bars:
            plt.errorbar(
                xs,
                ys,
                yerr=es,
                marker="o",
                linewidth=2,
                capsize=4,
                label=METHOD_LABELS[source],
                color=METHOD_COLORS[source],
            )
        else:
            plt.plot(
                xs,
                ys,
                marker="o",
                linewidth=2,
                label=METHOD_LABELS[source],
                color=METHOD_COLORS[source],
            )

    plt.title(title)
    plt.xlabel("Process count")
    plt.ylabel("Mean time [s]")
    if subtitle:
        plt.suptitle(subtitle, y=0.98, fontsize=11)
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.legend()
    if x_max is not None:
        plt.xlim(left=0.5, right=x_max + 0.25)
        plt.xticks([x for x in [1, 2, 4, 8, 16, 32, 64, 112] if x <= x_max])
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def main() -> int:
    args = parse_args()
    rows = load_rows(args.input)
    summary_rows = aggregate(rows)
    if not summary_rows:
        raise SystemExit("No valid rows found (status=ok).")
    write_summary(args.summary_output, summary_rows)

    zoom_output = args.zoom_figure_output
    if zoom_output is None:
        zoom_output = args.figure_output.with_name(f"{args.figure_output.stem}_zoom{args.figure_output.suffix}")

    plot(summary_rows, args.figure_output, args.title, args.show_error_bars)
    plot(
        summary_rows,
        zoom_output,
        args.title,
        args.show_error_bars,
        x_max=16,
        subtitle="Zoomed view: process counts up to 16",
        figsize=(11.3, 8.5),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
