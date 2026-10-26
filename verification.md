# SEC EDGAR 10-K 独立验证：六项全部通过（6/6）

六家公司 `metrics.revenue_usd` 均与对应 accession 的 SEC EDGAR 官方 10-K 合并利润表营收一致，报表单位均为百万美元，财年期间一致。本次仅以 `comparison.json` 取得脚本原始值、XBRL 标签和 accession；10-K 仅用于独立核对，不替代 company facts API 作为脚本数据源。核对来源仅为 SEC EDGAR 官方 10-K 主文档及其官方报表文件，未使用其他网站。

通过标准：10-K 合并利润表的营收按报表单位换算为美元后，与 `metrics.revenue_usd` 完全相等，且对应完整财年与脚本期间一致。

## 1. 苹果（Apple Inc.）

- 指标：`metrics.revenue_usd`
- XBRL 标签：`RevenueFromContractWithCustomerExcludingAssessedTax`
- 脚本原始美元值：416,161,000,000 美元
- 10-K 合并利润表：CONSOLIDATED STATEMENTS OF OPERATIONS，`Net sales` 为 **416,161 百万美元**，即 416,161,000,000 美元
- 财年期间：2024-09-29 至 2025-09-27；10-K 报表列为 `12 Months Ended Sep. 27, 2025`
- accession：`0000320193-25-000079`
- 10-K URL：https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm
- 合并利润表官方文件：https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/R3.htm
- 结论：**通过**。数值、单位和期间均一致。

## 2. 微软（Microsoft Corporation）

- 指标：`metrics.revenue_usd`
- XBRL 标签：`RevenueFromContractWithCustomerExcludingAssessedTax`
- 脚本原始美元值：331,839,000,000 美元
- 10-K 合并利润表：INCOME STATEMENTS，`Total revenue`（官方渲染表汇总行名为 `Revenue`）为 **331,839 百万美元**，即 331,839,000,000 美元
- 财年期间：2025-07-01 至 2026-06-30；10-K 报表列为 `Year Ended June 30, 2026`，官方渲染表列示 `12 Months Ended Jun. 30, 2026`
- accession：`0001193125-26-323660`
- 10-K URL：https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm
- 合并利润表官方文件：https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/R2.htm
- 结论：**通过**。数值、单位和期间均一致。

## 3. Alphabet（Alphabet Inc.）

- 指标：`metrics.revenue_usd`
- XBRL 标签：`Revenues`
- 脚本原始美元值：402,836,000,000 美元
- 10-K 合并利润表：CONSOLIDATED STATEMENTS OF INCOME，`Revenues` 为 **402,836 百万美元**，即 402,836,000,000 美元
- 财年期间：2025-01-01 至 2025-12-31；10-K 报表列为 `12 Months Ended Dec. 31, 2025`
- accession：`0001652044-26-000018`
- 10-K URL：https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/goog-20251231.htm
- 合并利润表官方文件：https://www.sec.gov/Archives/edgar/data/1652044/000165204426000018/R5.htm
- 结论：**通过**。数值、单位和期间均一致。

## 4. 亚马逊（AMAZON COM INC）

- 指标：`metrics.revenue_usd`
- XBRL 标签：`RevenueFromContractWithCustomerExcludingAssessedTax`
- 脚本原始美元值：716,924,000,000 美元
- 10-K 合并利润表：CONSOLIDATED STATEMENTS OF OPERATIONS，`Total net sales` 为 **716,924 百万美元**，即 716,924,000,000 美元
- 财年期间：2025-01-01 至 2025-12-31；10-K 报表列为 `Year Ended December 31, 2025`，官方渲染表列示 `12 Months Ended Dec. 31, 2025`
- accession：`0001018724-26-000004`
- 10-K URL：https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm
- 合并利润表官方文件：https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/R4.htm
- 结论：**通过**。数值、单位和期间均一致。

## 5. Meta（Meta Platforms, Inc.）

- 指标：`metrics.revenue_usd`
- XBRL 标签：`RevenueFromContractWithCustomerExcludingAssessedTax`
- 脚本原始美元值：200,966,000,000 美元
- 10-K 合并利润表：CONSOLIDATED STATEMENTS OF INCOME，`Revenue` 为 **200,966 百万美元**，即 200,966,000,000 美元
- 财年期间：2025-01-01 至 2025-12-31；10-K 报表列为 `12 Months Ended Dec. 31, 2025`
- accession：`0001628280-26-003942`
- 10-K URL：https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/meta-20251231.htm
- 合并利润表官方文件：https://www.sec.gov/Archives/edgar/data/1326801/000162828026003942/R5.htm
- 结论：**通过**。数值、单位和期间均一致。

## 6. 英伟达（NVIDIA CORP）

- 指标：`metrics.revenue_usd`
- XBRL 标签：`Revenues`
- 脚本原始美元值：215,938,000,000 美元
- 10-K 合并利润表：Consolidated Statements of Income，`Revenue` 为 **215,938 百万美元**，即 215,938,000,000 美元
- 财年期间：2025-01-27 至 2026-01-25；10-K 报表列为 `12 Months Ended Jan. 25, 2026`
- accession：`0001045810-26-000021`
- 10-K URL：https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/nvda-20260125.htm
- 合并利润表官方文件：https://www.sec.gov/Archives/edgar/data/1045810/000104581026000021/R3.htm
- 结论：**通过**。数值、单位和期间均一致。

`comparison.md` 对比表中的十亿美元展示值是将原始美元值除以 1,000,000,000 后四舍五入至 1 位小数的结果，并非 10-K 原始披露精度；本次通过/失败判断使用未四舍五入的美元值进行核对。
