#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import japanize_matplotlib
import matplotlib.pyplot as plt

# フォントサイズの定数設定
FONT_SIZE_TITLE = 24
FONT_SIZE_AXIS_LABEL = 20
FONT_SIZE_TICKS = 14
FONT_SIZE_LEGEND = 12

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
        description="Create PPX time plots from a raw CSV and write a summary CSV."
    )
    parser.add_argument("--input", type=Path, required=True, help="Raw CSV path.")
    parser.add_argument("--summary-output", type=Path, required=True, help="Summary CSV output path.")
    parser.add_argument("--figure-output", type=Path, required=True, help="Main figure output path.")
    parser.add_argument(
        "--zoom-figure-output",
        type=Path,
        default=None,
        help="Zoomed figure output path. If omitted, '_zoom' is appended before the suffix.",
    )
    parser.add_argument(
        "--title",
        default="Laplace MPI: Mean execution time vs process count",
        help="Figure title.",
    )
    parser.add_argument("--show-error-bars", action="store_true", help="Show standard deviation error bars.")
    return parser.parse_args()


def load_rows(input_path: Path) -> list[dict[str, str]]:
    with input_path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


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
        nprocs_values = sorted(nprocs for (current_source, nprocs) in grouped.keys() if current_source == source)
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
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["source", "nprocs", "repeat_count", "mean_sec", "stdev_sec"])
        writer.writeheader()
        writer.writerows(rows)


def _group_summary_rows(summary_rows: list[dict[str, str]]) -> dict[str, list[tuple[int, float, float]]]:
    grouped: dict[str, list[tuple[int, float, float]]] = defaultdict(list)
    for row in summary_rows:
        grouped[row["source"]].append((int(row["nprocs"]), float(row["mean_sec"]), float(row["stdev_sec"])))
    for source in grouped:
        grouped[source].sort(key=lambda item: item[0])
    return grouped


def _zoom_upper_bound(summary_rows: list[dict[str, str]]) -> float:
    non_baseline = [float(row["mean_sec"]) for row in summary_rows if row["source"] != "laplace"]
    values = non_baseline if non_baseline else [float(row["mean_sec"]) for row in summary_rows]
    if not values:
        return 1.0
    return max(values) * 1.15


def plot(summary_rows: list[dict[str, str]], output_path: Path, title: str, show_error_bars: bool, zoom: bool = False) -> None:
    grouped = _group_summary_rows(summary_rows)
    x_values = sorted({int(row["nprocs"]) for row in summary_rows})
    if not x_values:
        raise SystemExit("No valid data found in CSV")

    fig, ax = plt.subplots(figsize=(10, 6))
    for source in METHOD_ORDER:
        series = grouped.get(source, [])
        if not series:
            continue
        xs = [item[0] for item in series]
        means = [item[1] for item in series]
        stdevs = [item[2] for item in series]
        color = METHOD_COLORS.get(source)
        label = METHOD_LABELS.get(source, source)
        if show_error_bars:
            ax.errorbar(xs, means, yerr=stdevs, marker="o", linewidth=2, markersize=6, capsize=4, color=color, label=label)
        else:
            ax.plot(xs, means, marker="o", linewidth=2, markersize=6, color=color, label=label)

        for x_value, y_value in zip(xs, means):
            ax.annotate(
                f"{y_value:.3f}s",
                xy=(x_value, y_value),
                xytext=(0, 6),
                textcoords="offset points",
                ha="center",
                fontsize=9,
                color=color,
            )

    ax.set_title(title + (" (zoom)" if zoom else ""), fontsize=FONT_SIZE_TITLE)
    ax.set_xlabel("MPI processes", fontsize=FONT_SIZE_AXIS_LABEL)
    ax.set_ylabel("Mean elapsed time [s]", fontsize=FONT_SIZE_AXIS_LABEL)
    ax.set_xticks(x_values)
    ax.tick_params(axis="both", labelsize=FONT_SIZE_TICKS)
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.legend(fontsize=FONT_SIZE_LEGEND)
    ax.set_xscale("log", base=2)
    ax.set_xlim(left=min(x_values) * 0.9, right=max(x_values) * 1.1)
    if zoom:
        ax.set_ylim(bottom=0, top=_zoom_upper_bound(summary_rows))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)


def default_zoom_path(figure_output: Path) -> Path:
    return figure_output.with_name(f"{figure_output.stem}_zoom{figure_output.suffix}")


def main() -> int:
    args = parse_args()
    rows = load_rows(args.input)
    summary_rows = aggregate(rows)
    write_summary(args.summary_output, summary_rows)
    plot(summary_rows, args.figure_output, args.title, args.show_error_bars, zoom=False)
    zoom_output = args.zoom_figure_output if args.zoom_figure_output is not None else default_zoom_path(args.figure_output)
    plot(summary_rows, zoom_output, args.title, args.show_error_bars, zoom=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())