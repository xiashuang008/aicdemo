# aicdemo 任务文档

## 目标

仅通过 SEC EDGAR XBRL company facts API 获取财务数据，比较苹果、微软、Alphabet、亚马逊、Meta 和英伟达的营收规模、营收增长、经营利润及利润率，交付可复现的表格和一页中文 LaTeX 简报。

## 数据来源边界

- 数据脚本只请求 `https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json`。
- 不使用行情、财报聚合网站、新闻报道或硬编码财务结果。
- 每家公司选一个脚本输出值，与对应 10-K 独立核对。10-K 只用于人工/智能体验证，不作为脚本的数据源。
- CIK、公司显示名称和 XBRL 标签属于配置，不是财务结果。

## 工作步骤

1. 编写本任务文档及智能体 Prompt。
2. 完成数据获取、年度事实筛选、指标计算和 CLI。
3. 运行真实 API，生成 Markdown 与 JSON 对比表。
4. 每家公司选取一个数值，与对应 10-K 核对并记录来源和结果。
5. 根据对比表撰写一页中文 LaTeX 简报，编译 PDF 并检查页数。
6. 编译代码、验证 JSON、检查错误路径、复核所有交付物。
7. 全部检查通过后提交 git commit，推送 `main` 到 GitHub，并确认远端提交记录。

## 智能体 Prompt

### 数据与实现智能体

> 你在 `C:/Users/xiashuang008/aicdemo` 工作。仓库目标是仅用 SEC EDGAR XBRL company facts API 比较苹果、微软、Alphabet、亚马逊、Meta、英伟达。现有 `companyfacts.py` 和 `compare.py` 是初稿，请阅读、修正并完成实现，所有代码由你编写或修订。只允许 Python 标准库，不新增依赖，不创建测试脚手架。脚本必须要求真实 SEC User-Agent，顺序请求 API，处理超时、429/5xx 和无效响应；从 10-K/10-K-A、FY、300–400 天 USD 事实中选择最新完整年度，避免旧标签和跨期间拼接。营收候选为 RevenueFromContractWithCustomerExcludingAssessedTax、Revenues、SalesRevenueNet；成本候选为 CostOfGoodsAndServicesSold、CostOfRevenue；经营利润和净利润分别为 OperatingIncomeLoss、NetIncomeLoss。毛利润优先同期间 GrossProfit，否则同期间营收减成本。输出中文 Markdown 和含期间、数值、标签、accession、filed 的 JSON。更新 README，说明运行方法和口径。不要生成财务数据、不要 commit 或 push。完成后报告修改和需要主智能体验证的事项。

### 10-K 核对智能体

> 对 `comparison.json` 中六家公司分别选取一个直接来自 XBRL 的数值，优先营收或经营利润。根据 JSON 的 accession 找到 SEC EDGAR 上对应 10-K，核对 10-K 合并利润表中的数值、单位和期间。10-K 仅用于验证，不得替代 company facts API 作为脚本数据源。记录公司、指标、脚本值、10-K 值、财年期间、accession、10-K URL 和通过/失败结论。不得猜测；无法核对就明确标记失败。不要修改代码、不要 commit 或 push。

### 简报智能体

> 在 `C:/Users/xiashuang008/aicdemo` 中，只根据 `comparison.json` 和已完成的 10-K 核对记录撰写中文简报。创建 `brief.tex`，使用 XeLaTeX 可编译的中文文档类，内容必须控制在一页，涵盖规模、增长、利润率、商业模式差异、财年及一次性损益限制，并注明唯一数据源为 SEC company facts API。表格数字必须与 JSON 一致，不使用外部数据。编译生成 `brief.pdf`，检查只有一页且中文可读。不要 commit 或 push。

## 交付物

- `companyfacts.py`、`compare.py`：可复现的数据获取与计算脚本。
- `comparison.md`、`comparison.json`：真实 API 生成的对比表及来源元数据。
- `verification.md`：六家公司各一个数值与 10-K 的核对记录。
- `brief.tex`、`brief.pdf`：一页中文 LaTeX 简报及 PDF。
- `README.md`：运行方法与口径。
- GitHub `main` 分支上的提交记录；所有检查通过后才推送。

## 验收标准

- 脚本没有第三方依赖，数据请求只访问 company facts endpoint。
- 六家公司均有同一年度期间的营收、经营利润和净利润；增长率使用相邻完整财年。
- 毛利润直接值或回退计算均有来源记录，不混用不同期间。
- Markdown 表格、JSON 和 PDF 数字一致；JSON 可解析。
- 六项 10-K 核对全部通过。
- `python -m py_compile companyfacts.py compare.py` 通过。
- XeLaTeX 编译通过，PDF 恰为一页且中文显示正常。
- 缺少 User-Agent 时明确失败；请求或必需事实缺失时不输出误导性结果。
- git 工作区内容检查完毕，提交并推送后远端 commit 与本地一致。
