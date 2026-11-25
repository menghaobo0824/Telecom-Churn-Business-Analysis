# 电信用户流失归因与挽留策略分析

> 一个从 **SQL 诊断 → 财务量化 → 机器学习预测 → A/B 实验验证** 的完整数据分析项目。
> 用 7,043 名电信用户的真实样本，回答一个业务问题：**有限的挽留预算，应该花在谁身上？**

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3%2B-F7931E?logo=scikitlearn&logoColor=white)
![SQL](https://img.shields.io/badge/SQL-15%20queries-336791)
![License](https://img.shields.io/badge/License-MIT-green)
![pipeline](https://github.com/menghaobo0824/Telecom-Churn-Business-Analysis/actions/workflows/ci.yml/badge.svg)

---

## 核心结论（TL;DR）

| # | 发现 | 关键数字 |
|---|---|---|
| 1 | **留存悬崖**：流失集中在入网前 6 个月 | 0–6 个月流失率 **52.94%**，首月 **62%**；2 年以上仅 14.04% |
| 2 | **高危组合**：月付 + 电子支票 | 流失率 **53.73%**，占 26.3% 用户却贡献 **53.2%** 流失人数 |
| 3 | **财务失血**：流失是可对账的现金流 | 每月损失 **139,130.85 元**，年化约 **167 万元**；流失用户月租比留存高 **21.5%** |
| 4 | **高价值名单**：最贵的流失不在长期合同 | One year 榜首 **8,684.8 元**，高于 Two year 的 7,856 元 |
| 5 | **长尾结构**：营收比 80/20 更平缓 | 80% 营收需 **38.4%** 用户；Top 20% 贡献 **53.6%**；头部单人价值是均值的 **3.8 倍** |

> 一句话：流失不是"人慢慢变少"，而是"新人在头半年成批走掉，走的时候还比留下的人更贵"。

---

## 1. 业务问题

电信行业进入存量竞争：新增成本高企，样本整体流失率 **26.54%**（每 4 个用户走 1 个），
而挽留一个存量用户的成本通常只有获取新用户的 1/5。

于是问题被拆成四层，每一层对应一种分析方法：

| 层次 | 业务问题 | 方法 | 产物 |
|---|---|---|---|
| ① 分层 | 流失发生在哪个阶段？ | `CASE WHEN` 分箱 + `AVG(Churn)` | 发现一 |
| ② 归因 | 哪些特征叠加最危险？ | `GROUP BY` 交叉 + `HAVING` 过滤小样本 | 发现二 |
| ③ 量化 | 流失到底值多少钱？ | `WHERE Churn=1` + `SUM/AVG` | 发现三 |
| ④ 定位 | 先救谁、救多少人？ | `RANK() / SUM() OVER` 窗口函数 | 发现四、五 |

分析链路：

```mermaid
flowchart LR
    A["原始 CSV<br/>7,043 × 21"] --> B["clean.py<br/>清洗 / 回填 / IQR 封顶"]
    B --> C[("MySQL<br/>data 表")]
    C --> D["15 条 SQL<br/>分层·归因·量化·排序"]
    D --> E["BI 看板<br/>FineBI"]
    C --> F["ml_churn.py<br/>流失概率预测"]
    F --> G["高价值名单<br/>阈值与收益曲线"]
    D --> H["abtest_analysis.py<br/>功效分析·假设检验·分层"]
    G --> H
    H --> I["挽留策略<br/>落地与复盘"]
```

---

## 2. SQL：15 条脚本覆盖 6 类分析能力

全部脚本在 [`sql/`](sql/) 目录，逐条带业务注释，索引见 [`sql/README.md`](sql/README.md)。

| 能力 | 脚本 |
|---|---|
| 聚合铺底 | `01` 大盘、`02` 人群切片 |
| 多表关联 / CTE | `02`、`07` 服务组合、`14` 高危画像 |
| 窗口函数 | `03` `PARTITION BY`、`05` `LAG`、`08` `ROW_NUMBER`、`10` `RANK`、`12` `NTILE`、`13` `DENSE_RANK`、`15` `LEAD` |
| 自连接基准 | `06` 高于同类均值的流失用户 |
| 小样本防护 | `09` `HAVING COUNT(*) > 100` |
| 财务口径 | `11` MRR 损失、`12` 帕累托分层 |

示例（Q04 留存悬崖）：

```sql
SELECT
    CASE
        WHEN tenure <= 6  THEN '1. 0-6个月'
        WHEN tenure <= 12 THEN '2. 6-12个月'
        WHEN tenure <= 24 THEN '3. 1-2年'
        ELSE '4. 2年以上'
    END AS lifecycle_stage,
    COUNT(*) AS total_users,
    ROUND(AVG(Churn) * 100, 2) AS churn_rate_pct
FROM data
GROUP BY lifecycle_stage
ORDER BY lifecycle_stage;
```

| 阶段 | 用户数 | 流失人数 | 流失率 |
|---|---|---|---|
| 0–6 个月 | 1,481 | 784 | **52.94%** |
| 6–12 个月 | 705 | 253 | 35.89% |
| 1–2 年 | 1,024 | 294 | 28.71% |
| 2 年以上 | 3,833 | 538 | 14.04% |

---

## 3. 机器学习：从"谁会流失"到"先救谁"

`sql` 回答因果线索，模型回答**排序**：把 7,043 人按流失概率排队，让有限的客服人力先打最值钱的那通电话。

| 环节 | 做法 |
|---|---|
| 特征 | 原始 21 列 + 4 个派生特征：`service_count`（增值服务数）、`avg_monthly`（累计消费/在网月数）、`is_new`（≤6 月）、`charge_ratio`（当前月租/历史均值） |
| 预处理 | `ColumnTransformer`：数值 → 中位数填补 + 标准化；类别 → `OneHotEncoder(handle_unknown="ignore", min_frequency=20)` |
| 模型 | LogisticRegression（`class_weight=balanced`，基线）/ RandomForest / HistGradientBoosting |
| 评估 | 5 折分层 CV，指标 `ROC-AUC`、`PR-AUC`（类别不平衡更看 PR-AUC）、`F1` |
| 阈值 | 不用 0.5，而是**按业务收益寻优**：`收益 = TP × (ARPU×12×35% − 20元) − FP × 20元` |
| 解释 | 留出集上的置换重要性（permutation importance），输出 Top-12 特征 |

```bash
python src/ml_churn.py                       # 自动找 data/telco.csv
python src/ml_churn.py --data data/telco.csv --out results
```

输出：`metrics.json`、`model_comparison.csv`、`feature_importance.csv`、
`fig_roc.png`、`fig_pr.png`、`fig_importance.png`、`fig_threshold_profit.png`、`best_model.joblib`。

> 指标不写死在本文件里——请在自己下载的数据上运行后查看 `results/metrics.json`，
> 避免把"纸面参数"当成结论。

---

## 4. A/B 实验：把策略从"看起来有用"变成"可验证"

设计文档见 [`experiments/abtest_design.md`](experiments/abtest_design.md)，代码 `src/abtest_analysis.py`。

- **假设**：新客护航（第 7/30/60/90 天四次触达）能压低 0–6 个月流失率
- **功效分析**：基线 52.94%、MDE 4pp、α=0.05、power=0.8 → **每组 2,451 人**
- **分析**：双样本比例 z 检验 + Wald / 自助法置信区间 + NNT + SRM 检查 + 合同分层
- **决策规则**：显著为正且护栏不恶化才全量，否则重测或放弃

模拟跑出的结果（**模拟数据，仅演示统计口径**）：

| 指标 | 结果 |
|---|---|
| 对照 / 实验流失率 | 52.59% / 47.16% |
| 绝对提升 | **−5.43 pp**（95% CI −8.22 ~ −2.63） |
| 相对提升 | −10.32%（95% CI −15.63 ~ −5.00） |
| p 值 | 0.0001 |
| NNT | 18.4 |

```bash
python src/abtest_analysis.py
```

---

## 5. 仓库结构

```
telecom-churn-analysis/
├── sql/                     # 15 条 SQL（按 Part 1-6 分组）
│   ├── 01_overall_churn_overview.sql
│   ├── ...
│   └── 15_lead_value_tracking.sql
├── src/
│   ├── clean.py             # 清洗 + IQR 封顶 + 可选写入 MySQL
│   ├── make_demo_data.py    # 生成同构演示数据（无原始数据时跑通流水线）
│   ├── ml_churn.py          # 三模型训练 / 评估 / 阈值寻优 / 解释
│   └── abtest_analysis.py   # 功效分析 / z 检验 / CI / 分层
├── notebooks/               # 逐步分析（前两个已带执行结果，可直接在 GitHub 阅读）
│   ├── 01_data_overview.ipynb    # 数据概览：缺失、类型、分布、类别不平衡
│   ├── 02_churn_drivers.ipynb    # 用 pandas 复现报告的五条结论
│   └── 03_modeling.ipynb         # 特征工程 → 三模型 → 阈值寻优 → 解释
├── experiments/
│   └── abtest_design.md     # 实验设计（指标、样本量、决策规则）
├── finebi/
│   ├── README.md            # 看板口径、待修正项与复现步骤
│   └── dashboard_spec.md    # 15 个组件的逐条配置手册
├── docs/
│   ├── report.pdf           # 完整分析报告（13 页）
│   └── figures/             # SQL 结果与 BI 看板截图
├── data/                    # telco.csv（7,043 行原始数据）+ 字段说明
├── results/                 # 运行产物（git 忽略）
└── .github/workflows/
    ├── ci.yml               # 推送即跑：SQL 校验 + 清洗 + A/B 分析
    └── ml.yml               # 手动触发：模型训练与图表产出
```

---

## 6. 快速开始

```bash
# 1) 依赖
pip install -r requirements.txt

# 2) 数据：仓库已内置 data/telco.csv（7,043 行 × 21 列），可直接使用
#    也可以生成同构的合成数据来跑通流水线（不需要真实数据）：
python src/make_demo_data.py

# 3) 清洗
python src/clean.py --data data/telco.csv --out data/telco_clean.csv

# 4) SQL（可选：写入 MySQL 后逐条执行 sql/*.sql）
export MYSQL_URL="mysql+pymysql://root:pass@localhost:3306/churn?charset=utf8mb4"
python src/clean.py --data data/telco.csv --load-mysql

# 5) 建模与实验
python src/ml_churn.py
python src/abtest_analysis.py
```

Windows PowerShell 设置环境变量：

```powershell
$env:MYSQL_URL = "mysql+pymysql://root:pass@localhost:3306/churn?charset=utf8mb4"
```

---

## 7. 图表

| 留存悬崖 | 合同 × 支付矩阵 |
|---|---|
| ![tenure](docs/figures/fig_bi_tenure_churn_curve.png) | ![matrix](docs/figures/fig_bi_contract_payment_matrix.png) |

| 流失月租损失 | 营收集中度 |
|---|---|
| ![mrr](docs/figures/fig_bi_mrr_loss.png) | ![top](docs/figures/fig_bi_high_value_list.png) |

完整分析见 [`docs/report.pdf`](docs/report.pdf)。

---

## 8. 工程约定

- **口径统一**：`Churn` 为 0/1，`AVG(Churn)` 即流失率；金额单位统一为元
- **小样本防护**：所有交叉分析加 `HAVING COUNT(*) > 100`，避免长尾格子带偏结论
- **不删样本**：清洗只做回填与封顶（winsorize），保证 7,043 人的口径与报告一致
- **可复现**：随机种子固定；CI 每次推送都用数据跑通全链路
- **诚实标注**：演示数据 / 模拟实验在文档与代码注释中都明确标注
- **CI 范围**：推送时校验 15 条 SQL 的结构、清洗管线与 A/B 分析；模型训练耗时较长，
  改为手动触发（`Actions → ml → Run workflow`），避免每次提交都排队等训练

## 9. Roadmap

- [ ] 引入 SHAP 做单用户级别解释，接入客服工作台
- [ ] 生存分析（Kaplan-Meier / Cox）估计剩余生命周期，替代固定 12 个月假设
- [ ] 增益模型（Uplift Modeling）区分"自然留存"与"被挽留"，避免预算浪费
- [ ] SQL 增加 data quality 检查脚本（空值率、枚举域、主键唯一性）

## 10. 勘误（重要）

早期版本把 Q12 的 `累计营收占比` 字段读错了单位：该字段已经 `× 100`，
**`0.53` 表示 0.53%，不是 53%**。按全部 7,043 名用户重算：

| 口径 | 正确值 |
|---|---|
| Top 10 名用户占营收 | **0.53%**（单人最高 0.054%） |
| Top 1% 用户（70 人） | 3.62% |
| Top 10% 用户（704 人） | **30.79%** |
| Top 20% 用户（1,408 人） | **53.63%** |
| 覆盖 80% 营所需用户数 | **2,702 人（38.4%）** |

因此结论从"头部极端集中"修正为"**比经典 80/20 更平缓的长尾结构**"：
80% 营收需要 38.4% 的用户，而不是 20%。但这不削弱"名单制"建议——
头部单人价值 8,684.8 元是均值 2,279.7 元的 **3.8 倍**，流失一个头部用户等于流失近 4 个普通用户。

`docs/report.pdf` 为初版报告，其中"发现五"的百分比标题尚未更新；
正确口径以上表与 `notebooks/02_churn_drivers.ipynb` 为准。

## 11. 数据与许可

- 代码：[MIT License](LICENSE)
- 数据：**Telco Customer Churn**（IBM Sample Data Sets），版权归数据提供方，
  仓库内置原始文件仅用于复现，请遵循 [data/README.md](data/README.md) 中的许可说明
- 报告与图表：个人分析作品，欢迎在注明出处的前提下引用
