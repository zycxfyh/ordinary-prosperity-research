# Round 10 CE 全支出数据接入与执行协议

## 目标

Round 10 将 Round 9 已验证的食品整合扩展到 2023 年全部发布支出 UCC。脚本必须直接解析 BLS 官方 Integrated Hierarchical Grouping，并将 Source Selection workbook 作为独立版本证据摄取。

## 必需输入

```text
data/raw/us-ce/intrvw22.zip
data/raw/us-ce/intrvw23.zip
data/raw/us-ce/diary23.zip
data/raw/us-ce/stubs.zip
data/raw/us-ce/ce_source_integrate.xlsx
```

原始微观数据、官方二进制文档和派生 respondent-level 数据均不得提交到 Git。

## 官方角色

- `intrvw22.zip`：提供 2023 Interview Q1；
- `intrvw23.zip`：提供 2023 Interview Q2—Q4 及 2024 Q1 回溯；
- `diary23.zip`：提供 2023 四个 Diary collection quarters；
- `stubs.zip`：包含 `CE-HG-Integ-2023.txt`，定义 UCC 来源、annualization factor、section 与层级；
- `ce_source_integrate.xlsx`：记录 CE 发布表的调查来源选择，用于版本和结构交叉核对。

## 完整性记录

执行前必须记录：

1. 文件名；
2. 字节数；
3. SHA-256；
4. ZIP 完整性；
5. grouping 中选中的 member；
6. source-selection workbook 的 sheet、行列数与非空单元格数；
7. 运行脚本 commit SHA；
8. Python、pandas、numpy 与 openpyxl 版本。

## 环境

```bash
python -m pip install pandas numpy openpyxl pytest
```

## 合成合同测试

```bash
pytest -q tests/test_round10_full_expenditure_integration.py
```

测试覆盖：

- 官方固定宽度起始位置；
- UCC source/factor/section 解析；
- 同一 UCC 在多个层级出现时只计一次；
- source 或 factor 冲突时 fail closed；
- Interview 与 Diary 年度化 factor；
- 独立样本均值和方差合并。

## 正式运行

```bash
python analysis/us-ce/round10_full_expenditure_integration.py \
  --interview-2022 data/raw/us-ce/intrvw22.zip \
  --interview-2023 data/raw/us-ce/intrvw23.zip \
  --diary-2023 data/raw/us-ce/diary23.zip \
  --hierarchical-groupings data/raw/us-ce/stubs.zip \
  --source-selection data/raw/us-ce/ce_source_integrate.xlsx \
  --output-dir data/derived/us-ce/round10
```

## 准入门

脚本默认使用：

```text
BLS 2023 all-CU total expenditure = 77,280 USD
validation tolerance = ±1.0%
```

只有全体 consumer units 的综合总支出通过准入门，结果才可标记：

```text
integrated_expenditure_validated
```

若失败，脚本必须保留 manifest、映射、样本审计和 validation CSV，然后以非零状态退出。Y1 和住房细分结果全部保持阻断。

## 输出

```text
data/derived/us-ce/round10/
├── issue-04-round-10-source-manifest.json
├── issue-04-round-10-ucc-source-map.csv
├── issue-04-round-10-source-selection-audit.csv
├── issue-04-round-10-ucc-coverage.csv
├── issue-04-round-10-ucc-estimates-all-cu.csv
├── issue-04-round-10-category-estimates.csv
├── issue-04-round-10-group-total-estimates.csv
├── issue-04-round-10-sample-audit.csv
└── issue-04-round-10-validation.csv
```

输出只允许包含聚合估计、哈希、样本计数、UCC 元数据和验证状态。

## 解释边界

即使全体总支出验证通过：

- Y1 仍是单人经济共享单位，不等于住宅独居；
- 租户与按揭组差异仍是描述性结果；
- Interview 与 Diary 不能按受访者记录连接；
- 综合群体均值不能构造个人年度现金账本；
- 收入多重插补、按揭本金、资产、债务和家庭转移属于后续研究。
