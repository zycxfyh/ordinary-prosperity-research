# 第九轮断言—来源映射

| 断言 | 主要来源 | 证据类型 | 备注 |
|---|---|---|---|
| Interview和Diary使用独立样本，不能跨调查连接CU | `bls2026PumdGettingStarted` | 官方方法 | 综合只能在估计量/UCC层面进行 |
| Diary每周记录独立加权，周值需年度化 | `bls2026PumdGettingStarted` | 官方方法 | 本轮使用52周年度化；与季度乘13等价 |
| 综合估计需要在UCC层面分别估计并相加 | `bls2026PumdGettingStarted`, `bls2026PumdDocumentation` | 官方方法 | 非食品完整整合仍需hierarchical grouping |
| 2023 Interview食品在家定义及80%杂货食品分配 | `bls2024PumdFoodHomeErrata` | 官方勘误 | 解释FMLI食品摘要不能直接作为综合食品 |
| 2023 FMLD `FOODHOME`/`FOODTOT`被重新处理 | `bls2024PumdSummaryErrata` | 官方勘误 | 当前文件通过官方总量复现验证 |
| 2023官方全体食品=9,985；在家=6,053；外食=3,933 | `bls2024ConsumerExpenditures2023` | 官方统计 | 用于fail-closed准入验证 |
| 食品细项的Interview/Diary来源与UCC含义 | `bls2026UccCpiConcordance` | 官方分类 | 与PUMD `PUBFLAG/PUB_FLAG`和过渡月份联合使用 |
| 2023主估计只需Diary 2023四季度；Interview需相邻年度包 | `bls2026PumdData`, `bls2026PumdGettingStarted` | 官方文件结构 | 2022 Diary仅用于敏感性 |
| Y1食品7,616.89美元及住房分组结果 | 四份PUMD、`round09_diary_food_integration.py` | 本轮加权估计 | 食品总体程序已通过官方全体值复现 |
| 完整总支出仍Blocked | `bls2026PumdDocumentation`, 本轮验证表 | 方法与内部验证 | 部分整合值较官方总支出低约5.2% |
