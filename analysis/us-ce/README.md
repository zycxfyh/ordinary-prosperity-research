# US Consumer Expenditure Survey analysis

本目录保存 Issue #1 第六轮的美国 CE 微观分析实现。原始 BLS 数据不提交到仓库。

## 研究状态

```text
source availability: public
implementation: available
current-session binary ingestion: blocked
new estimates committed: no
```

脚本输出只能先标记为 `preliminary_interview_only`。通过变量字典、UCC source selection、收入插补和公开表验证后，才允许升级为 `validated`。

## 环境

```bash
python --version  # 3.11+
python -m pip install pandas numpy
```

## 执行

在仓库根目录运行：

```bash
python analysis/us-ce/round06_ce_y1.py \
  --target-year 2023 \
  --download
```

第一次运行会下载官方 BLS CSV Interview 数据包：

```text
data/raw/us-ce/intrvw22.zip
data/raw/us-ce/intrvw23.zip
```

下载、解压并检查当前 BLS 字典中的 `CUTENURE` 后，再运行：

```bash
python analysis/us-ce/round06_ce_y1.py \
  --target-year 2023 \
  --acknowledge-historical-tenure-codes
```

脚本刻意要求第二次显式确认。历史住房代码来自 BLS 官方旧版字典，但每个发布年份仍必须以当期字典为准。

## 输出

默认写入：

```text
data/derived/us-ce/round06/
├── source_manifest.json
├── preliminary_y1_estimates.csv
├── y1_sample_audit.csv
└── audit_log.csv
```

### `source_manifest.json`

记录：

- BLS官方地址；
- 发布年份；
- 本地路径；
- 文件大小；
- SHA-256；
- 解压目录。

### `preliminary_y1_estimates.csv`

按以下组别输出：

- `all_y1`；
- `renter`；
- `owner_with_mortgage`；
- `owner_without_mortgage`。

每项指标包含：

- 未加权访谈数；
- 去重 consumer unit 数；
- 加权总体；
- 加权均值；
- 加权 P25、中位数与 P75；
- BRR 标准误和95%置信区间；
- 结果状态。

## Y1定义

```text
25 <= AGE_REF <= 34
FAM_SIZE == 1
NO_EARNR >= 1
```

这是**一人经济共享单位**，不必然表示住宅中独居。Consumer Expenditure Survey允许一个人与他人同住但保持财务独立时构成独立consumer unit。

## 自然年规则

2023年需要两个相邻发布包。支出汇总变量按BLS规则组合：

```text
2023 Q1: CQ
2023 Q2-Q4: CQ + PQ
2024 Q1: PQ
```

自然年分析权重：

```text
FINLWT21 / 4 × MO_SCOPE / 3
```

## 发布前强制检查

1. 取得并保存当期BLS变量字典；
2. 核对`CUTENURE`代码；
3. 核对2023 FMLI errata已包含在数据包中；
4. 确认12个月收入没有按访谈次数累加；
5. 使用ITBI、NTAXI与收入插补文件复核收入；
6. 使用hierarchical grouping和source-selection重建主要UCC；
7. 解释Interview-only与综合CE正式表之间的差异；
8. 对普通支出应用44个BRR权重；
9. 对插补收入使用CE收入插补指南；
10. 报告样本量、权重、零值、top-code、插补和不确定性。

## 不提交的文件

请不要将以下内容提交到Git：

```text
data/raw/
data/derived/us-ce/round06/*.csv
```

研究结果进入仓库时，应提交经过审查的汇总表、代码版本、来源manifest和方法说明，而不是包含微观记录的原始数据。