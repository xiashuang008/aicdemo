from __future__ import annotations

import json
import math
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date
from typing import Any, Iterable

API_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
REVENUE_TAGS = (
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "Revenues",
    "SalesRevenueNet",
)
COST_TAGS = ("CostOfGoodsAndServicesSold", "CostOfRevenue")
GROSS_PROFIT_TAGS = ("GrossProfit",)
OPERATING_INCOME_TAGS = ("OperatingIncomeLoss",)
NET_INCOME_TAGS = ("NetIncomeLoss",)


class CompanyFactsError(RuntimeError):
    pass


@dataclass(frozen=True)
class Fact:
    tag: str
    start: str
    end: str
    value: int | float
    accession: str
    filed: str

    @property
    def period(self) -> tuple[str, str]:
        return self.start, self.end

    def to_dict(self) -> dict[str, Any]:
        return {
            "tag": self.tag,
            "start": self.start,
            "end": self.end,
            "value_usd": self.value,
            "accession": self.accession,
            "filed": self.filed,
        }


@dataclass(frozen=True)
class CompanyAnnuals:
    entity_name: str
    cik: str
    revenue: Fact
    previous_revenue: Fact | None
    gross_profit: int | float | None
    gross_profit_facts: tuple[Fact, ...]
    gross_profit_derivation: str | None
    operating_income: Fact
    net_income: Fact

    @property
    def start(self) -> str:
        return self.revenue.start

    @property
    def end(self) -> str:
        return self.revenue.end


class SecCompanyFactsClient:
    def __init__(
        self,
        user_agent: str,
        timeout: float = 30.0,
        retries: int = 3,
    ) -> None:
        if not user_agent.strip():
            raise CompanyFactsError("SEC User-Agent 不能为空")
        self.user_agent = user_agent.strip()
        self.timeout = timeout
        self.retries = retries

    def fetch(self, cik: str) -> dict[str, Any]:
        normalized_cik = normalize_cik(cik)
        url = API_URL.format(cik=normalized_cik)
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/json",
                "Accept-Encoding": "identity",
            },
        )
        for attempt in range(self.retries + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    payload = json.load(response)
                if not isinstance(payload, dict) or not isinstance(payload.get("facts"), dict):
                    raise CompanyFactsError(f"CIK {normalized_cik} 的 SEC 响应格式无效")
                return payload
            except urllib.error.HTTPError as exc:
                retryable = exc.code == 429 or 500 <= exc.code < 600
                if retryable and attempt < self.retries:
                    time.sleep(2**attempt)
                    continue
                if exc.code in (401, 403):
                    detail = "；请检查 User-Agent 是否包含可识别的名称和联系方式"
                else:
                    detail = ""
                raise CompanyFactsError(
                    f"SEC 请求失败：CIK {normalized_cik}，HTTP {exc.code}{detail}"
                ) from exc
            except (urllib.error.URLError, TimeoutError) as exc:
                if attempt < self.retries:
                    time.sleep(2**attempt)
                    continue
                raise CompanyFactsError(
                    f"SEC 请求失败：CIK {normalized_cik}，{exc}"
                ) from exc
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise CompanyFactsError(f"CIK {normalized_cik} 的 SEC 响应不是有效 JSON") from exc
        raise AssertionError("unreachable")


def normalize_cik(cik: str) -> str:
    normalized = str(cik).strip()
    if not normalized.isdigit() or not 1 <= len(normalized) <= 10:
        raise CompanyFactsError(f"无效 CIK：{cik!r}")
    return normalized.zfill(10)


def company_facts_url(cik: str) -> str:
    return API_URL.format(cik=normalize_cik(cik))


def extract_company_annuals(payload: dict[str, Any], cik: str) -> CompanyAnnuals:
    normalized_cik = normalize_cik(cik)
    revenue_facts = _annual_facts(payload, REVENUE_TAGS)
    if not revenue_facts:
        raise CompanyFactsError(f"CIK {normalized_cik} 缺少 10-K 年度营收事实")

    operating_by_period = {
        fact.period: fact for fact in _annual_facts(payload, OPERATING_INCOME_TAGS)
    }
    net_by_period = {
        fact.period: fact for fact in _annual_facts(payload, NET_INCOME_TAGS)
    }
    complete_revenue_facts = [
        fact
        for fact in revenue_facts
        if fact.period in operating_by_period and fact.period in net_by_period
    ]
    if not complete_revenue_facts:
        raise CompanyFactsError(
            f"CIK {normalized_cik} 缺少营收、经营利润和净利润同期间的完整 10-K 年度事实"
        )

    revenue = max(complete_revenue_facts, key=lambda fact: (fact.end, fact.start))
    period = revenue.period
    operating_income = operating_by_period[period]
    net_income = net_by_period[period]

    gross_fact = _fact_for_period(payload, GROSS_PROFIT_TAGS, period)
    cost_fact = _fact_for_period(payload, COST_TAGS, period)
    if gross_fact is not None:
        gross_profit = gross_fact.value
        gross_profit_facts = (gross_fact,)
        gross_profit_derivation = "reported"
    elif cost_fact is not None:
        gross_profit = revenue.value - cost_fact.value
        gross_profit_facts = (revenue, cost_fact)
        gross_profit_derivation = "revenue_minus_cost"
    else:
        gross_profit = None
        gross_profit_facts = ()
        gross_profit_derivation = None

    previous_revenue = _previous_annual_fact(payload, REVENUE_TAGS, revenue)
    entity_name = str(payload.get("entityName") or normalized_cik)
    return CompanyAnnuals(
        entity_name=entity_name,
        cik=normalized_cik,
        revenue=revenue,
        previous_revenue=previous_revenue,
        gross_profit=gross_profit,
        gross_profit_facts=gross_profit_facts,
        gross_profit_derivation=gross_profit_derivation,
        operating_income=operating_income,
        net_income=net_income,
    )


def _fact_for_period(
    payload: dict[str, Any], tags: Iterable[str], period: tuple[str, str]
) -> Fact | None:
    return next(
        (fact for fact in _annual_facts(payload, tags) if fact.period == period),
        None,
    )


def _previous_annual_fact(
    payload: dict[str, Any], tags: Iterable[str], current: Fact
) -> Fact | None:
    current_start = date.fromisoformat(current.start)
    current_end = date.fromisoformat(current.end)
    candidates = []
    for fact in _annual_facts(payload, tags):
        previous_end = date.fromisoformat(fact.end)
        if previous_end >= current_start:
            continue
        if 300 <= (current_end - previous_end).days <= 400:
            candidates.append(fact)
    return max(candidates, key=lambda fact: fact.end, default=None)


def _annual_facts(payload: dict[str, Any], tags: Iterable[str]) -> list[Fact]:
    facts = payload.get("facts")
    if not isinstance(facts, dict):
        return []
    gaap = facts.get("us-gaap")
    if not isinstance(gaap, dict):
        return []

    tag_priority = {tag: priority for priority, tag in enumerate(tags)}
    by_period: dict[tuple[str, str], Fact] = {}
    for tag in tag_priority:
        concept = gaap.get(tag)
        if not isinstance(concept, dict):
            continue
        units = concept.get("units")
        if not isinstance(units, dict):
            continue
        entries = units.get("USD")
        if not isinstance(entries, list):
            continue
        for entry in entries:
            fact = _as_annual_fact(tag, entry)
            if fact is None:
                continue
            incumbent = by_period.get(fact.period)
            rank = (-tag_priority[fact.tag], fact.filed, fact.accession)
            if incumbent is None:
                by_period[fact.period] = fact
                continue
            incumbent_rank = (
                -tag_priority[incumbent.tag],
                incumbent.filed,
                incumbent.accession,
            )
            if rank > incumbent_rank:
                by_period[fact.period] = fact
    return sorted(by_period.values(), key=lambda fact: (fact.end, fact.start))


def _as_annual_fact(tag: str, entry: Any) -> Fact | None:
    if not isinstance(entry, dict):
        return None
    if entry.get("form") not in ("10-K", "10-K/A") or entry.get("fp") != "FY":
        return None
    value = entry.get("val")
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        return None
    accession = entry.get("accn")
    if not isinstance(accession, str) or not accession.strip():
        return None
    try:
        start = date.fromisoformat(entry["start"])
        end = date.fromisoformat(entry["end"])
        filed = date.fromisoformat(entry["filed"])
    except (KeyError, TypeError, ValueError):
        return None
    if not 300 <= (end - start).days <= 400:
        return None
    return Fact(
        tag=tag,
        start=start.isoformat(),
        end=end.isoformat(),
        value=value,
        accession=accession,
        filed=filed.isoformat(),
    )
