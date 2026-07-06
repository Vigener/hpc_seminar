#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import japanize_matplotlib  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes
from matplotlib.figure import Figure

FONT_SIZE_TITLE = 20
FONT_SIZE_AXIS_LABEL = 16
FONT_SIZE_TICKS = 12
FONT_SIZE_LEGEND = 12

N = 2000
TOTAL_FLOP = 2.0 * (N**3)
GIGA = 1e9

MAIN_SOURCE_ORDER = [
    "matvec_original",
    "matvec_loopswap",
    "matvec_loopswap_padding",
    "matvec_loopswap_unroll",
    "matvec_dgemm",
]

MAIN_SOURCE_LABELS = {
    "matvec_original": "オリジナル",
    "matvec_loopswap": "ループ入れ替え",
    "matvec_loopswap_padding": "入れ替え＋パディング",
    "matvec_loopswap_unroll": "入れ替え＋アンロール",
    "matvec_dgemm": "DGEMM (BLAS)",
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
    "matvec_blocking_32_128_16",
    "matvec_blocking_32_96_32",
    "matvec_blocking_16_256_8",
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
    "matvec_loopswap_blocking_32_128_16",
    "matvec_loopswap_blocking_32_96_32",
    "matvec_loopswap_blocking_16_256_8",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MatVec PPX 実行結果から比較グラフを生成します。"
    )
    parser.add_argument("input_file", type=Path, help="入力CSVファイルのパス")
    parser.add_argument("out_dir", type=Path, help="出力先ディレクトリのパス")
    parser.add_argument(
        "--suffix",
        type=str,
        default="",
        help="出力ファイル名に付与するサフィックス（例: --suffix _mac → main_comparison_mac.png）",
    )
    return parser.parse_args()


def load_and_average_times(input_file: Path) -> dict[str, dict[str, float]]:
    raw_data: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    with input_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            opt_type = row["opt_type"]
            source = (
                row["source"]
                .replace("_n2000_ppx", "")
                .replace("_n2000_mac", "")
                .replace("_n2000", "")
            )
            raw_data[opt_type][source].append(float(row["time"]))

    avg_data: dict[str, dict[str, float]] = defaultdict(dict)
    for opt_type, sources in raw_data.items():
        for source, times in sources.items():
            avg_data[opt_type][source] = sum(times) / len(times)

    return avg_data


def save_dual_figures(fig: Figure, base_output_file: Path, timestamp: str) -> None:
    timestamp_dir = base_output_file.parent / timestamp
    timestamp_dir.mkdir(parents=True, exist_ok=True)

    timestamped_file = (
        timestamp_dir / f"{base_output_file.stem}{base_output_file.suffix}"
    )
    latest_file = base_output_file.with_name(
        f"{base_output_file.stem}_latest{base_output_file.suffix}"
    )

    fig.savefig(timestamped_file, dpi=200, bbox_inches="tight")
    fig.savefig(latest_file, dpi=200, bbox_inches="tight")


def plot_grouped_bar(
    ax: Axes,
    labels: list[str],
    generic_values: list[float],
    ppx_values: list[float],
    title: str,
    ylabel: str,
    generic_annotations: list[str] | None = None,
    ppx_annotations: list[str] | None = None,
    generic_label: str = "汎用 (-O3)",
    ppx_label: str = "AMD特化 (-march=znver2)",
    is_gflops: bool = False,
) -> None:
    x = np.arange(len(labels))
    width = 0.35

    has_generic = any(v > 0 for v in generic_values)
    has_ppx = any(v > 0 for v in ppx_values)

    bars1 = []
    bars2 = []

    if has_generic and has_ppx:
        bars1 = ax.bar(
            x - width / 2, generic_values, width, label=generic_label, color="#4c78a8"
        )
        bars2 = ax.bar(
            x + width / 2, ppx_values, width, label=ppx_label, color="#f58518"
        )
    elif has_generic:
        bars1 = ax.bar(
            x, generic_values, width * 2, label=generic_label, color="#4c78a8"
        )
    elif has_ppx:
        bars2 = ax.bar(x, ppx_values, width * 2, label=ppx_label, color="#f58518")

    ax.set_ylabel(ylabel, fontsize=FONT_SIZE_AXIS_LABEL)
    ax.set_title(title, fontsize=FONT_SIZE_TITLE, pad=18)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=FONT_SIZE_TICKS, rotation=15, ha="right")
    ax.tick_params(axis="y", labelsize=FONT_SIZE_TICKS)
    ax.set_ylim(bottom=0)
    ax.grid(True, axis="y", linestyle="--", alpha=0.35)
    if has_generic or has_ppx:
        ax.legend(fontsize=FONT_SIZE_LEGEND)

    def get_auto_annotation(val):
        if is_gflops:
            return _fmt_gflops(val)
        return _fmt_time(val)

    if bars1:
        for i, bar in enumerate(bars1):
            text = (
                generic_annotations[i]
                if generic_annotations
                else get_auto_annotation(generic_values[i])
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

    if bars2:
        for i, bar in enumerate(bars2):
            text = (
                ppx_annotations[i]
                if ppx_annotations
                else get_auto_annotation(ppx_values[i])
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


def _fmt_time(val: float) -> str:
    if val <= 0.0:
        return "0.00s"
    if val >= 0.01:
        return f"{val:.2f}s"
    n = abs(int(math.floor(math.log10(val))))
    return f"{val:.{n}f}s"


def _fmt_gflops(val: float) -> str:
    if val <= 0.0:
        return "0.0G"
    return f"{val:.1f}G"


def _filter_order(order: list[str], data: dict[str, float]) -> list[str]:
    return [s for s in order if s in data]


def _best_or_none(order: list[str], data: dict[str, float]) -> str | None:
    available = _filter_order(order, data)
    if not available:
        return None
    return min(available, key=lambda s: data[s])


def create_main_graph(
    avg_data: dict[str, dict[str, float]],
    output_file: Path,
    timestamp: str,
    is_gflops: bool = False,
) -> None:
    labels = []
    generic_vals = []
    ppx_vals = []
    generic_texts = []
    ppx_texts = []

    gen_data = avg_data.get("generic", {})
    ppx_data = avg_data.get("ppx_tuned", {})

    for source in MAIN_SOURCE_ORDER:
        g_time = gen_data.get(source)
        p_time = ppx_data.get(source)
        if g_time is None and p_time is None:
            continue
        labels.append(MAIN_SOURCE_LABELS[source])
        g_time = g_time or 0.0
        p_time = p_time or 0.0

        if is_gflops:
            g_val = (TOTAL_FLOP / g_time / GIGA) if g_time > 0 else 0.0
            p_val = (TOTAL_FLOP / p_time / GIGA) if p_time > 0 else 0.0
            generic_vals.append(g_val)
            ppx_vals.append(p_val)
            generic_texts.append(_fmt_gflops(g_val) if g_val > 0 else "N/A")
            ppx_texts.append(_fmt_gflops(p_val) if p_val > 0 else "N/A")
        else:
            generic_vals.append(g_time)
            ppx_vals.append(p_time)
            generic_texts.append(_fmt_time(g_time) if g_time > 0 else "N/A")
            ppx_texts.append(_fmt_time(p_time) if p_time > 0 else "N/A")

    best_g_block = _best_or_none(BLOCKING_ORDER, gen_data)
    best_p_block = _best_or_none(BLOCKING_ORDER, ppx_data)

    if best_g_block or best_p_block:
        labels.append(MAIN_SOURCE_LABELS["best_blocking"])
        g_time = gen_data.get(best_g_block, 0) if best_g_block else 0.0
        p_time = ppx_data.get(best_p_block, 0) if best_p_block else 0.0
        size_g_block = (
            best_g_block.replace("matvec_blocking_", "").replace("_", "x")
            if best_g_block
            else "-"
        )
        size_p_block = (
            best_p_block.replace("matvec_blocking_", "").replace("_", "x")
            if best_p_block
            else "-"
        )

        if is_gflops:
            g_val = (TOTAL_FLOP / g_time / GIGA) if g_time > 0 else 0.0
            p_val = (TOTAL_FLOP / p_time / GIGA) if p_time > 0 else 0.0
            generic_vals.append(g_val)
            ppx_vals.append(p_val)
            generic_texts.append(
                f"{_fmt_gflops(g_val)}\n({size_g_block})" if best_g_block else "N/A"
            )
            ppx_texts.append(
                f"{_fmt_gflops(p_val)}\n({size_p_block})" if best_p_block else "N/A"
            )
        else:
            generic_vals.append(g_time)
            ppx_vals.append(p_time)
            generic_texts.append(
                f"{_fmt_time(g_time)}\n({size_g_block})" if best_g_block else "N/A"
            )
            ppx_texts.append(
                f"{_fmt_time(p_time)}\n({size_p_block})" if best_p_block else "N/A"
            )

    best_g_hyb = _best_or_none(LOOPSWAP_BLOCKING_ORDER, gen_data)
    best_p_hyb = _best_or_none(LOOPSWAP_BLOCKING_ORDER, ppx_data)

    if best_g_hyb or best_p_hyb:
        labels.append(MAIN_SOURCE_LABELS["best_loopswap_blocking"])
        g_time = gen_data.get(best_g_hyb, 0) if best_g_hyb else 0.0
        p_time = ppx_data.get(best_p_hyb, 0) if best_p_hyb else 0.0
        size_g_hyb = (
            best_g_hyb.replace("matvec_loopswap_blocking_", "").replace("_", "x")
            if best_g_hyb
            else "-"
        )
        size_p_hyb = (
            best_p_hyb.replace("matvec_loopswap_blocking_", "").replace("_", "x")
            if best_p_hyb
            else "-"
        )

        if is_gflops:
            g_val = (TOTAL_FLOP / g_time / GIGA) if g_time > 0 else 0.0
            p_val = (TOTAL_FLOP / p_time / GIGA) if p_time > 0 else 0.0
            generic_vals.append(g_val)
            ppx_vals.append(p_val)
            generic_texts.append(
                f"{_fmt_gflops(g_val)}\n({size_g_hyb})" if best_g_hyb else "N/A"
            )
            ppx_texts.append(
                f"{_fmt_gflops(p_val)}\n({size_p_hyb})" if best_p_hyb else "N/A"
            )
        else:
            generic_vals.append(g_time)
            ppx_vals.append(p_time)
            generic_texts.append(
                f"{_fmt_time(g_time)}\n({size_g_hyb})" if best_g_hyb else "N/A"
            )
            ppx_texts.append(
                f"{_fmt_time(p_time)}\n({size_p_hyb})" if best_p_hyb else "N/A"
            )

    if not labels:
        print("  [skip] メイン比較グラフに描画可能なデータがありません")
        return

    gen_label = avg_data.get("_gen_label", "汎用 (-O3)")
    ppx_label = "AMD特化 (-march=znver2)"

    title = "全体比較: N=2000 での最適化手法別実行時間"
    ylabel = "実行時間 [sec]"
    if is_gflops:
        title = "全体比較: N=2000 での最適化手法別性能"
        ylabel = "性能 [GFLOPS]"

    fig, ax = plt.subplots(figsize=(14, 7))
    plot_grouped_bar(
        ax,
        labels,
        generic_vals,
        ppx_vals,
        title,
        ylabel,
        generic_texts,
        ppx_texts,
        generic_label=str(gen_label),
        ppx_label=ppx_label,
        is_gflops=is_gflops,
    )

    fig.tight_layout()
    save_dual_figures(fig, output_file, timestamp)
    plt.close(fig)


def create_detail_graph(
    avg_data: dict[str, dict[str, float]],
    order_list: list[str],
    title: str,
    output_file: Path,
    timestamp: str,
    is_gflops: bool = False,
) -> None:
    gen_data = avg_data.get("generic", {})
    ppx_data = avg_data.get("ppx_tuned", {})

    available = _filter_order(order_list, gen_data)
    ppx_available = _filter_order(order_list, ppx_data)
    all_available = list(dict.fromkeys(available + ppx_available))
    if not all_available:
        print(f"  [skip] データが一つもないため '{title}' のグラフをスキップします")
        return

    labels = [
        s.replace("matvec_loopswap_blocking_", "")
        .replace("matvec_blocking_", "")
        .replace("_", "x")
        for s in all_available
    ]

    if is_gflops:
        generic_vals = [
            (TOTAL_FLOP / gen_data.get(s, 0.0) / GIGA)
            if gen_data.get(s, 0.0) > 0
            else 0.0
            for s in all_available
        ]
        ppx_vals = [
            (TOTAL_FLOP / ppx_data.get(s, 0.0) / GIGA)
            if ppx_data.get(s, 0.0) > 0
            else 0.0
            for s in all_available
        ]
        y_label = "性能 [GFLOPS]"
        title = title.replace("実行時間", "性能")
    else:
        generic_vals = [gen_data.get(s, 0.0) for s in all_available]
        ppx_vals = [ppx_data.get(s, 0.0) for s in all_available]
        y_label = "実行時間 [sec]"

    fig, ax = plt.subplots(figsize=(14, 7))
    plot_grouped_bar(
        ax,
        labels,
        generic_vals,
        ppx_vals,
        title,
        y_label,
        is_gflops=is_gflops,
    )

    fig.tight_layout()
    save_dual_figures(fig, output_file, timestamp)
    plt.close(fig)


def print_markdown_tables(avg_data: dict[str, dict[str, float]]) -> None:
    print("\n" + "=" * 60)
    print("【テキストベース解析用データ（Markdown Table）】")
    print("=" * 60 + "\n")

    gen_data = avg_data.get("generic", {})
    ppx_data = avg_data.get("ppx_tuned", {})
    has_ppx = len(ppx_data) > 0
    gen_label = avg_data.get("_gen_label", "汎用 (-O3)")
    ppx_label = "AMD特化 (-march=znver2)"

    def get_gflops(t):
        return (TOTAL_FLOP / t / GIGA) if t and t > 0 else 0.0

    def fmt_cell(t):
        if t is None or t <= 0:
            return "-", "-"
        return f"{t:.6f}", f"{get_gflops(t):.2f}"

    print("### 1. 全体比較: N=2000 での最適化手法別実行時間・性能\n")
    if has_ppx:
        print(
            f"| 手法 | {gen_label} [sec] | {gen_label} [GFLOPS] | {ppx_label} [sec] | {ppx_label} [GFLOPS] |"
        )
        print("| :--- | :---: | :---: | :---: | :---: |")
    else:
        print(f"| 手法 | {gen_label} [sec] | {gen_label} [GFLOPS] |")
        print("| :--- | :---: | :---: |")

    for source in MAIN_SOURCE_ORDER:
        g_val = gen_data.get(source)
        p_val = ppx_data.get(source)
        if g_val is None and p_val is None:
            continue
        label = MAIN_SOURCE_LABELS[source].replace("\n", " ")
        g_str, g_gflops = fmt_cell(g_val)
        if has_ppx:
            p_str, p_gflops = fmt_cell(p_val)
            print(f"| {label} | {g_str} | {g_gflops} | {p_str} | {p_gflops} |")
        else:
            print(f"| {label} | {g_str} | {g_gflops} |")

    best_g_block = _best_or_none(BLOCKING_ORDER, gen_data)
    best_p_block = _best_or_none(BLOCKING_ORDER, ppx_data)
    if best_g_block or best_p_block:
        g_val = gen_data.get(best_g_block, 0) if best_g_block else 0
        p_val = ppx_data.get(best_p_block, 0) if best_p_block else 0
        g_str, g_gflops = fmt_cell(g_val)
        p_str, p_gflops = fmt_cell(p_val)
        g_size = (
            best_g_block.replace("matvec_blocking_", "").replace("_", "x")
            if best_g_block
            else ""
        )
        p_size = (
            best_p_block.replace("matvec_blocking_", "").replace("_", "x")
            if best_p_block
            else ""
        )
        g_disp = f"{g_str} ({g_size})" if best_g_block else "-"
        p_disp = f"{p_str} ({p_size})" if best_p_block else "-"
        g_gflops_disp = f"{g_gflops}" if best_g_block else "-"
        p_gflops_disp = f"{p_gflops}" if best_p_block else "-"

        if has_ppx:
            print(
                f"| ブロッキング単体 (最速値) | {g_disp} | {g_gflops_disp} | {p_disp} | {p_gflops_disp} |"
            )
        else:
            print(f"| ブロッキング単体 (最速値) | {g_disp} | {g_gflops_disp} |")

    best_g_hyb = _best_or_none(LOOPSWAP_BLOCKING_ORDER, gen_data)
    best_p_hyb = _best_or_none(LOOPSWAP_BLOCKING_ORDER, ppx_data)
    if best_g_hyb or best_p_hyb:
        g_val = gen_data.get(best_g_hyb, 0) if best_g_hyb else 0
        p_val = ppx_data.get(best_p_hyb, 0) if best_p_hyb else 0
        g_str, g_gflops = fmt_cell(g_val)
        p_str, p_gflops = fmt_cell(p_val)
        g_size = (
            best_g_hyb.replace("matvec_loopswap_blocking_", "").replace("_", "x")
            if best_g_hyb
            else ""
        )
        p_size = (
            best_p_hyb.replace("matvec_loopswap_blocking_", "").replace("_", "x")
            if best_p_hyb
            else ""
        )
        g_disp = f"{g_str} ({g_size})" if best_g_hyb else "-"
        p_disp = f"{p_str} ({p_size})" if best_p_hyb else "-"
        g_gflops_disp = f"{g_gflops}" if best_g_hyb else "-"
        p_gflops_disp = f"{p_gflops}" if best_p_hyb else "-"

        if has_ppx:
            print(
                f"| 入れ替え＋ブロック (最速値) | {g_disp} | {g_gflops_disp} | {p_disp} | {p_gflops_disp} |\n"
            )
        else:
            print(f"| 入れ替え＋ブロック (最速値) | {g_disp} | {g_gflops_disp} |\n")

    blocking_available = _filter_order(BLOCKING_ORDER, gen_data)
    blocking_p_available = _filter_order(BLOCKING_ORDER, ppx_data)
    blocking_all = list(dict.fromkeys(blocking_available + blocking_p_available))
    if blocking_all:
        print("### 2. ブロッキング単体: サイズ別実行時間・性能比較 (N=2000)\n")
        if has_ppx:
            print(
                f"| ブロックサイズ | {gen_label} [sec] | {gen_label} [GFLOPS] | {ppx_label} [sec] | {ppx_label} [GFLOPS] |"
            )
            print("| :--- | :---: | :---: | :---: | :---: |")
        else:
            print(f"| ブロックサイズ | {gen_label} [sec] | {gen_label} [GFLOPS] |")
            print("| :--- | :---: | :---: |")
        for s in blocking_all:
            label = s.replace("matvec_blocking_", "").replace("_", "x")
            g_str, g_gflops = fmt_cell(gen_data.get(s))
            if has_ppx:
                p_str, p_gflops = fmt_cell(ppx_data.get(s))
                print(f"| {label} | {g_str} | {g_gflops} | {p_str} | {p_gflops} |")
            else:
                print(f"| {label} | {g_str} | {g_gflops} |")
        print("\n")

    hyb_available = _filter_order(LOOPSWAP_BLOCKING_ORDER, gen_data)
    hyb_p_available = _filter_order(LOOPSWAP_BLOCKING_ORDER, ppx_data)
    hyb_all = list(dict.fromkeys(hyb_available + hyb_p_available))
    if hyb_all:
        print("### 3. 入れ替え＋ブロッキング: サイズ別実行時間・性能比較 (N=2000)\n")
        if has_ppx:
            print(
                f"| ブロックサイズ | {gen_label} [sec] | {gen_label} [GFLOPS] | {ppx_label} [sec] | {ppx_label} [GFLOPS] |"
            )
            print("| :--- | :---: | :---: | :---: | :---: |")
        else:
            print(f"| ブロックサイズ | {gen_label} [sec] | {gen_label} [GFLOPS] |")
            print("| :--- | :---: | :---: |")
        for s in hyb_all:
            label = s.replace("matvec_loopswap_blocking_", "").replace("_", "x")
            g_str, g_gflops = fmt_cell(gen_data.get(s))
            if has_ppx:
                p_str, p_gflops = fmt_cell(ppx_data.get(s))
                print(f"| {label} | {g_str} | {g_gflops} | {p_str} | {p_gflops} |")
            else:
                print(f"| {label} | {g_str} | {g_gflops} |")
    print("\n" + "=" * 60 + "\n")


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    avg_data = load_and_average_times(args.input_file)

    if "generic" not in avg_data and "ppx_tuned" not in avg_data:
        first_opt = next(iter(avg_data))
        print(f"  [info] 単一opt_type '{first_opt}' を 'generic' として扱います")
        avg_data = {
            "generic": avg_data[first_opt],
            "ppx_tuned": {},
            "_gen_label": first_opt,
        }
    else:
        avg_data.setdefault("generic", {})
        avg_data.setdefault("ppx_tuned", {})

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # --- 実行時間のグラフ (3種) ---
    create_main_graph(
        avg_data,
        args.out_dir / f"main_comparison{args.suffix}.png",
        timestamp,
        is_gflops=False,
    )
    create_detail_graph(
        avg_data,
        BLOCKING_ORDER,
        "ブロッキング単体: サイズ別実行時間比較 (N=2000)",
        args.out_dir / f"blocking_comparison{args.suffix}.png",
        timestamp,
        is_gflops=False,
    )
    create_detail_graph(
        avg_data,
        LOOPSWAP_BLOCKING_ORDER,
        "入れ替え＋ブロッキング: サイズ別実行時間比較 (N=2000)",
        args.out_dir / f"loopswap_blocking_comparison{args.suffix}.png",
        timestamp,
        is_gflops=False,
    )

    # --- 性能(GFLOPS)のグラフ (3種) ---
    create_main_graph(
        avg_data,
        args.out_dir / f"main_comparison{args.suffix}_gflops.png",
        timestamp,
        is_gflops=True,
    )
    create_detail_graph(
        avg_data,
        BLOCKING_ORDER,
        "ブロッキング単体: サイズ別性能比較 (N=2000)",
        args.out_dir / f"blocking_comparison{args.suffix}_gflops.png",
        timestamp,
        is_gflops=True,
    )
    create_detail_graph(
        avg_data,
        LOOPSWAP_BLOCKING_ORDER,
        "入れ替え＋ブロッキング: サイズ別性能比較 (N=2000)",
        args.out_dir / f"loopswap_blocking_comparison{args.suffix}_gflops.png",
        timestamp,
        is_gflops=True,
    )

    print_markdown_tables(avg_data)

    print(
        f"生成されたグラフは\n"
        f"  {args.out_dir / f'main_comparison{args.suffix}_latest.png'} と \n"
        f"  {args.out_dir / f'blocking_comparison{args.suffix}_latest.png'} と \n"
        f"  {args.out_dir / f'loopswap_blocking_comparison{args.suffix}_latest.png'} \n"
        f"  （およびそれぞれの _gflops_latest.png）\n"
        f"として保存されています。\n"
        f"（※履歴は {args.out_dir / timestamp}/ 内にも保存されました）\n"
    )


if __name__ == "__main__":
    main()
