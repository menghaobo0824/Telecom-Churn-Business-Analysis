# FineBI 看板：现状、口径与待办

本目录用于存放 FineBI 工程文件与看板说明。仪表板截图统一放在 `docs/figures/`。

> **逐条 SQL 的组件配置手册见 [`dashboard_spec.md`](dashboard_spec.md)** ——
> 15 个组件的图表类型、维度/指标、聚合方式、筛选、排序、标签格式都写在里面，照着拖即可。

---

## 1. 现有看板与截图对应关系

| 看板 | 截图 | 核心指标 | 对应 SQL |
|---|---|---|---|
| 留存悬崖 | `docs/figures/fig_bi_tenure_churn_curve.png` | 按在网月数的流失率 | Q04 |
| 高危组合矩阵 | `docs/figures/fig_bi_contract_payment_matrix.png` | 合同 × 支付 流失率 | Q09 |
| 流失金额 | `docs/figures/fig_bi_mrr_loss.png` | MRR 损失（元） | Q11 |
| 高价值名单 | `docs/figures/fig_bi_high_value_list.png` | 流失用户消费 Top 名单 | Q13 |
| 营收集中度 | `docs/figures/fig_bi_pareto_curve.png` | 累计营收占比 | Q12 |

---

## 2. 指标口径（务必与 SQL 一致）

| 指标 | 计算方式 | 注意 |
|---|---|---|
| 流失率 | `AVG(Churn)`，Churn 为 0/1 | 不要用「流失人数 / 总人数」再取整，会丢精度 |
| MRR 损失 | `SUM(MonthlyCharges) WHERE Churn = 1` | 单位：元/月，年化再 × 12 |
| 客单价对比 | 流失组 vs 留存组的 `AVG(MonthlyCharges)` | 用于证明"高价值客户先走" |
| 累计营收占比 | `SUM(TotalCharges) OVER(ORDER BY TotalCharges DESC) / SUM(TotalCharges) OVER()` | **已经是比例，乘 100 后 0.53 表示 0.53%** |
| 高价值名单 | `RANK() OVER(PARTITION BY Contract ORDER BY TotalCharges DESC) <= 3` | 每类合同各取 3 人，共 9 人 |

> ⚠️ **报告里的 53% 就是在这里出错的**：SQL 输出的 `累计营收占比` 已经 ×100，
> 第 10 名用户的 0.53 是 **0.53%**，不是 53%。正确结论见根目录 README 的「勘误」。

---

## 3. 还需要在 FineBI 做的事（按优先级）

### P0：修正「营收集中度」看板（当前结论有误）

1. 新建计算字段 **用户百分位**：`PERCENT_RANK() OVER(ORDER BY TotalCharges DESC)`，
   或直接用 `排名 / 总人数`。
2. X 轴放 **用户百分位（0–100%）**，Y 轴放 **累计营收占比（0–100%）**——
   现在这张图 X 轴是用户名，Y 轴只到 0.53，读者会误读成 53%。
3. 在曲线上标注三个点：Top 10%（30.79%）、Top 20%（53.63%）、80% 营收对应 38.4% 用户。
4. 标题改为：**「Top 20% 用户贡献 53.6% 营收，比经典 80/20 更平缓」**。
5. 导出 PNG 覆盖 `docs/figures/fig_bi_pareto_curve.png`。

### P1：新增「流失总览」页（面试官第一眼看这页）

- 4 个 KPI 卡：用户总数 7,043 / 流失率 26.54% / 月度 MRR 损失 139,130.85 元 / 待挽留名单数
- 1 条按在网月数的流失率折线（对应留存悬崖）
- 1 个合同类型的流失率柱状（月付 vs 一年 vs 两年）

### P2：把「高危组合矩阵」做成热力图

- 行：合同类型；列：支付方式
- 颜色：流失率；**单元格标签同时显示样本量**（避免 7 人的格子被当成结论）
- 加筛选：样本量 ≥ 100（对应 SQL 的 `HAVING`）

### P3：新增「挽留名单」明细表（可直接给电销）

| 字段 | 说明 |
|---|---|
| customerID | 用户 ID |
| Contract / PaymentMethod | 合同、支付方式 |
| tenure / MonthlyCharges | 在网月数、月租 |
| TotalCharges | 历史总消费 |
| risk_score | 模型预测的流失概率（来自 `src/ml_churn.py` 输出） |
| priority | 价值 × 风险的优先级 |

- 支持按合同、支付方式筛选
- 支持导出 Excel，字段顺序与电销系统对齐

### P4：全局交互

- 顶部筛选器：合同、支付方式、网络类型、生命周期（联动全页）
- 点击某个柱子 → 下钻到名单明细（FineBI 的「跳转」功能）
- 设置「刷新时间」与「数据更新时间」提示

---

## 4. 工程文件存放

若要把 FineBI 工程文件放进仓库：

```
finebi/
├── README.md                 # 本文件
├── churn_dashboard.fbi       # 仪表板工程文件（可选，需注明 FineBI 版本）
└── export/
    └── churn_dashboard.pdf   # 仪表板导出的 PDF（可选）
```

- 大文件（> 20 MB）不要直接提交，超过 GitHub 单文件 100 MB 限制会推不上去
- 截图建议 PNG、宽度 ≥ 1200px，命名统一 `fig_bi_<主题>.png`

---

## 5. 复现步骤

1. 在 MySQL 中执行 `src/clean.py` 建好的 `data` 表
2. FineBI → 新建数据连接（MySQL）→ 选 `data` 表
3. 按第 2 节的指标口径建计算字段
4. 按第 3 节搭 4 个看板 → 导出 PNG → 替换 `docs/figures/` 下同名文件
5. 提交前检查：截图里的数字与 `sql/` 查询结果、`notebooks/02_churn_drivers.ipynb` 三者一致
