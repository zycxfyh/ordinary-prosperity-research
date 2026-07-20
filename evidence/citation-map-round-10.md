# Round 10 断言—来源映射

| 断言 | 证据 | 状态 |
|---|---|---|
| CE 发布结果整合 Interview 与 Diary 两个独立样本 | `bls2026_pumd_getting_started` | 官方方法 |
| 两套调查的受访者不能按 NEWID 跨调查连接 | `bls2026_pumd_getting_started` | 官方方法 |
| Integrated Hierarchical Grouping 给出 UCC source、factor 与 section | `bls2026_pumd_documentation` | 官方格式合同 |
| 固定宽度起始位置为 1/4/7/70/83/86/89 | `bls2026_pumd_documentation` | 官方格式合同 |
| Diary 周估计先乘 13 转成季度，再使用官方 factor 年度化 | `bls2026_pumd_getting_started`、`bls2026_pumd_documentation` | 官方方法 + 官方元数据 |
| Interview 年度估计需要目标年四季度及次年 Q1，并从前一年度包取得目标年 Q1 | `bls2026_pumd_getting_started`、`bls2026_pumd_data` | 官方方法 |
| `FINLWT21 / 4` 与 Interview `MO_SCOPE / 3` 用于总体分母 | `bls2026_pumd_getting_started` | 官方方法 |
| 普通支出抽样误差使用 44 个 replicate weights | `bls2026_pumd_getting_started` | 官方方法 |
| 2023 all-CU 官方总支出为 77,280 美元 | `bls2024_ce_2023` | 官方发布值 |
| PUMD 因 disclosure protection 可能无法与 confidential tables 完全一致 | `bls2026_pumd_getting_started`、`bls2026_pumd_data` | 官方限制 |
| Round 10 当前尚未产生新的完整总支出估计 | 本轮执行日志与 Draft PR | 仓库事实 |
