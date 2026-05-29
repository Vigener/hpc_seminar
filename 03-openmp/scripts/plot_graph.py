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

SERIAL_SOURCE = "matvec_serial"
PARALLEL_SOURCE = "matvec_simd_reduction"

SERIAL_LABEL = "並列化なし"
PARALLEL_LABEL = "並列化あり"

SERIAL_STYLE = {"marker": "o", "linestyle": "-", "color": "#1f77b4"}
PARALLEL_STYLE = {"marker": "s", "linestyle": "--", "color": "#d62728"}


def parse_results(input_path: Path) -> dict[str, dict[int, float]]:
    data: dict[str, dict[int, float]] = {}

    with input_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required_fields = {"source", "threads", "repeat_index", "elapsed_sec"}
        if set(reader.fieldnames or ()) != required_fields:
            raise ValueError(f"CSV の列が不正です: {reader.fieldnames}")

        for row in reader:
            source = row["source"]
            threads = int(row["threads"])
            elapsed_ms = float(row["elapsed_sec"]) * 1000.0

            data.setdefault(source, {})[threads] = elapsed_ms

    return data


def validate_data(data: dict[str, dict[int, float]]) -> None:
    missing_sources = [source for source in (SERIAL_SOURCE, PARALLEL_SOURCE) if source not in data]
    if missing_sources:
        raise ValueError(f"CSV に必要な source がありません: {missing_sources}")

    missing_nodes = {
        source: [thread_count for thread_count in THREAD_ORDER if thread_count not in data.get(source, {})]
        for source in (SERIAL_SOURCE, PARALLEL_SOURCE)
    }
    missing_nodes = {source: nodes for source, nodes in missing_nodes.items() if nodes}
    if missing_nodes:
        raise ValueError(f"データが不足しています: {missing_nodes}")


def plot_graph(data: dict[str, dict[int, float]], output_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(13, 8))

    serial_y = [data[SERIAL_SOURCE][thread_count] for thread_count in THREAD_ORDER]
    parallel_y = [data[PARALLEL_SOURCE][thread_count] for thread_count in THREAD_ORDER]

    ax.plot(
        THREAD_ORDER,
        serial_y,
        marker=SERIAL_STYLE["marker"],
        linestyle=SERIAL_STYLE["linestyle"],
        color=SERIAL_STYLE["color"],
        linewidth=2.5,
        markersize=8,
        label=SERIAL_LABEL,
    )
    ax.plot(
        THREAD_ORDER,
        parallel_y,
        marker=PARALLEL_STYLE["marker"],
        linestyle=PARALLEL_STYLE["linestyle"],
        color=PARALLEL_STYLE["color"],
        linewidth=2.5,
        markersize=8,
        label=PARALLEL_LABEL,
    )

    for thread_count, time_ms in zip(THREAD_ORDER, serial_y, strict=True):
        ax.annotate(
            f"{time_ms:.1f} ms",
            xy=(thread_count, time_ms),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            fontsize=FONT_SIZE_TICKS - 1,
            color=SERIAL_STYLE["color"],
        )

    for thread_count, time_ms in zip(THREAD_ORDER, parallel_y, strict=True):
        ax.annotate(
            f"{time_ms:.1f} ms",
            xy=(thread_count, time_ms),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            fontsize=FONT_SIZE_TICKS - 1,
            color=PARALLEL_STYLE["color"],
        )

    ax.set_xlabel("スレッド数", fontsize=FONT_SIZE_AXIS_LABEL)
    ax.set_ylabel("実行時間 [ms]", fontsize=FONT_SIZE_AXIS_LABEL)
    ax.set_title("OpenMP 行列ベクトル積の実行時間比較\n（並列化なし / 並列化あり）", fontsize=FONT_SIZE_TITLE)
    ax.set_xticks(THREAD_ORDER)
    ax.tick_params(axis="x", labelsize=FONT_SIZE_TICKS)
    ax.tick_params(axis="y", labelsize=FONT_SIZE_TICKS)
    ax.set_ylim(bottom=0)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(fontsize=FONT_SIZE_LEGEND)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, format=output_path.suffix.lstrip("."), bbox_inches="tight")
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="OpenMP の実行時間を CSV から読み取り、並列化なしと並列化ありを比較するグラフを描画します。"
    )
    parser.add_argument("input_file", type=Path, help="out/matvec_ppx_*.csv")
    parser.add_argument("output_path", type=Path, help="出力先の画像または PDF ファイル")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    data = parse_results(args.input_file)
    validate_data(data)
    plot_graph(data, args.output_path)


if __name__ == "__main__":
    main()