# Issue #1 第五轮断言—来源映射

> 主题：原型 Y 微观数据访问、分析单位与提取协议  
> 日期：2026-07-20

## 1. 分析单位修正

| 断言 | Citation key | 证据性质 | 限制 |
|---|---|---|---|
| CE consumer unit可以是独居者、与他人同住但经济独立者，或共同承担主要支出的多成员单位 | `bls2026glossary` | 官方定义 | 不能由一人CU自动推出住宅中只有一人 |
| HILDA没有预设唯一家庭参考人，研究者应围绕研究问题自行定义 | `hilda2026faq` | 官方FAQ | 需要在程序中显式记录焦点个人规则 |

## 2. 美国CE

| 断言 | Citation key | 证据性质 | 限制 |
|---|---|---|---|
| 2024 PUMD公开提供SAS、Stata和CSV，Interview CSV包约52.4MB | `bls2026pumddata` | 官方数据页 | 本轮运行环境未成功摄取二进制ZIP |
| FMLI、MEMI、ITBI、MTBI等文件通过NEWID关联 | `bls2026pumdguide` | 官方方法文档 | 具体人口变量需依年度dictionary确认 |
| 自2020年起需结合前一年和当前年度包构造完整日历年 | `bls2026pumddata`; `bls2026pumdguide` | 官方方法文档 | 必须处理Q1及下一年Q1回溯月份 |
| 代表性估计使用FINLWT21并调整季度数和月份范围 | `bls2026pumdguide` | 官方估计方法 | 不调整会高估总体规模或误配月份 |
| 标准误使用WTREP01—WTREP44进行BRR | `bls2026pumdguide` | 官方估计方法 | 普通BRR公式不适用于插补收入标准误 |
| 2024 CE不再提供税负和税后收入 | `bls2026aftertax`; `bls2026faq` | 官方方法变化 | 2024税后结果必须自行估税或不发布 |
| FMLI收入汇总变量不一定直接等同于正式表格定义 | `bls2026faq` | 官方FAQ | 应以ITBI/UCC及定义复核 |

## 3. 中国CHFS

| 断言 | Citation key | 证据性质 | 限制 |
|---|---|---|---|
| CHFS 2021需实名注册、申请审核后下载 | `chfs2026public2021` | 官方数据发布 | 自动化代理不能代替用户身份申请 |
| 2021样本22,027户、覆盖29省级地区和269区县，约70%于2021完成 | `chfs2026public2021` | 官方数据发布 | 需要记录2021/2022实际调查月份和价格处理 |
| 2026年7月更新后每轮含hh、ind、master_hh和master_ind四类文件 | `chfs2026update` | 官方更新公告 | 后续应锁定更新版并保存校验信息 |

## 4. 澳大利亚HILDA

| 断言 | Citation key | 证据性质 | 限制 |
|---|---|---|---|
| HILDA Release 24通过DSS Dataverse申请 | `hilda2026datausers`; `dss2024dataaccess` | 官方访问规则 | 需要机构身份及批准 |
| General Release可供海外研究人员，Restricted Release只向符合条件的澳大利亚用户开放 | `dss2024dataaccess` | 官方访问规则 | General Release部分变量可能top-code或变换 |
| 申请通常需要机构邮箱、在线请求和保密承诺 | `dss2024dataaccess` | 官方访问规则 | 不能由代理代签 |
| User Manual涵盖插补、匹配、权重和数据质量 | `hilda2026manual` | 官方方法文档 | 具体变量仍需通过cross-wave index确认 |
| Program Library提供文件匹配、纵向构造、权重和税收福利模型程序 | `hilda2026programlibrary` | 官方程序资源 | 程序需按Release 24和本研究变量调整 |

## 5. 本轮结论成熟度

| 结论 | 等级 | 说明 |
|---|---|---|
| 必须分开焦点个人、住宅家庭与经济共享单位 | 强 | 三个调查的单位定义不一致，且共同居住会导致逻辑冲突 |
| 美国严格税后主估计应优先采用2023 | 强 | 2024 CE官方不提供税负和税后收入 |
| CHFS和HILDA在数据结构上可构造Y1/Y2/Y3 | 中强 | 官方文件结构支持，但尚未执行用户授权下载和变量映射 |
| 当前已经得到三国同口径微观估计 | 不成立 | 本轮完成的是访问与执行协议，不是估计结果 |
