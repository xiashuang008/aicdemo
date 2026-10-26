# 大型科技公司财务对比

仅使用 Python 标准库和 SEC EDGAR XBRL company facts API，比较苹果、微软、Alphabet、亚马逊、Meta、英伟达的年度营收、增长、毛利润、经营利润和净利润。脚本不内置财务结果，也不访问行情、新闻或财务聚合网站。

## 运行

需要 Python 3.10 或更高版本，以及能够访问 `data.sec.gov` 的网络。SEC 要求请求方提供可识别的名称和联系方式；必须通过 `--user-agent` 或环境变量 `SEC_USER_AGENT` 提供真实 User-Agent，脚本没有默认值。

```bash
python compare.py --user-agent "你的真实姓名 你的真实邮箱" --format markdown > comparison.md
python compare.py --user-agent "你的真实姓名 你的真实邮箱" --format json > comparison.json
```

也可以使用环境变量：

```bash
export SEC_USER_AGENT="你的真实姓名 你的真实邮箱"
python compare.py --format markdown > comparison.md
python compare.py --format json > comparison.json
```

可选参数 `--timeout` 设置单次请求超时秒数，默认 30 秒。六家公司严格按配置顺序逐家请求，成功取得并解析全部数据后才输出；失败时错误写入标准错误并返回非零状态，不输出部分公司的对比结果。缺少 User-Agent 会明确报错。

网络错误和超时会指数退避重试，HTTP 429 和 5xx 也会重试；默认最多请求四次。其他 HTTP 错误、无效 JSON 和无效响应结构会明确失败。401/403 错误会提示检查 User-Agent。

## 数据来源与筛选口径

每家公司只请求以下形式的 endpoint，其中 CIK 补足为十位数字：

```text
https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json
```

年度事实必须同时满足：

- `form` 为 `10-K` 或 `10-K/A`；
- `fp` 为 `FY`；
- 单位为 `USD`；
- `start`、`end`、`filed`、`accn` 和数值有效；
- `end - start` 为 300–400 天（含边界）。

同期间同一标签有多个披露时，采用 `filed` 最新的事实。营收标签按以下优先级选择，避免优先采用旧标签：

1. `RevenueFromContractWithCustomerExcludingAssessedTax`
2. `Revenues`
3. `SalesRevenueNet`

成本标签依次为 `CostOfGoodsAndServicesSold`、`CostOfRevenue`。经营利润和净利润分别只使用 `OperatingIncomeLoss`、`NetIncomeLoss`。

脚本先找出营收、经营利润和净利润三者共有的年度期间，再选择截止日最新的完整年度。三项核心指标必须来自完全相同的 `start` 和 `end`；如果最新营收年度缺少另一项核心指标，会回退到最近的三项齐备年度，而不是跨期间拼接。

前期营收必须是另一个 300–400 天的年度事实，其截止日早于本财年开始日，且与本财年截止日相隔 300–400 天。营收同比增长率为：

```text
(本年营收 / 前期营收 - 1) × 100%
```

找不到符合条件的相邻前期营收时，增长率显示为 `N/A`，不会使用季度、非相邻期间或外部数据替代。

## 毛利润与利润率

毛利润优先采用同期间 `GrossProfit`。若该事实不存在，则仅在同期间成本事实存在时，用同期间营收减成本计算；两者都没有时，毛利润和毛利率为 `N/A`。JSON 的 `sources.gross_profit.derivation` 区分 `reported` 和 `revenue_minus_cost`，其 `facts` 数组保留直接值或回退计算所引用的全部来源。

毛利率、经营利润率和净利率分别以毛利润、经营利润和净利润除以本年营收。Markdown 金额以十亿美元显示并四舍五入到一位小数，百分比显示到一位小数；JSON 保留 API 原始美元数值及未格式化的计算结果。

## JSON 来源元数据

每家公司包含财年 `period`、指标 `metrics` 和来源 `sources`。营收、前期营收、经营利润、净利润及毛利润相关事实均记录：

- `start`、`end`：事实期间；
- `value_usd`：原始美元数值；
- `tag`：XBRL 标签；
- `accession`：SEC 披露 accession；
- `filed`：披露日期。

`sources.company_facts_url` 记录对应 API 地址。各公司财年截止日和成本费用分类可能不同，GAAP 净利润也可能受投资损益及一次性税项影响，横向比较时应注意这些限制。

## 简报与独立核对

`comparison.md` 和 `comparison.json` 是真实 API 输出。`verification.md` 记录六家公司各一个营收值与对应 SEC 10-K 的独立核对；10-K 仅用于验证，不是脚本数据源。

中文简报使用 XeLaTeX 和 `ctexart`，重新编译命令为：

```bash
xelatex -interaction=nonstopmode -halt-on-error brief.tex
```

`brief.pdf` 为 A4 单页简报，`brief.tex` 为源文件。`TASK.md` 记录任务边界、智能体 Prompt、交付物和验收标准。
