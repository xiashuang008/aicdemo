from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from plot_peer_comparison import PROJECT_ROOT, load_data


def build_table(rows) -> str:
    lines = (
        r"\begin{tabular}{l c r r r r r}",
        r"\toprule",
        r"公司 & 财年截止日 & 营收 & 营收同比 & 毛利率 & 经营利润率 & 净利率 \\",
        r"\midrule",
    )
    body = [
        f'{row["name"]} & {row["fiscal_year_end"]} & {row["revenue_bn"]:.1f} & '
        f'{row["growth"]:.1f}\\% & {row["gross_margin"]:.1f}\\% & '
        f'{row["operating_margin"]:.1f}\\% & {row["net_margin"]:.1f}\\% \\\\'
        for row in rows
    ]
    ending = (r"\bottomrule", r"\end{tabular}")
    return "\n".join((*lines, *body, *ending)) + "\n"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="从 comparison.json 生成仅含 tabular 的五家公司 LaTeX 对比表。")
    parser.add_argument("--input", type=Path, default=PROJECT_ROOT / "comparison.json", help="财务数据 JSON 路径。")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "output" / "tables" / "peer_comparison.tex", help="输出 TeX 路径。")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    rows, _, _ = load_data(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(build_table(rows), encoding="utf-8")
    print(f"Saved: {args.output.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
