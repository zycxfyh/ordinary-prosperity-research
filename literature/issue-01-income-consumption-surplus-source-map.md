# Issue #1 文献与报告地图：收入如何转化为可支配盈余？

> 阶段：证据搜集 · 2026-07-20  
> 状态：第一轮资料池，尚未进入综合分析

## 1. 搜集目标

本轮围绕以下证据链建立可引用资料池：

```text
市场收入与转移收入
→ 税收和社会缴费
→ 家庭可支配收入
→ 现金消费与实物消费
→ 可支配盈余／家庭储蓄
→ 流动资产、住房权益、养老金与其他资产
```

资料按五类组织：

1. 跨国统计口径与协调数据库；
2. 美国官方报告与调查；
3. 中国官方报告与家庭金融调查；
4. 澳大利亚官方报告与纵向调查；
5. 储蓄、流动性、家庭内部配置和资产参与的机制论文。

本文件仅说明资料的研究用途、口径和限制，不在本阶段判断三国差异由何种机制主导。

---

## 2. 跨国统计框架与数据库

| Citation key | 资料 | 类型 | 可支持的研究任务 | 使用前必须核对 |
|---|---|---|---|---|
| `oecd2013icwframework` | OECD, *Framework for Statistics on the Distribution of Household Income, Consumption and Wealth* | 国际统计框架 | 联合定义收入、消费和财富；确定家庭分析单位；设计跨国指标字典 | 2013框架较早，需与2024手册共同使用 |
| `oecd2024distributionhandbook` | OECD, *Handbook on Household Distributional Results* | 国际统计手册 | 将微观住户数据与国民账户总量衔接；定义调整后可支配收入、实际最终消费和储蓄 | 主要分析单位是家庭；包含社会实物转移时与现金口径不同 |
| `zwijnenburg2021distribution` | Zwijnenburg et al., OECD Statistics Working Paper | 方法与试算结果 | 了解收入—消费—储蓄分布数据的协调步骤与实证可行性 | 2020轮次覆盖国与数据年份不等同于本项目三国最新年份 |
| `lis2025disposablemethod` | LIS Disposable Household Income methodology | 协调微观数据库方法 | 统一税后、转移后家庭收入；使用平方根等价尺度；比较中位数、分位数和贫困线 | LIS通常不计入住房等耐用品的推算服务价值；国家覆盖和年份不齐 |
| `lis2024database` | Luxembourg Income Study Database | 跨国微观数据库 | 取得劳动收入、资本收入、养老金、转移、税费和人口变量的协调数据 | 中国、美国、澳大利亚可用年份与原始调查来源需要逐国核对 |
| `lws2024database` | Luxembourg Wealth Study Database | 跨国财富微观数据库 | 连接收入、流量、金融资产、住房和债务 | 财富参考时点与收入参考年可能不同；各国资产明细不完全一致 |
| `oecd2018taxsavings` | OECD, *Taxation of Household Savings* | 跨国政策报告 | 比较银行存款、股票、养老金和住房的边际有效税率 | 主要反映2016年前后的制度，现行税制需另行更新 |

### 本组资料的功能

这组资料用于建立“可比较的共同语言”，而不是直接提供普通人的最终画像。后续分析必须至少同时保留：

- 现金可支配收入与包含社会实物转移的调整后可支配收入；
- 家庭总量与等价化人均量；
- 平均数、中位数和分位数组；
- 微观调查结果与国民账户总量；
- 储蓄流量与资产负债表存量。

---

## 3. 美国资料

| Citation key | 资料 | 类型 | 主要变量／对象 | 计划用途 | 局限或口径提醒 |
|---|---|---|---|---|---|
| `census2025income2024` | U.S. Census Bureau, *Income in the United States: 2024* | 官方住户收入报告 | 家庭收入、个人收入、收入分布、税后收入估计 | 确定美国收入中位数、收入来源和群体差异 | CPS ASEC“money income”与BEA国民账户收入不同；高收入和部分非现金收入覆盖有限 |
| `bls2025ce2024` | BLS, *Consumer Expenditures—2024* | 官方消费调查 | 消费单元收入、总支出、住房、交通、食品、保险与养老金 | 建立消费结构和收入分位支出表 | 发布值多为均值；“consumer unit”不完全等于Census household；2024税后收入模型存在更新限制 |
| `bea2026distribution` | BEA, *Distribution of Personal Income* | 分布国民账户 | 个人收入、税后个人收入、消费与储蓄分布 | 衔接微观分布与NIPA总量；观察可支配收入和消费的联合分布 | 2024为暂定／实验估计；与CPS、CE的家庭定义不同 |
| `fed2026shed` | Federal Reserve, *Economic Well-Being of U.S. Households in 2025* | 全国成人调查 | 月末余额、应急储蓄、账单困难、意外支出、住房、信用 | 测量“有无盈余”与流动性韧性，而非只看年度收入 | 自报调查；对象是成年人及其家庭，不等于完整家庭资产负债表 |
| `fed2023scf` | Federal Reserve, *2022 Survey of Consumer Finances* | 家庭资产负债调查 | 收入、资产、债务、净值、养老金和金融参与 | 连接收入盈余与资产所有；按年龄、收入和财富分组 | 财富高度偏斜，必须同时使用均值和中位数；最晚完整波次为2022 |
| `cbo2026income2022` | CBO, *The Distribution of Household Income, 2022* | 税收与转移分布报告 | 市场收入、社会保险、经经济状况调查的转移、联邦税 | 分解税前收入如何变为转移税后收入 | 数据年份滞后；CBO收入定义、家庭规模调整和资本利得处理需单独记录 |

### 美国数据之间的预定分工

- Census：人口与收入分布基线；
- BLS CE：支出结构与消费单元特征；
- BEA：宏观一致的可支配收入、消费与储蓄分布；
- SHED：月度预算余量、意外支出和流动性困难；
- SCF：资产负债表、净值和资产参与；
- CBO：税收与转移制度如何改变家庭资源。

这些资料不能直接横向拼接为同一个“平均家庭”，后续需要统一调查单位、年份、价格基期和家庭规模。

---

## 4. 中国资料

| Citation key | 资料 | 类型 | 主要变量／对象 | 计划用途 | 局限或口径提醒 |
|---|---|---|---|---|---|
| `nbs2026income2025` | 国家统计局，《2025年居民收入和消费支出情况》 | 官方年度住户调查 | 人均可支配收入及中位数、收入来源、八类消费、城乡分组 | 建立中国全国和城乡收入—消费基线 | 人均均值不能直接代表家庭；全国、城镇和特定年龄教育群体需分开 |
| `nbs2024disposablemethod` | 国家统计局，《居民人均可支配收入的计算方法》 | 官方方法说明 | 工资、经营、财产和转移净收入；16万户抽样 | 记录中国可支配收入定义、抽样和汇总方法 | 与OECD调整后可支配收入、美国money income并非完全同口径 |
| `nbs2025householdsource` | 国家统计局，《居民人均可支配收入的基础数据来源》 | 官方调查设计 | 调查对象、样本设计、误差目标和数据质量 | 评估住户调查代表性与抽样误差 | 公开聚合数据不足以直接分析细粒度家庭异质性 |
| `chfs2025sixthreport` | 中国家庭金融调查与研究中心，《中国家庭金融调查（第六轮）研究报告》 | 全国微观调查研究报告 | 就业、收入支出、住房、金融资产、负债、保险和社会保障 | 连接收入、消费、住房和家庭资产负债表 | 报告与微观数据的具体调查年份、样本权重和口径需查阅正文 |
| `chfs2026data2021` | CHFS 2021公开数据发布 | 微观数据资源 | 家庭金融、收入、支出、资产、债务与人口就业 | 为后续可重复的家庭层面分析准备数据入口 | 数据申请、变量缺失、权重和跨波次一致性需要审查 |
| `pboc2020urbanbalance` | 中国人民银行调查统计司课题组，《2019年中国城镇居民家庭资产负债情况调查》 | 城镇家庭资产负债调查 | 房产、金融资产、负债、偿债和财富分布 | 补充城镇家庭住房集中度、债务与金融资产结构 | 仅覆盖城镇、单次调查且年份较早；目前登记页面为《中国金融》转载入口，后续应寻找正式原刊 |

### 中国数据之间的预定分工

- 国家统计局住户调查：全国收入与消费基线；
- CHFS：家庭资产负债表和微观异质性；
- 人民银行城镇调查：住房、金融资产和负债结构的独立交叉验证。

后续必须分别处理城乡、地区、家庭规模、住房持有、户籍、就业形态和年龄结构，不能由全国人均值直接推出“典型年轻劳动者”的盈余。

---

## 5. 澳大利亚资料

| Citation key | 资料 | 类型 | 主要变量／对象 | 计划用途 | 局限或口径提醒 |
|---|---|---|---|---|---|
| `abs2022sihincome` | ABS, *Survey of Income and Housing User Guide: Income* | 官方调查方法 | 私人收入、政府现金福利、税后收入、等价化收入、社会实物转移 | 建立澳大利亚收入概念层级和家庭规模调整方法 | 最近完整SIH公开周期较旧；“final income”依赖HES联合调查 |
| `abs2017hesmethod` | ABS, *Household Expenditure Survey 2015–16 Methodology* | 官方消费调查方法 | 家庭支出、收入、财富、住房成本和消费日记 | 构建澳大利亚支出分类和家庭单位定义 | HES每六年一次，现有完整数据较旧；疫情后价格结构变化需用其他资料更新 |
| `abs2025savingmethod` | ABS, *Australian National Accounts Methodology: Household Saving Ratio* | 国民账户方法 | 家庭净储蓄、净可支配收入和最终消费 | 提供宏观家庭储蓄率定义与时间序列口径 | 宏观家庭部门含义不能替代住户分布分析 |
| `hilda2025report` | Melbourne Institute, *HILDA Statistical Report 2025* | 全国纵向住户调查报告 | 家庭经济福祉、劳动、家庭生活、收入和财富 | 观察同一家庭和个人随时间变化的轨迹 | 报告选择性展示主题；严格分析需申请微观数据并处理面板流失 |
| `rba2020wealth` | RBA, *Household Wealth prior to COVID-19* | 中央银行研究报告 | HILDA资产、债务、流动性与三个月支出缓冲 | 连接净值、流动资产和收入冲击韧性 | 使用2018波次，疫情后资产价格和债务环境已变化 |
| `treasury2020rir` | Australian Treasury, *Retirement Income Review* | 独立制度评估 | Age Pension、强制superannuation、自愿储蓄和住房 | 研究制度性储蓄如何改变私人可支配资源和退休资产 | 主体聚焦退休；不能直接代表青年和中年家庭全部盈余 |
| `ruthbahpham2020super` | Ruthbah & Pham, *Household Savings and the Superannuation Guarantee* | Treasury委托研究 | 强制养老金与其他家庭储蓄的替代／新增关系 | 评估制度性储蓄是否等量增加家庭总储蓄 | 需阅读全文确认识别设计、样本和外推范围 |

### 澳大利亚数据之间的预定分工

- SIH/HES：收入、消费、财富和住房成本的横截面；
- HILDA：个体与家庭的纵向转变；
- ABS国民账户：宏观储蓄率；
- RBA：资产负债表与金融稳定；
- Treasury：强制养老金和退休制度。

---

## 6. 机制论文

### 6.1 流动性约束与预防性储蓄

| Citation key | 论文 | 研究用途 | 当前登记状态 |
|---|---|---|---|
| `deaton1991saving` | Deaton, “Saving and Liquidity Constraints” | 理解无法借款时，资产如何作为收入冲击缓冲库存 | 已核对摘要与正式发表信息；待读全文 |
| `carrollsamwick1998precautionary` | Carroll & Samwick, “How Important is Precautionary Saving?” | 研究收入不确定性与财富持有之间的经验关系 | 已核对NBER摘要和期刊信息；待读全文与识别限制 |
| `athreya2025distress` | Athreya et al., “Effects of Macroeconomic Shocks: Household Financial Distress Matters” | 研究危机前资产负债表健康如何改变冲击后的消费响应 | 已核对期刊摘要；待读模型与数据附录 |
| `rohwedder2026savingregret` | Rohwedder, Hurd & Börsch-Supan, “Self-assessed Life-Cycle Saving Behavior…” | 区分储蓄不足中的拖延解释与经济冲击解释 | 2026 NBER工作论文；尚未同行评审定稿 |

### 6.2 流动资产、非流动资产与“有财富但无现金”

| Citation key | 论文 | 研究用途 | 当前登记状态 |
|---|---|---|---|
| `kaplanviolanteweidner2014` | Kaplan, Violante & Weidner, “The Wealthy Hand-to-Mouth” | 区分净值与流动性；比较八国低流动财富家庭 | 已核对NBER与Brookings发表信息；待读跨国样本附录 |
| `campbell2006householdfinance` | Campbell, “Household Finance” | 建立家庭资产参与、分散、抵押贷款和金融错误的研究地图 | 综述／主席演讲；用于领域框架，不作为单一因果证据 |
| `vissing2002participation` | Vissing-Jørgensen, “Portfolio Choice Heterogeneity…” | 研究金融市场参与成本、劳动收入与资产参与 | NBER工作论文；需核对正式发表版本和估计假设 |

### 6.3 家庭内部资源分配

| Citation key | 论文 | 研究用途 | 当前登记状态 |
|---|---|---|---|
| `liseSeitz2011intrahousehold` | Lise & Seitz, “Consumption Inequality and Intra-household Allocations” | 说明家庭等价尺度可能掩盖成员间消费差异 | 已核对ReStud摘要；英国历史数据，外推三国需谨慎 |

### 6.4 中国高储蓄的竞争解释

| Citation key | 论文 | 研究用途 | 当前登记状态 |
|---|---|---|---|
| `chamonprasad2010china` | Chamon & Prasad, “Why Are Saving Rates of Urban Households in China Rising?” | 住房、教育、医疗、借贷约束和预防性动机候选机制 | 1995–2005城镇数据；用于历史机制而非当前水平 |
| `chamonliuprasad2013` | Chamon, Liu & Prasad, “Income Uncertainty and Household Savings in China” | 收入暂时性风险和养老金改革的储蓄机制 | 数据至2006；需与当前劳动市场和社保制度重新校准 |
| `weizhang2011competitive` | Wei & Zhang, “The Competitive Saving Motive” | 婚配市场和社会竞争如何影响家庭储蓄 | 强机制主张；需审查识别、替代解释和时代适用性 |
| `chenetal2018longtermcare` | Chen et al., “The Chinese Saving Rate: Long-term Care Risks…” | 老年照护风险、家庭保险和人口结构 | 结构模型结果；需区分模型拟合与直接因果识别 |

---

## 7. 全文阅读优先级

### A级：第二步分析前必须精读

1. OECD 2024分布统计手册；
2. 三国核心官方住户调查的方法文件；
3. 美国Census、BLS CE、BEA分布数据、SCF与SHED；
4. 中国国家统计局住户调查、CHFS研究报告；
5. 澳大利亚SIH/HES、HILDA 2025报告；
6. Deaton；Carroll & Samwick；Kaplan–Violante–Weidner；Campbell；
7. Chamon–Prasad与Chamon–Liu–Prasad。

### B级：用于机制竞争与反例

1. CBO税收转移分布；
2. 澳大利亚退休收入审查及强制super研究；
3. Lise–Seitz家庭内部配置；
4. Wei–Zhang婚配竞争储蓄；
5. 中国长期照护风险模型；
6. Athreya等金融困境研究；
7. Rohwedder等储蓄后悔研究。

### C级：后续扩展

- 各国内部地区生活成本；
- 住房租买与财富形成；
- 教育回报与学生债务；
- 医疗、育儿和长期照护支出；
- 移民身份与制度资格；
- 性别、家庭分工和经济自主。

---

## 8. 下一步分析前的资料缺口

以下缺口暂不以推断填补：

1. 中国CHFS第六轮报告的完整书目、调查年份、样本规模和变量定义；
2. 中国人民银行2019城镇家庭资产负债调查的正式原刊或机构PDF；
3. 澳大利亚2025 HILDA报告中与家庭经济福祉直接相关章节的逐表阅读；
4. 三个国家可落在相近年份的税后等价化家庭收入、实际消费和储蓄分布；
5. 三国青年／初入劳动力市场人群的统一年龄和家庭状态样本；
6. 住房本金偿还、养老金缴费和耐用品购买应如何在“消费—储蓄”之间分类；
7. 社会实物转移在三国比较中的估值方法。

完成这些核对后，第二步才能开始构建三国收入向可支配盈余转换的比较分析。
