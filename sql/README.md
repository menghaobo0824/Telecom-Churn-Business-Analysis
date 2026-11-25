# SQL 分析脚本（15 条）

全部脚本基于 MySQL 8.0 编写，统一从 `data` 表读取（字段与公开 Telco Churn 数据集一致）。
执行前请先运行 `src/clean.py` 完成清洗入库，或直接导入同名字段的数据表。

> 约定：`Churn` 为 0/1 数值型，`AVG(Churn)` 即流失率；`TotalCharges`、`MonthlyCharges` 为数值型。

## 目录

| 编号 | 脚本 | 业务目的 |
|---|---|---|
| Q01 | [整体流失大盘](01_overall_churn_overview.sql) | 全量用户规模、流失人数与流失率 |
| Q02 | [用户画像 JOIN 流失](02_demographics_join.sql) | 老年 / 有伴侣群体的流失差异 |
| Q03 | [性别内合同流失占比](03_contract_share_by_gender.sql) | 窗口函数 PARTITION BY |
| Q04 | [留存悬崖（生命周期）](04_retention_cliff_lifecycle.sql) | 0-6 个月新人期流失率最高 |
| Q05 | [合同阶梯与 LAG 环比](05_contract_ladder_lag.sql) | 合同期延长带来的流失率降幅 |
| Q06 | [高客单价流失名单（SELF JOIN）](06_high_value_self_join.sql) | 月租高于同合同均值的流失用户 |
| Q07 | [服务组合风险（多表关联）](07_service_stack_risk.sql) | 网络类型 × 安全 × 技术支持 |
| Q08 | [光纤裸奔用户（ROW_NUMBER）](08_fiber_bare_user_rank.sql) | 无任何增值服务的高危用户 |
| Q09 | [死亡组合（合同 × 支付）](09_payment_contract_combo.sql) | 月付 + 电子支票流失率最高 |
| Q10 | [支付方式高危排名（RANK）](10_payment_rank_monthly.sql) | 月付用户内部按流失率排名 |
| Q11 | [流失金额量化（MRR 损失）](11_revenue_loss_quant.sql) | 流失人数折算成真金白银 |
| Q12 | [营收二八定律（NTILE）](12_pareto_ntile_decile.sql) | Top 10% 用户贡献的营收占比 |
| Q13 | [新老客消费之王（DENSE_RANK）](13_value_king_dense_rank.sql) | 流失用户中的高价值个体 |
| Q14 | [高危用户全景画像（CTE）](14_high_risk_profile_cte.sql) | 多条件叠加的终极高危名单 |
| Q15 | [消费排名追踪（LEAD）](15_lead_value_tracking.sql) | 相邻排名用户的合同与金额差 |

## 覆盖能力

- **聚合与分组**：Q01–Q02，基础大盘与人群切片
- **多表关联**：Q02、Q07、Q14，CTE + JOIN 构建分析宽表
- **窗口函数**：Q03 `PARTITION BY`、Q05 `LAG`、Q08 `ROW_NUMBER`、Q10 `RANK`、Q12 `NTILE`、Q13 `DENSE_RANK`、Q15 `LEAD`
- **自连接**：Q06，用同类均值做基准对比
- **业务口径**：Q09 用 `HAVING COUNT(*) > 100` 过滤小样本，避免结论偶然

## 与报告的对应关系

| 报告结论 | 对应脚本 |
|---|---|
| 整体流失率 26.54% | Q01 |
| 0–6 个月流失率 52.94% | Q04 |
| 月付 + 电子支票 53.73% | Q09 |
| 每月损失 13.91 万元 | Q11 |
| Top10 贡献 53% 营收 | Q12 |
| 高价值流失名单 | Q06 / Q13 |
