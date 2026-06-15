#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from datetime import datetime  # タイムスタンプ取得用に追加
from pathlib import Path

import japanize_matplotlib  # noqa: F401
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes  # 型ヒントのために正しくインポート
from matplotlib.figure import Figure

FONT_SIZE_TITLE = 20
FONT_SIZE_AXIS_LABEL = 16
FONT_SIZE_TICKS = 12
FONT_SIZE_LEGEND = 12

MAIN_SOURCE_ORDER = [
    "matvec_original",
    "matvec_loopswap",
    "matvec_loopswap_padding",
    "matvec_loopswap_unroll",
    "matvec_dgemm",  # ★ここに追加
]

MAIN_SOURCE_LABELS = {
    "matvec_original": "オリジナル",
    "matvec_loopswap": "ループ入れ替え",
    "matvec_loopswap_padding": "入れ替え＋パディング",
    "matvec_loopswap_unroll": "入れ替え＋アンロール",
    "matvec_dgemm": "DGEMM (BLAS)",  # ★ここに追加
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
    "matvec_blocking_32_128_16",  # ★ここに追加
    "matvec_blocking_32_96_32",  # ★ここに追加
    "matvec_blocking_16_256_8",  # ★ここに追加
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
    "matvec_loopswap_blocking_32_128_16",  # ★ここに追加
    "matvec_loopswap_blocking_32_96_32",  # ★ここに追加
    "matvec_loopswap_blocking_16_256_8",  # ★ここに追加
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="MatVec PPX 実行結果から比較グラフを3種生成します。"
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
    # raw_data[opt_type][base_source] = [time1, time2, ...]
    raw_data: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))

    with input_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            opt_type = row["opt_type"]
            # "_n2000" や "_ppx", "_mac" などのサフィックスを除去してベースのソース名を取得
            source = (
                row["source"]
                .replace("_n2000_ppx", "")
                .replace("_n2000_mac", "")
                .replace("_n2000", "")
            )
            raw_data[opt_type][source].append(float(row["time"]))

    # 平均値の計算
    avg_data: dict[str, dict[str, float]] = defaultdict(dict)
    for opt_type, sources in raw_data.items():
        for source, times in sources.items():
            avg_data[opt_type][source] = sum(times) / len(times)

    return avg_data


def save_dual_figures(fig: Figure, base_output_file: Path, timestamp: str) -> None:
    """タイムスタンプ専用フォルダとlatest版の2か所に画像を保存する"""
    # タイムスタンプ用のサブディレクトリを作成（例: out/20260607_143000/）
    timestamp_dir = base_output_file.parent / timestamp
    timestamp_dir.mkdir(parents=True, exist_ok=True)

    # 履歴用ファイルパス（例: out/20260607_143000/main_comparison.png）
    timestamped_file = (
        timestamp_dir / f"{base_output_file.stem}{base_output_file.suffix}"
    )

    # latest用ファイルパス（例: out/main_comparison_latest.png）
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
) -> None:
    x = np.arange(len(labels))
    width = 0.35

    has_generic = any(v > 0 for v in generic_values)
    has_ppx = any(v > 0 for v in ppx_values)

    bars1 = []
    bars2 = []

    if has_generic and has_ppx:
        # 両方ある → 通常のグループ棒グラフ
        bars1 = ax.bar(
            x - width / 2, generic_values, width, label=generic_label, color="#4c78a8"
        )
        bars2 = ax.bar(
            x + width / 2, ppx_values, width, label=ppx_label, color="#f58518"
        )
    elif has_generic:
        # generic のみ → 単一バー
        bars1 = ax.bar(
            x, generic_values, width * 2, label=generic_label, color="#4c78a8"
        )
    elif has_ppx:
        # ppx のみ → 単一バー
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

    # アノテーション（値や補足テキスト）の追加
    if bars1:
        for i, bar in enumerate(bars1):
            text = (
                generic_annotations[i]
                if generic_annotations
                else _fmt_time(generic_values[i])
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
            text = ppx_annotations[i] if ppx_annotations else _fmt_time(ppx_values[i])
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
    """0.01s以下は最初の非ゼロ桁まで表示、それ以外は小数点以下2桁"""
    if val <= 0.0:
        return "0.00s"
    if val >= 0.01:
        return f"{val:.2f}s"
    n = abs(int(math.floor(math.log10(val))))
    return f"{val:.{n}f}s"


def _filter_order(order: list[str], data: dict[str, float]) -> list[str]:
    """ORDERリストを、実際にデータが存在するsourceだけに絞り込む"""
    return [s for s in order if s in data]


def _best_or_none(order: list[str], data: dict[str, float]) -> str | None:
    """データがあるsourceの中から最速のものを返す。一つもなければNone"""
    available = _filter_order(order, data)
    if not available:
        return None
    return min(available, key=lambda s: data[s])


def create_main_graph(
    avg_data: dict[str, dict[str, float]], output_file: Path, timestamp: str
) -> None:
    labels = []
    generic_vals = []
    ppx_vals = []
    generic_texts = []
    ppx_texts = []

    gen_data = avg_data.get("generic", {})
    ppx_data = avg_data.get("ppx_tuned", {})

    # 1. 基本手法のデータ収集（CSVに存在するものだけ）
    for source in MAIN_SOURCE_ORDER:
        # どちらのopt_typeにもデータがなければスキップ
        g_val = gen_data.get(source)
        p_val = ppx_data.get(source)
        if g_val is None and p_val is None:
            continue
        labels.append(MAIN_SOURCE_LABELS[source])
        g_val = g_val or 0.0
        p_val = p_val or 0.0
        generic_vals.append(g_val)
        ppx_vals.append(p_val)
        generic_texts.append(_fmt_time(g_val) if g_val else "N/A")
        ppx_texts.append(_fmt_time(p_val) if p_val else "N/A")

    # 2. ブロッキング単体の最速値を探す
    best_g_block = _best_or_none(BLOCKING_ORDER, gen_data)
    best_p_block = _best_or_none(BLOCKING_ORDER, ppx_data)

    if best_g_block or best_p_block:
        labels.append(MAIN_SOURCE_LABELS["best_blocking"])
        g_val = gen_data.get(best_g_block, 0) if best_g_block else 0.0
        p_val = ppx_data.get(best_p_block, 0) if best_p_block else 0.0
        generic_vals.append(g_val)
        ppx_vals.append(p_val)
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
        generic_texts.append(
            f"{_fmt_time(g_val)}\n({size_g_block})" if best_g_block else "N/A"
        )
        ppx_texts.append(f"{_fmt_time(p_val)}\n({size_p_block})" if best_p_block else "N/A")

    # 3. 入れ替え＋ブロック（ハイブリッド版）の最速値を探す
    best_g_hyb = _best_or_none(LOOPSWAP_BLOCKING_ORDER, gen_data)
    best_p_hyb = _best_or_none(LOOPSWAP_BLOCKING_ORDER, ppx_data)

    if best_g_hyb or best_p_hyb:
        labels.append(MAIN_SOURCE_LABELS["best_loopswap_blocking"])
        g_val = gen_data.get(best_g_hyb, 0) if best_g_hyb else 0.0
        p_val = ppx_data.get(best_p_hyb, 0) if best_p_hyb else 0.0
        generic_vals.append(g_val)
        ppx_vals.append(p_val)
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
        generic_texts.append(f"{_fmt_time(g_val)}\n({size_g_hyb})" if best_g_hyb else "N/A")
        ppx_texts.append(f"{_fmt_time(p_val)}\n({size_p_hyb})" if best_p_hyb else "N/A")

    if not labels:
        print("  [skip] メイン比較グラフに描画可能なデータがありません")
        return

    # opt_type に応じて凡例ラベルを切り替え
    gen_label = avg_data.get("_gen_label", "汎用 (-O3)")
    ppx_label = "AMD特化 (-march=znver2)"

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
        generic_label=gen_label,
        ppx_label=ppx_label,
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
) -> None:
    gen_data = avg_data.get("generic", {})
    ppx_data = avg_data.get("ppx_tuned", {})

    # CSVに存在するsourceだけに絞り込む
    available = _filter_order(order_list, gen_data)
    # ppx側にもあるものをmerge（片方だけにあるケースも拾う）
    ppx_available = _filter_order(order_list, ppx_data)
    all_available = list(dict.fromkeys(available + ppx_available))
    if not all_available:
        print(f"  [skip] データが一つもないため '{title}' のグラフをスキップします")
        return

    # matvec_blocking_ / matvec_loopswap_blocking_ プレフィックスを消して 40x8x8 形式に
    labels = [
        s.replace("matvec_loopswap_blocking_", "")
        .replace("matvec_blocking_", "")
        .replace("_", "x")
        for s in all_available
    ]
    generic_vals = [gen_data.get(s, 0.0) for s in all_available]
    ppx_vals = [ppx_data.get(s, 0.0) for s in all_available]

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
    save_dual_figures(fig, output_file, timestamp)
    plt.close(fig)


def print_markdown_tables(avg_data: dict[str, dict[str, float]]) -> None:
    """分析用のMarkdownテーブルを標準出力にプリントする"""
    print("\n" + "=" * 60)
    print("【テキストベース解析用データ（Markdown Table）】")
    print("=" * 60 + "\n")

    gen_data = avg_data.get("generic", {})
    ppx_data = avg_data.get("ppx_tuned", {})
    has_ppx = len(ppx_data) > 0
    gen_label = f"{avg_data.get('_gen_label', '汎用 (-O3)')} [sec]"
    ppx_label = "AMD特化 (-march=znver2) [sec]"

    # 1. 全体比較
    print("### 1. 全体比較: N=2000 での最適化手法別実行時間\n")
    if has_ppx:
        print(f"| 手法 | {gen_label} | {ppx_label} |")
        print("| :--- | :---: | :---: |")
    else:
        print(f"| 手法 | {gen_label} |")
        print("| :--- | :---: |")

    for source in MAIN_SOURCE_ORDER:
        g_val = gen_data.get(source)
        p_val = ppx_data.get(source)
        if g_val is None and p_val is None:
            continue  # データが無い手法はスキップ
        label = MAIN_SOURCE_LABELS[source].replace("\n", " ")
        g_str = f"{g_val:.6f}" if g_val is not None else "-"
        if has_ppx:
            p_str = f"{p_val:.6f}" if p_val is not None else "-"
            print(f"| {label} | {g_str} | {p_str} |")
        else:
            print(f"| {label} | {g_str} |")

    best_g_block = _best_or_none(BLOCKING_ORDER, gen_data)
    best_p_block = _best_or_none(BLOCKING_ORDER, ppx_data)
    if best_g_block or best_p_block:
        g_str = (
            f"{gen_data.get(best_g_block, 0):.6f} ({best_g_block.replace('matvec_blocking_', '').replace('_', 'x')})"
            if best_g_block
            else "-"
        )
        p_str = (
            f"{ppx_data.get(best_p_block, 0):.6f} ({best_p_block.replace('matvec_blocking_', '').replace('_', 'x')})"
            if best_p_block
            else "-"
        )
        if has_ppx:
            print(f"| ブロッキング単体 (最速値) | {g_str} | {p_str} |")
        else:
            print(f"| ブロッキング単体 (最速値) | {g_str} |")

    best_g_hyb = _best_or_none(LOOPSWAP_BLOCKING_ORDER, gen_data)
    best_p_hyb = _best_or_none(LOOPSWAP_BLOCKING_ORDER, ppx_data)
    if best_g_hyb or best_p_hyb:
        g_str = (
            f"{gen_data.get(best_g_hyb, 0):.6f} ({best_g_hyb.replace('matvec_loopswap_blocking_', '').replace('_', 'x')})"
            if best_g_hyb
            else "-"
        )
        p_str = (
            f"{ppx_data.get(best_p_hyb, 0):.6f} ({best_p_hyb.replace('matvec_loopswap_blocking_', '').replace('_', 'x')})"
            if best_p_hyb
            else "-"
        )
        if has_ppx:
            print(f"| 入れ替え＋ブロック (最速値) | {g_str} | {p_str} |\n")
        else:
            print(f"| 入れ替え＋ブロック (最速値) | {g_str} |\n")

    # 2. ブロッキング単体詳細
    blocking_available = _filter_order(BLOCKING_ORDER, gen_data)
    blocking_p_available = _filter_order(BLOCKING_ORDER, ppx_data)
    blocking_all = list(dict.fromkeys(blocking_available + blocking_p_available))
    if blocking_all:
        print("### 2. ブロッキング単体: サイズ別実行時間比較 (N=2000)\n")
        if has_ppx:
            print(f"| ブロックサイズ | {gen_label} | {ppx_label} |")
            print("| :--- | :---: | :---: |")
        else:
            print(f"| ブロックサイズ | {gen_label} |")
            print("| :--- | :---: |")
        for s in blocking_all:
            label = s.replace("matvec_blocking_", "").replace("_", "x")
            g_val = gen_data.get(s)
            p_val = ppx_data.get(s)
            g_str = f"{g_val:.6f}" if g_val is not None else "-"
            if has_ppx:
                p_str = f"{p_val:.6f}" if p_val is not None else "-"
                print(f"| {label} | {g_str} | {p_str} |")
            else:
                print(f"| {label} | {g_str} |")
        print("\n")

    # 3. 入れ替え＋ブロッキング詳細
    hyb_available = _filter_order(LOOPSWAP_BLOCKING_ORDER, gen_data)
    hyb_p_available = _filter_order(LOOPSWAP_BLOCKING_ORDER, ppx_data)
    hyb_all = list(dict.fromkeys(hyb_available + hyb_p_available))
    if hyb_all:
        print("### 3. 入れ替え＋ブロッキング: サイズ別実行時間比較 (N=2000)\n")
        if has_ppx:
            print(f"| ブロックサイズ | {gen_label} | {ppx_label} |")
            print("| :--- | :---: | :---: |")
        else:
            print(f"| ブロックサイズ | {gen_label} |")
            print("| :--- | :---: |")
        for s in hyb_all:
            label = s.replace("matvec_loopswap_blocking_", "").replace("_", "x")
            g_val = gen_data.get(s)
            p_val = ppx_data.get(s)
            g_str = f"{g_val:.6f}" if g_val is not None else "-"
            if has_ppx:
                p_str = f"{p_val:.6f}" if p_val is not None else "-"
                print(f"| {label} | {g_str} | {p_str} |")
            else:
                print(f"| {label} | {g_str} |")
    print("\n" + "=" * 60 + "\n")


def main() -> None:
    args = parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)

    avg_data = load_and_average_times(args.input_file)

    # opt_type を正規化: どのCSVでも "generic" と "ppx_tuned" キーが存在するようにする
    # - PPXのCSV → generic, ppx_tuned がそのまま使われる
    # - MacのCSV → mac_native を generic にマッピング、ppx_tuned は空
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

    # 実行時のタイムスタンプを取得
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 3つのグラフを生成
    create_main_graph(
        avg_data, args.out_dir / f"main_comparison{args.suffix}.png", timestamp
    )
    create_detail_graph(
        avg_data,
        BLOCKING_ORDER,
        "ブロッキング単体: サイズ別実行時間比較 (N=2000)",
        args.out_dir / f"blocking_comparison{args.suffix}.png",
        timestamp,
    )
    create_detail_graph(
        avg_data,
        LOOPSWAP_BLOCKING_ORDER,
        "入れ替え＋ブロッキング: サイズ別実行時間比較 (N=2000)",
        args.out_dir / f"loopswap_blocking_comparison{args.suffix}.png",
        timestamp,
    )

    # Markdownテーブルの出力
    print_markdown_tables(avg_data)

    print(
        f"生成されたグラフは\n"
        f"  {args.out_dir / f'main_comparison{args.suffix}_latest.png'} と \n"
        f"  {args.out_dir / f'blocking_comparison{args.suffix}_latest.png'} と \n"
        f"  {args.out_dir / f'loopswap_blocking_comparison{args.suffix}_latest.png'} \n"
        f"として保存されています。\n"
        f"（※履歴は {args.out_dir / timestamp}/ 内にも保存されました）\n"
    )


if __name__ == "__main__":
    main()
