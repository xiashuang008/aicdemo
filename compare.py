from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any, Sequence

from companyfacts import (
    CompanyAnnuals,
    CompanyFactsError,
    SecCompanyFactsClient,
    company_facts_url,
    extract_company_annuals,
)

COMPANIES = (
    ("苹果", "0000320193"),
    ("微软", "0000789019"),
    ("Alphabet", "0001652044"),
    ("亚马逊", "0001018724"),
    ("Meta", "0001326801"),
    ("英伟达", "0001045810"),
)


def build_result(annuals: CompanyAnnuals, display_name: str) -> dict[str, Any]:
    revenue = annuals.revenue.value
    previous_revenue = (
        annuals.previous_revenue.value if annuals.previous_revenue else None
    )
    metrics = {
        "revenue_usd": revenue,
        "previous_year_revenue_usd": previous_revenue,
        "revenue_growth_pct": _growth(revenue, previous_revenue),
        "gross_profit_usd": annuals.gross_profit,
        "gross_margin_pct": _ratio(annuals.gross_profit, revenue),
        "operating_income_usd": annuals.operating_income.value,
        "operating_margin_pct": _ratio(annuals.operating_income.value, revenue),
        "net_income_usd": annuals.net_income.value,
        "net_margin_pct": _ratio(annuals.net_income.value, revenue),
    }
    return {
        "name": display_name,
        "entity_name": annuals.entity_name,
        "cik": annuals.cik,
        "period": {"start": annuals.start, "end": annuals.end},
        "metrics": metrics,
        "sources": {
            "company_facts_url": company_facts_url(annuals.cik),
            "revenue": annuals.revenue.to_dict(),
            "previous_year_revenue": (
                annuals.previous_revenue.to_dict() if annuals.previous_revenue else None
            ),
            "gross_profit": {
                "derivation": annuals.gross_profit_derivation,
                "facts": [fact.to_dict() for fact in annuals.gross_profit_facts],
            },
            "operating_income": annuals.operating_income.to_dict(),
            "net_income": annuals.net_income.to_dict(),
        },
    }


def render_markdown(companies: Sequence[dict[str, Any]]) -> str:
    lines = [
        "# 大型科技公司财务对比",
        "",
        "数据来源：SEC EDGAR XBRL company facts API；各公司采用营收、经营利润和净利润齐备的最近 10-K 完整财年。",
        "",
        "| 公司 | 财年截止 | 营收（十亿美元） | 营收同比 | 毛利润（十亿美元） | 经营利润（十亿美元） | 净利润（十亿美元） | 毛利率 | 经营利润率 | 净利率 |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for company in companies:
        metrics = company["metrics"]
        name = company["name"]
        url = company["sources"]["company_facts_url"]
        lines.append(
            "| "
            + " | ".join(
                (
                    f"[{name}]({url})",
                    company["period"]["end"],
                    _number(metrics["revenue_usd"], billions=True),
                    _percent(metrics["revenue_growth_pct"]),
                    _number(metrics["gross_profit_usd"], billions=True),
                    _number(metrics["operating_income_usd"], billions=True),
                    _number(metrics["net_income_usd"], billions=True),
                    _percent(metrics["gross_margin_pct"]),
                    _percent(metrics["operating_margin_pct"]),
                    _percent(metrics["net_margin_pct"]),
                )
            )
            + " |"
        )
    lines.extend(
        (
            "",
            "注：营收同比按相邻完整财年计算。毛利润优先采用同期间 `GrossProfit`，否则用同期间营收减营业成本；不同期间的事实不会拼接。",
            "`N/A` 表示同期间事实或相邻财年营收不足，未以其他期间或其他来源补值。",
            "各公司财年截止日及成本费用分类不完全相同；GAAP 净利润还可能受投资损益和一次性税项影响。",
        )
    )
    return "\n".join(lines)


def _growth(current: int | float, previous: int | float | None) -> float | None:
    if previous in (None, 0):
        return None
    return (current / previous - 1) * 100


def _ratio(numerator: int | float | None, denominator: int | float) -> float | None:
    if numerator is None or denominator == 0:
        return None
    return numerator / denominator * 100


def _number(value: int | float | None, billions: bool = False) -> str:
    if value is None:
        return "N/A"
    if billions:
        return f"{value / 1_000_000_000:.1f}"
    return str(value)


def _percent(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.1f}%"


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="仅使用 SEC EDGAR XBRL company facts API 比较大型科技公司财务指标。"
    )
    parser.add_argument(
        "--user-agent",
        default=os.environ.get("SEC_USER_AGENT"),
        help="SEC 要求的 User-Agent；也可设置 SEC_USER_AGENT 环境变量。",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="输出格式（默认：markdown）。",
    )
    parser.add_argument("--timeout", type=float, default=30.0, help="单次请求超时秒数。")
    args = parser.parse_args(argv)
    if not args.user_agent or not args.user_agent.strip():
        parser.error("请通过 --user-agent 或 SEC_USER_AGENT 提供真实 SEC User-Agent")
    if args.timeout <= 0:
        parser.error("--timeout 必须大于 0")
    return args


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    client = SecCompanyFactsClient(args.user_agent, timeout=args.timeout)
    companies = []
    try:
        for display_name, cik in COMPANIES:
            payload = client.fetch(cik)
            annuals = extract_company_annuals(payload, cik)
            companies.append(build_result(annuals, display_name))
    except CompanyFactsError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        return 1

    if args.format == "json":
        document = {
            "source": "SEC EDGAR XBRL company facts API",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "companies": companies,
        }
        print(json.dumps(document, ensure_ascii=False, indent=2, allow_nan=False))
    else:
        print(render_markdown(companies))
    return 0


if __name__ == "__main__":
    sys.exit(main())
