# Issue #1 第八轮断言—来源映射

| 断言 | 来源 | 性质与限制 |
|---|---|---|
| 2023自然年需要2023 Q1—Q4及2024 Q1，且2023 Q1来自前一年数据包 | `bls2026pumdguide`; `bls2026pumddata` | BLS正式方法 |
| CQ/PQ的自然年组合规则 | `bls2026pumdguide` | BLS正式方法 |
| 人口分母使用`FINLWT21/4 × MO_SCOPE/3` | `bls2026pumdguide` | BLS正式公式 |
| FMLI 12个月收入不调整会产生约四倍估计 | `bls2026faq` | BLS明确警告 |
| Interview-only估计不能直接匹配整合发布表 | `bls2026pumdguide`; `bls2026pumddoc` | BLS方法限制 |
| CUTENURE 1—6的住房代码 | `ilo2007cutenure`; 数据内观察值 | ILO保存的BLS元数据；发布前仍应以当期BLS字典复核 |
| 2021—2022一人CU×年龄公开基准 | `bls2023oneperson2534` | 两年整合表，不是2023单年真值 |
| 第八轮数值 | 上传的BLS ZIP及`round08_ce_y1.py` | 本轮直接计算；aggregate-only；状态为preliminary |
