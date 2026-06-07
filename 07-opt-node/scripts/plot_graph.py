#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import japanize_matplotlib  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes  # 型ヒントのために正しくインポート

FONT_SIZE_TITLE = 20
FONT_SIZE_AXIS_LABEL = 16
FONT_SIZE_TICKS = 12
FONT_SIZE_LEGEND = 12

MAIN_SOURCE_ORDER = [
    "matvec_original",
    "matvec_loopswap",
    "matvec_loopswap_padding",
    "matvec_loopswap_unroll",
]

MAIN_SOURCE_LABELS = {
    "matvec_original": "オリジナル",
    "matvec_loopswap": "ループ入れ替え",
    "matvec_loopswap_padding": "入れ替え＋パディング",
    "matvec_loopswap_unroll": "入れ替え＋アンロール",
    "best_blocking": "ブロッキング単体\n(最速値)",
    "best_loopswap_blocking": "入れ替え＋ブロック\n(最速値)",
}

BLOCKING_ORDER = [
    "matvec_blocking_1_8_8",
    "matvec_blocking_4_4_4",
    "matvec_blocking_8_8_8",
    "matvec_blocking_16_16_16",
    "matvec_blocking_32_32_32",
    "matvec_blocking_48_48_48",
    "matvec_blocking_64_64_64",
    "matvec_blocking_128_128_128",
    "matvec_blocking_40_8_8",
    "matvec_blocking_8_8_40",
]

LOOPSWAP_BLOCKING_ORDER = [
    "matvec_loopswap_blocking_1_8_8",
    "matvec_loopswap_blocking_4_4_4",
    "matvec_loopswap_blocking_8_8_8",
    "matvec_loopswap_blocking_16_16_16",
    "matvec_loopswap_blocking_32_32_32",
    "matvec_loopswap_blocking_48_48_48",
    "matvec_loopswap_blocking_64_64_64",
    "matvec_loopswap_blocking_128_128_128",
    "matvec_loopswap_blocking_40_8_8",
    "matvec_loopswap_blocking_8_8_40",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MatVec PPX 実行結果から比較グラフを3種生成します。"
    )
    parser.add_argument("input_file", type=Path, help="入力CSVファイルのパス")
    parser.add_argument("out_dir", type=Path, help="出力先ディレクトリのパス")
    return parser.parse_args()


def load_and_average_times(input_file: Path) -> dict[str, dict[str, float]]:
    # raw_data[opt_type][base_source] = [time1, time2, ...]
    raw_data: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    with input_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            opt_type = row["opt_type"]
            # "_n2000" や "_ppx" などのサフィックスを除去してベースのソース名を取得
            source = row["source"].replace("_n2000_ppx", "").replace("_n2000", "")
            raw_data[opt_type][source].append(float(row["time"]))

    # 平均値の計算
    avg_data: dict[str, dict[str, float]] = defaultdict(dict)
    for opt_type, sources in raw_data.items():
        for source, times in sources.items():
            avg_data[opt_type][source] = sum(times) / len(times)

    return avg_data


def plot_grouped_bar(
    ax: Axes,
    labels: list[str],
    generic_values: list[float],
    ppx_values: list[float],
    title: str,
    ylabel: str,
    generic_annotations: list[str] | None = None,
    ppx_annotations: list[str] | None = None,
) -> None:
    x = np.arange(len(labels))
    width = 0.35

    bars1 = ax.bar(
        x - width / 2, generic_values, width, label="汎用 (-O3)", color="#4c78a8"
    )
    bars2 = ax.bar(
        x + width / 2,
        ppx_values,
        width,
        label="AMD特化 (-march=znver2)",
        color="#f58518",
    )

    ax.set_ylabel(ylabel, fontsize=FONT_SIZE_AXIS_LABEL)
    ax.set_title(title, fontsize=FONT_SIZE_TITLE, pad=18)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=FONT_SIZE_TICKS, rotation=15, ha="right")
    ax.tick_params(axis="y", labelsize=FONT_SIZE_TICKS)
    ax.set_ylim(bottom=0)
    ax.grid(True, axis="y", linestyle="--", alpha=0.35)
    ax.legend(fontsize=FONT_SIZE_LEGEND)

    # アノテーション（値や補足テキスト）の追加
    for i, bar in enumerate(bars1):
        text = (
            generic_annotations[i]
            if generic_annotations
            else f"{generic_values[i]:.2f}s"
        )
        ax.annotate(
            text,
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    for i, bar in enumerate(bars2):
        text = ppx_annotations[i] if ppx_annotations else f"{ppx_values[i]:.2f}s"
        ax.annotate(
            text,
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
        )


def create_main_graph(avg_data: dict[str, dict[str, float]], output_file: Path) -> None:
    labels = []
    generic_vals = []
    ppx_vals = []
    generic_texts = []
    ppx_texts = []

    # 1. 基本手法のデータ収集
    for source in MAIN_SOURCE_ORDER:
        labels.append(MAIN_SOURCE_LABELS[source])
        g_val = avg_data["generic"].get(source, 0)
        p_val = avg_data["ppx_tuned"].get(source, 0)
        generic_vals.append(g_val)
        ppx_vals.append(p_val)
        generic_texts.append(f"{g_val:.2f}s")
        ppx_texts.append(f"{p_val:.2f}s")

    # 2. ブロッキング単体の最速値を探す
    best_g_block = min(
        BLOCKING_ORDER, key=lambda s: avg_data["generic"].get(s, float("inf"))
    )
    best_p_block = min(
        BLOCKING_ORDER, key=lambda s: avg_data["ppx_tuned"].get(s, float("inf"))
    )

    labels.append(MAIN_SOURCE_LABELS["best_blocking"])
    generic_vals.append(avg_data["generic"].get(best_g_block, 0))
    ppx_vals.append(avg_data["ppx_tuned"].get(best_p_block, 0))

    size_g_block = best_g_block.replace("matvec_blocking_", "").replace("_", "x")
    size_p_block = best_p_block.replace("matvec_blocking_", "").replace("_", "x")
    generic_texts.append(
        f"{avg_data['generic'].get(best_g_block, 0):.2f}s\n({size_g_block})"
    )
    ppx_texts.append(
        f"{avg_data['ppx_tuned'].get(best_p_block, 0):.2f}s\n({size_p_block})"
    )

    # 3. 入れ替え＋ブロック（ハイブリッド版）の最速値を探す
    best_g_hyb = min(
        LOOPSWAP_BLOCKING_ORDER, key=lambda s: avg_data["generic"].get(s, float("inf"))
    )
    best_p_hyb = min(
        LOOPSWAP_BLOCKING_ORDER,
        key=lambda s: avg_data["ppx_tuned"].get(s, float("inf")),
    )

    labels.append(MAIN_SOURCE_LABELS["best_loopswap_blocking"])
    generic_vals.append(avg_data["generic"].get(best_g_hyb, 0))
    ppx_vals.append(avg_data["ppx_tuned"].get(best_p_hyb, 0))

    size_g_hyb = best_g_hyb.replace("matvec_loopswap_blocking_", "").replace("_", "x")
    size_p_hyb = best_p_hyb.replace("matvec_loopswap_blocking_", "").replace("_", "x")
    generic_texts.append(
        f"{avg_data['generic'].get(best_g_hyb, 0):.2f}s\n({size_g_hyb})"
    )
    ppx_texts.append(f"{avg_data['ppx_tuned'].get(best_p_hyb, 0):.2f}s\n({size_p_hyb})")

    fig, ax = plt.subplots(figsize=(14, 7))
    plot_grouped_bar(
        ax,
        labels,
        generic_vals,
        ppx_vals,
        "全体比較: N=2000 での最適化手法別実行時間",
        "実行時間 [sec]",
        generic_texts,
        ppx_texts,
    )

    fig.tight_layout()
    fig.savefig(output_file, dpi=200, bbox_inches="tight")
    plt.close(fig)


def create_detail_graph(
    avg_data: dict[str, dict[str, float]],
    order_list: list[str],
    title: str,
    output_file: Path,
) -> None:
    # matvec_blocking_ もしくは matvec_loopswap_blocking_ のプレフィックスを消して 40x8x8 のように整形
    labels = [
        s.replace("matvec_loopswap_blocking_", "")
        .replace("matvec_blocking_", "")
        .replace("_", "x")
        for s in order_list
    ]
    generic_vals = [avg_data["generic"].get(s, 0) for s in order_list]
    ppx_vals = [avg_data["ppx_tuned"].get(s, 0) for s in order_list]

    fig, ax = plt.subplots(figsize=(14, 7))
    plot_grouped_bar(
        ax,
        labels,
        generic_vals,
        ppx_vals,
        title,
        "実行時間 [sec]",
    )

    fig.tight_layout()
    fig.savefig(output_file, dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    avg_data = load_and_average_times(args.input_file)

    # 3つのグラフを生成
    create_main_graph(avg_data, args.out_dir / "main_comparison.png")
    create_detail_graph(
        avg_data,
        BLOCKING_ORDER,
        "ブロッキング単体: サイズ別実行時間比較 (N=2000)",
        args.out_dir / "blocking_comparison.png",
    )
    create_detail_graph(
        avg_data,
        LOOPSWAP_BLOCKING_ORDER,
        "入れ替え＋ブロッキング: サイズ別実行時間比較 (N=2000)",
        args.out_dir / "loopswap_blocking_comparison.png",
    )

    print(f"グラフを {args.out_dir} に出力しました。")


if __name__ == "__main__":
    main()
