# Round 7 CE 数据接入协议

## 所需文件

从 BLS Consumer Expenditure Surveys Public Use Microdata Data Files 页面下载 CSV Interview 数据包：

```text
intrvw22.zip
intrvw23.zip
```

不要重命名、解压后重新打包或修改文件内容。

## 放置位置

```text
data/raw/us-ce/intrvw22.zip
data/raw/us-ce/intrvw23.zip
```

`data/raw/`已被Git忽略。原始微观数据不得提交、上传到GitHub artifact或包含在论文附件中。

## 接入审计

收到文件后首先执行：

1. 记录原始文件名；
2. 记录下载日期和BLS来源页；
3. 计算字节数和SHA-256；
4. 使用ZIP完整性检查；
5. 盘点FMLI、MEMI、ITBI、MTBI、ITII和NTAXI文件；
6. 保存BLS当期字典、PUMD Guide和errata版本。

## 运行命令

```bash
python analysis/us-ce/round07_ce_y1.py \
  --target-year 2023 \
  --acknowledge-historical-tenure-codes \
  --output-dir data/derived/us-ce/round07
```

## 输出状态

首轮输出必须保持：

```text
preliminary_interview_only
```

只有完成UCC/source-selection、收入插补和BLS公开表验证后，才能升级为研究估计。不得由脚本成功退出直接推导论文结论。

## 验证顺序

1. 检查样本筛选是否为25—34岁、一人CU、至少一名收入者；
2. 检查租房、有按揭、无按揭代码；
3. 检查自然年季度与`MO_SCOPE`；
4. 检查同一CU轮换访谈是否被重复计算；
5. 检查`FINLWT21`和replicate weights；
6. 检查收入变量`FINCBTXM`、`FINATXEM`、`FSALARYM`；
7. 检查交通汇总`TRANSCQ`、`TRANSPQ`；
8. 与BLS一人CU×年龄交叉表和年度人口规模对照；
9. 报告样本数、加权总体、中位数、分位数、标准误和RSE；
10. 保留失败日志，不用填充值绕过缺失变量。
