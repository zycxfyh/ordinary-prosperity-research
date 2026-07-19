# 美国 CE 微观执行边界：云端下载尝试、失败证据与人工数据接入

> Issue #1 · 第七轮  
> 阶段：真实执行、外部访问边界与数据接入交接  
> 日期：2026-07-20

## 摘要

第七轮尝试把第六轮的美国 Consumer Expenditure Survey 2023 青年原型 Y1 估计器放到 GitHub-hosted runner 上执行。研究过程分别使用 Ubuntu 与 macOS runner，尝试 Python `urllib`、浏览器式 `curl`、自定义 User-Agent、Referer 与重试机制。两类 runner 均能正常拉取 GitHub Actions、安装 Python 与依赖，但 BLS 的两个官方 PUMD ZIP 地址持续返回 HTTP 403。因此，本轮没有取得 respondent-level 文件，也没有生成新的微观估计。

这不是数据不存在：BLS PUMD 页面仍列出 2022 与 2023 CSV Interview 数据包；DataLumos/ICPSR 也保存了相应版本。但 DataLumos 下载要求 Researcher Passport，2022 项目页面还要求申请访问。研究不能绕过账户、访问条款或机构身份要求。

本轮同时核对并修正了执行器中的三组变量映射：税后收入使用 `FINATXEM`，工资薪金使用 `FSALARYM`，交通季度汇总变量使用 `TRANSCQ` 与 `TRANSPQ`。修正已保存为 `analysis/us-ce/round07_ce_y1.py`，但结果状态仍保持 `preliminary_interview_only`。

## 1. 执行路径

临时 Draft PR #2 建立了只读、一次性云端执行路径：

```text
GitHub PR runner
→ 下载 BLS 2022/2023 Interview ZIP
→ 执行 fail-closed Python estimator
→ 只上传 aggregate-only artifact
→ 不提交原始数据或 respondent-level records
```

共执行五次：

1. Ubuntu：`setup-python` 因无 requirements 文件却启用 pip cache 而失败；
2. Ubuntu：环境成功，Python `urllib` 请求 BLS ZIP 返回 403；
3. Ubuntu：增加持久化执行日志，确认 403；
4. Ubuntu：改用浏览器式 `curl`、Referer 和重试，仍返回 403；
5. macOS：相同浏览器式请求仍返回 403。

因此，失败位于外部数据传输层，而不是样本筛选、权重或估计计算层。

## 2. 可信替代源审计

DataLumos 保存了 BLS 原始分发包及其项目元数据：

- 2023 项目 DOI：`10.3886/E247740V1`；
- 2022 项目 DOI：`10.3886/E247744V1`。

但下载入口要求 ICPSR Researcher Passport；2022 页面还将材料标记为需要申请的访问形式。元数据可匿名读取不等于文件可匿名下载。项目不会自动创建账户、代替用户接受条款或保存凭证。

## 3. 当前可执行入口

在普通浏览器中从 BLS PUMD Data Files 页面下载：

```text
intrvw22.zip
intrvw23.zip
```

随后把文件放在：

```text
data/raw/us-ce/intrvw22.zip
data/raw/us-ce/intrvw23.zip
```

运行：

```bash
python analysis/us-ce/round07_ce_y1.py \
  --target-year 2023 \
  --acknowledge-historical-tenure-codes \
  --output-dir data/derived/us-ce/round07
```

原始 ZIP 不进入 Git；只保留来源 URL、下载日期、字节数、SHA-256、BLS版本说明和汇总输出。

## 4. 结果准入门槛

即使脚本成功运行，结果仍不能立即进入论文。至少还需通过：

1. 当前变量字典核对；
2. FMLI 汇总变量与 ITBI/MTBI source-selection 核对；
3. 2023 税后收入和收入插补处理核对；
4. 季度、月份范围和轮换样本去重核对；
5. `FINLWT21` 与 44 个 replicate weights 核对；
6. 与 BLS 2022—2023、2023—2024公开交叉表进行数量级验证；
7. 小样本、RSE、top-code和插补比例审计。

## 5. 第七轮结论

第七轮没有产生可发表的新数字，但完成了三项实质推进：

- 证明现有代码可由云端 runner 启动，并把阻断定位到 BLS 自动下载策略；
- 排除了 Linux、macOS、Python 与浏览器式 `curl`差异；
- 将变量命名错误修正并形成明确的人工数据接入路径。

当前研究状态为：

```text
official data identified
+ estimator implemented
+ cloud execution attempted
+ access boundary evidenced
+ manual intake ready
- microdata not yet ingested
- estimates not yet generated
```

Issue #1继续保持开放。下一项不可替代的输入是两份官方 ZIP，而不是更多抽象方法设计。
