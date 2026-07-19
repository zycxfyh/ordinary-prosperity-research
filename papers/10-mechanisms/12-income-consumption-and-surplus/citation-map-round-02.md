# 第二轮引用映射

> 用途：为 `round-02-harmonisation-and-initial-analysis.md` 中的当前统计断言指定准确来源。后续整合论文时，将这些键并入 `bibliography/master.bib` 并替换正文中的通用方法引用。

| 正文断言 | 准确 citation key | 说明 |
|---|---|---|
| 2022—23年澳大利亚等价化家庭可支配收入中位数为每周1,192澳元（2023年6月价格） | `abs2025householdincomewealth` | 该点来自HILDA；同一页面另列2019—20 SIH数据 |
| ABS不发布2023—24 SIH收入、财富与住房成本结果 | `abs2025sihnonrelease` | 因问卷设计、调查无应答和数据质量问题 |
| 2026年3月季度家庭储蓄收入比率为6.2% | `abs2026nationalaccounts` | 宏观家庭部门指标，不代表中位家庭 |
| 2026年3月季度澳大利亚家庭财富为19,211.9十亿澳元 | `abs2026financewealth` | 宏观资产负债表，不能显示家庭间分布与流动性 |

## 正文替换建议

```text
[@abs2022sihincome]
→ [@abs2025householdincomewealth]

未带引用的2023—24 SIH停发段落
→ [@abs2025sihnonrelease]

[@abs2025savingmethod]（作为当前6.2%数值来源）
→ [@abs2026nationalaccounts]

未带引用的2026年家庭财富段落
→ [@abs2026financewealth]
```

`abs2022sihincome` 与 `abs2025savingmethod` 仍应保留，分别用于收入概念和家庭储蓄率方法，而不是作为最新观测值来源。
