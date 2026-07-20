# US Consumer Expenditure Survey analysis

本目录保存 Issue #1 及其子 Issue #4 的美国 CE 微观分析实现。原始 BLS 数据和官方二进制输入不提交到仓库。

## 当前研究状态

```text
Round 6: Interview estimator implementation complete
Round 7: cloud download boundary documented
Round 8: real 2023 Interview Y1 estimates generated
Round 9: Diary–Interview food integration validated against official totals
Round 10: full-expenditure estimator and contract tests ready
Round 10 official binary execution: not yet run
```

结果状态必须逐项区分：

- `preliminary_interview_only`：只使用 Interview；
- `integrated_food_validated`：食品估计程序已复现官方全体结果；
- `integrated_expenditure_validated`：完整支出程序通过 77,280 美元准入门；
- `supported_preliminary_descriptive`：全体估计器通过后、RSE 可接受的子群描述性结果；
- `blocked`：方法、来源、样本或验证尚不足。

## 环境

```bash
python --version  # 3.11+
python -m pip install pandas numpy openpyxl pytest
```

## 原始输入

```text
data/raw/us-ce/
├── intrvw22.zip
├── intrvw23.zip
├── diary22.zip
├── diary23.zip
├── stubs.zip
└── ce_source_integrate.xlsx
```

- 2023 Interview 自然年需要 `intrvw22.zip` 与 `intrvw23.zip`；
- 2023 Diary 主估计只需要 `diary23.zip`；
- `diary22.zip`用于相邻年份敏感性；
- `stubs.zip`提供 `CE-HG-Integ-2023.txt`；
- source-selection workbook 作为独立版本证据摄取。

## Y1 定义

```text
25 <= AGE_REF <= 34
FAM_SIZE == 1
NO_EARNR >= 1
```

Y1 表示一人经济共享单位，不必然表示住宅中独居。

## 估计规则

### Interview population

```text
Σ FINLWT21 / 4 × MO_SCOPE / 3
```

2023 自然年支出月份来自：

```text
2023 Q1: CQ
2023 Q2-Q4: CQ + PQ
2024 Q1: PQ
```

### Diary population

```text
Σ FINLWT21 / 4
```

Diary EXPD 为周记录。Round 10 先乘 13 转为季度金额，再乘官方 integrated grouping factor。

### 双调查整合

Interview 与 Diary 是独立样本，不能连接 respondent records。每个 UCC 分别估计后，在估计量层面合并：

```text
combined mean = Interview mean + Diary mean
combined SE   = sqrt(Interview SE² + Diary SE²)
```

## Round 9：食品整合

```bash
python analysis/us-ce/round09_diary_food_integration.py \
  --interview-2022 data/raw/us-ce/intrvw22.zip \
  --interview-2023 data/raw/us-ce/intrvw23.zip \
  --diary-2022 data/raw/us-ce/diary22.zip \
  --diary-2023 data/raw/us-ce/diary23.zip \
  --output-dir data/derived/us-ce/round09
```

Round 9 已近乎精确复现 BLS 2023 全体 consumer units 的食品在家、外食和食品合计。

## Round 10：全部支出整合

先运行合成合同测试：

```bash
pytest -q tests/test_round10_full_expenditure_integration.py
```

再执行正式估计：

```bash
python analysis/us-ce/round10_full_expenditure_integration.py \
  --interview-2022 data/raw/us-ce/intrvw22.zip \
  --interview-2023 data/raw/us-ce/intrvw23.zip \
  --diary-2023 data/raw/us-ce/diary23.zip \
  --hierarchical-groupings data/raw/us-ce/stubs.zip \
  --source-selection data/raw/us-ce/ce_source_integrate.xlsx \
  --output-dir data/derived/us-ce/round10
```

Round 10 直接解析官方固定宽度 grouping 的：

- UCC；
- source；
- annualization factor；
- section；
- hierarchy path。

全体 consumer units 综合总支出必须在默认 ±1% 容差内复现 BLS 2023 官方值 77,280 美元，否则脚本非零退出，所有 Y1 细分继续阻断。详细协议见 `round10-data-intake.md`。

## 发布前强制检查

1. 保存全部输入字节数、SHA-256 与 ZIP 完整性；
2. 核对 2023 FMLI errata；
3. 确认 `CE-HG-Integ-2023.txt` 被唯一选中；
4. 冲突 UCC source/factor 必须 fail closed；
5. source-selection workbook 已摄取并记录结构；
6. 44 个 BRR replicate weights 已用于普通支出；
7. 报告样本量、加权总体、SE、RSE 与置信区间；
8. 小样本住房组不得进入主结论；
9. ITII 收入插补不确定性不得由普通 BRR 替代；
10. 群体均值不得解释为个体现金账本或因果效应。

## 不提交的文件

```text
data/raw/
data/derived/
```

研究分支只提交可复现代码、输入哈希、聚合结果、验证证据和方法说明。