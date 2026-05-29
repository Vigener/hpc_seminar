# /// script
# requires-python = ">=3.12"
# ///
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import japanize_matplotlib
import matplotlib.pyplot as plt


FONT_SIZE_TITLE = 24
FONT_SIZE_AXIS_LABEL = 20
FONT_SIZE_TICKS = 14
FONT_SIZE_LEGEND = 12

THREAD_ORDER = [1, 2, 4]

# Preferred ordering for display (will be filtered by CSV contents)
PREFERRED_MODE_ORDER = ["serial", "parallel", "simd_reduction", "no_simd"]

MODE_DISPLAY = {
    "serial": "Serial",
    "parallel": "Parallel",
    "simd_reduction": "SIMD Reduction",
    "no_simd": "No SIMD",
}

SIZE_PALETTE = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd", "#8c564b"]

MODE_STYLE = {
    "serial": {"marker": "o", "linestyle": "-"},
    "parallel": {"marker": "s", "linestyle": "--"},
    "simd_reduction": {"marker": "^", "linestyle": ":"},
    "no_simd": {"marker": "D", "linestyle": "-."},
}


def parse_results(input_path: Path) -> tuple[dict[str, dict[int, dict[int, float]]], list[int], list[str]]:
    data: dict[str, dict[int, dict[int, float]]] = {}
    sizes: set[int] = set()
    modes_seen: set[str] = set()

    with input_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required_fields = {"size", "mode", "threads", "time_sec"}
        if set(reader.fieldnames or ()) != required_fields:
            raise ValueError(f"CSV の列が不正です: {reader.fieldnames}")

        for row in reader:
            size = int(row["size"])
            mode = row["mode"]
            threads = int(row["threads"])
            time_ms = float(row["time_sec"]) * 1000.0

            sizes.add(size)
            modes_seen.add(mode)
            data.setdefault(mode, {}).setdefault(size, {})
            data[mode][size][threads] = time_ms

    # Determine mode order by preferred ordering then any extras (stable)
    mode_order = [m for m in PREFERRED_MODE_ORDER if m in modes_seen]
    for m in sorted(modes_seen):
        if m not in mode_order:
            mode_order.append(m)

    return data, sorted(sizes), mode_order


def validate_data(data: dict[str, dict[int, dict[int, float]]], sizes: list[int], mode_order: list[str]) -> None:
    for mode in mode_order:
        for size in sizes:
            series = data.get(mode, {}).get(size, {})
            missing_threads = [t for t in THREAD_ORDER if t not in series]
            if missing_threads:
                raise ValueError(f"size={size} の {mode} データが不足しています: {missing_threads}")


def plot_graph(data: dict[str, dict[int, dict[int, float]]], sizes: list[int], mode_order: list[str], output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(13, 8))

    size_styles = {size: {"color": SIZE_PALETTE[index % len(SIZE_PALETTE)]} for index, size in enumerate(sizes)}

    for size in sizes:
        for mode in mode_order:
            series = data[mode][size]
            x_values = THREAD_ORDER
            y_values = [series[thread_count] for thread_count in x_values]
            size_style = size_styles[size]
            mode_style = MODE_STYLE[mode]
            label_display = f"M=N={size} ({MODE_DISPLAY.get(mode, mode)})"

            ax.plot(
                x_values,
                y_values,
                marker=mode_style["marker"],
                color=size_style["color"],
                linestyle=mode_style["linestyle"],
                linewidth=2,
                markersize=8,
                label=label_display,
            )

            for thread_count, time_ms in zip(x_values, y_values):
                ax.annotate(
                    f"{time_ms:.1f} ms",
                    xy=(thread_count, time_ms),
                    xytext=(0, 8),
                    textcoords="offset points",
                    ha="center",
                    fontsize=FONT_SIZE_TICKS - 1,
                    color=size_style["color"],
                )

    ax.set_xlabel("スレッド数", fontsize=FONT_SIZE_AXIS_LABEL)
    ax.set_ylabel("実行時間 [ms]", fontsize=FONT_SIZE_AXIS_LABEL)
    ax.set_title("OpenMP 行列ベクトル積の実行時間比較\n（4 実装 + 2 サイズ）", fontsize=FONT_SIZE_TITLE)
    ax.set_xticks(THREAD_ORDER)
    ax.tick_params(axis="x", labelsize=FONT_SIZE_TICKS)
    ax.tick_params(axis="y", labelsize=FONT_SIZE_TICKS)
    ax.set_ylim(bottom=0)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(fontsize=FONT_SIZE_LEGEND, ncol=2)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format=output_path.suffix.lstrip("."), bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OpenMP の実行時間を CSV から読み取り、4 実装と 2 サイズを比較するグラフを描画します。"
    )
    parser.add_argument("input_file", type=Path, help="results/matvec_bench.csv")
    parser.add_argument("output_path", type=Path, help="出力先の画像または PDF ファイル")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data, sizes, mode_order = parse_results(args.input_file)
    validate_data(data, sizes, mode_order)
    plot_graph(data, sizes, mode_order, args.output_path)


if __name__ == "__main__":
    main()