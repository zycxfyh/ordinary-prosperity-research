# 美国 CE 2023 Round 10：全支出 UCC 整合的研究合同与实现

> Issue #4 · Parent Issue #1  
> 状态：`estimator-ready / full-total-not-yet-executed`  
> 日期：2026-07-20

## 摘要

Round 9 已在 UCC 层整合 Consumer Expenditure Survey 的 Interview 与 Diary 两个独立样本，并将 2023 年全体 consumer units 的食品在家、外食和食品合计复现到与 BLS 官方值相差不超过 0.013%。但把综合食品替换进 Interview 总支出后，部分整合总支出仍比官方 77,280 美元低约 5.2%。这说明食品以外的服装、家居、个人护理、娱乐及其他项目仍包含 Diary 来源 UCC 或年度化 factor，不能继续使用 FMLI Interview-only 总额代替完整综合消费。

本轮建立全支出估计器。实现不手工维护“哪些项目来自哪个调查”的类别清单，而是机械解析 BLS 2023 Integrated Hierarchical Grouping 中每个 UCC 的 source、factor、section 和层级路径，并摄取 source-selection workbook 作为独立版本证据。Interview 与 Diary 分别应用权重和 44 个 BRR replicate weights，均值在 UCC 和类别层聚合，两个独立样本的方差相加。

当前会话没有重新摄取官方 grouping/workbook 与原始 ZIP 二进制文件，因此本轮没有生成新的全支出数值，也不宣称已经复现 77,280 美元。已完成的是可运行、失败封闭的估计器、合成合同测试、输入协议和准入标准。正式数据执行后，只有全体总支出落入预设容差，Y1 与住房组的完整综合消费才允许从 `blocked` 升级为 `supported preliminary`。

## 1. 为什么 Round 10 必须单独进行

Round 9 已证明：

```text
Interview 与 Diary 不能连接受访者
→ 两套样本分别定义同一目标人口
→ 每个 UCC 独立估计
→ 按官方来源选择合并
→ 独立样本方差相加
```

食品成功不等于总消费成功。Round 9 的部分整合结果为：

```text
Interview total
- Interview food summary
+ integrated UCC food
= 73,267 USD（all CU）
```

与 BLS 2023 官方总支出 77,280 美元相比仍低约 5.2%。因此完整消费继续处于 `Blocked`。

## 2. 官方输入合同

### 2.1 Integrated Hierarchical Grouping

`CE-HG-Integ-2023.txt` 是本轮的 UCC 级权威输入。BLS 固定宽度字段包括：

| 字段 | 起始位置 | 用途 |
|---|---:|---|
| record type | 1 | 名称首行、续行或评论 |
| level | 4 | 1—9 层级 |
| name | 7 | UCC或聚合名称 |
| UCC | 70 | 六位标识符 |
| source | 83 | `I`、`D`、`G`、`T`、`S` |
| factor | 86 | 年度化乘数 `1` 或 `4` |
| section | 89 | `FOOD`、`EXPEND`等 |

估计器只准入 `source in {I, D}` 且 `section in {FOOD, EXPEND}` 的六位 UCC。相同 UCC 可以因发布层级在文件中重复出现，但只能计入一次；source 或 factor 冲突时立即停止。

### 2.2 Source Selection workbook

`ce_source_integrate.xlsx` 被保存为独立输入证据。首版实现记录：

- SHA-256；
- sheet names；
- 每个 sheet 的有效行列数；
- 非空单元格数。

UCC 级执行仍由 integrated grouping 驱动。除非后续建立 workbook 与 UCC 的机械映射，不能把“成功读取 workbook”描述为 UCC 逐项核验完成。

## 3. 年度化与估计

### 3.1 Interview

Round 9 已将 MTBI 限定到 `REF_YR == 2023` 并通过五个 collection quarters 提供自然年月份。每个准入 UCC 的 `COST` 乘官方 factor，再按 `FINLWT21` 和 Interview population denominator 估计。

### 3.2 Diary

EXPD 是周记录。每个准入 UCC 先乘 13 转换为季度金额，再乘 integrated grouping factor。通常 factor 4 将季度值年度化，但脚本不假定所有 UCC 都是 4，而直接消费官方字段。

### 3.3 分母

```text
Interview population = Σ FINLWT21 / 4 × MO_SCOPE / 3
Diary population     = Σ FINLWT21 / 4
```

### 3.4 合并

对同一群体和指标：

```text
integrated mean = Interview component + Diary component
integrated SE   = sqrt(Interview SE² + Diary SE²)
```

该合并只发生在估计量层面。

## 4. 输出群体

- all consumer units；
- 25—34 岁一人 CU 基准；
- Y1：25—34 岁、一人 CU、至少一名收入者；
- Y1 租户；
- Y1 有按揭住房；
- Y1 无按揭住房；
- Y1 无现金租金。

所有住房组比较均为描述性。无按揭与无现金租金组预期继续受到小样本限制。

## 5. 验证门槛

核心门槛：

```text
abs(PUMD integrated total / 77,280 - 1) <= 1%
```

验证失败时：

- all-CU 状态为 `validation_failed`；
- 所有子群状态为 `blocked_by_all_cu_validation`；
- 脚本非零退出；
- 不产生“青年完整预算已经完成”的研究陈述。

验证通过后：

- all-CU 估计器可标记 `integrated_expenditure_validated`；
- RSE ≤20%的子群可标记 `supported_preliminary_descriptive`；
- RSE 20%—30%仅为探索性；
- RSE >30%或无法形成稳定SE的单元继续阻断。

## 6. 已完成的实现

- 官方固定宽度 grouping parser；
- hierarchy path 与 top category 派生；
- 同 UCC 重复层级去重；
- 冲突 source/factor fail closed；
- source-selection workbook 结构审计；
- Interview 与 Diary UCC 年度化；
- group/category/UCC 三层聚合；
- 44 个 BRR 权重；
- 独立样本方差合并；
- all-CU 77,280 美元准入门；
- 原始文件哈希与样本审计；
- 五个合成合同测试。

本地合成测试结果：

```text
5 passed
```

## 7. 尚未完成

```text
official binary ingestion in current session: blocked
full all-CU execution: not run
77,280 reproduction: not yet demonstrated
Y1 full integrated expenditure: not generated
scientific conclusion: unchanged from Round 9
```

## 8. 下一次执行后的判定

### 路径 A：验证通过

1. 提交聚合输出和输入哈希；
2. 逐类别检查与官方顶层表的差异；
3. 检查 UCC coverage 与零记录项目；
4. 审查 Y1、租户和按揭组 RSE；
5. 将完整消费从 `Blocked` 升级为经过验证的估计器输出；
6. 开始 ITII 收入插补和资本形成研究。

### 路径 B：验证失败

按以下顺序诊断：

1. grouping 固定宽度解析；
2. FOOD/EXPEND 重复 UCC 去重；
3. source 与 factor；
4. Interview target-year months；
5. Diary `×13×factor`；
6. PUBFLAG/PUB_FLAG；
7. 2023 新旧 UCC 的季度过渡；
8. PUMD disclosure adjustment 与官方 confidential table 差异。

不得通过手工补差、缩放到 77,280 或删除不匹配项目来制造通过。

## 9. 研究边界

Round 10 即使成功，也只完成群体完整消费估计。它仍不能回答：

- 个体年度负盈余比例；
- 可自由支配现金；
- 按揭本金形成；
- 流动资产变化；
- 家庭外部转移；
- 住房所有权的因果效果；
- 三国可比的最终盈余。

Round 10 的准确贡献是把美国 Y1 的消费侧从“部分来源整合”推进到“可以由官方 UCC 规则重建并接受外部总量验证”的估计系统。
