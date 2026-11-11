# 项目进展记录

## 记录约定

- 重要分析或交付完成后，记录数据来源、核验结果、关键假设和最终交付物。
- 普通问答、临时分析和一般性修改过程不作记录。

## 2026-10-31

- 对比范围：苹果、微软、Alphabet、亚马逊、英伟达，不包含 Meta。
- 数据来源：`comparison.json`，原始来源为 SEC EDGAR XBRL company facts API。
- 核验结果：五家公司营收均已与对应 10-K 合并利润表核对，数值、单位和期间一致（5/5）；详见 `verification.md`。
- 主要交付物：`output/peer_comparison.html`、`output/figures/` 中的对比图、`output/tables/peer_comparison.tex`、`report/main.tex` 和单页 `report/main.pdf`。
- 口径与局限：各公司财年截止日不同，不能视为同一自然期间；GAAP 净利润可能受投资损益和一次性税项影响；毛利润包含直接披露与同期间营收减成本两种来源；报告不构成估值或投资建议。
- 文字与版式：报告已经润色并重新编译，数值、财年日期、来源和限制保持不变；最终 PDF 已逐页检查，无裁切或溢出。
