# 查询结果（15 条 SQL 的原始输出）

这 15 个 CSV 是 `sql/` 目录下对应脚本在 `data` 表（7,043 行）上的**真实执行结果**，
直接由 MySQL 客户端导出，未做任何二次加工。

用途：
- 复核报告里的每个数字（可下载、可 diff，比截图更可靠）
- 作为「SQL 能跑通」的证据链
- 名单类结果可直接给电销/运营使用

| 文件 | 对应 SQL | 行数 | 关键结论 |
|---|---|---|---|
| `q01_overall_churn.csv` | [Q01](../../sql/01_overall_churn_overview.sql) | 1 | 7,043 人 / 流失 1,869 / 26.54% |
| `q02_demographics.csv` | [Q02](../../sql/02_demographics_join.sql) | 4 | 老年且无伴侣：48.86%（最高） |
| `q03_contract_share_gender.csv` | [Q03](../../sql/03_contract_share_by_gender.sql) | 6 | 两性别的合同结构几乎一致，性别不是抓手 |
| `q04_retention_cliff.csv` | [Q04](../../sql/04_retention_cliff_lifecycle.sql) | 4 | 0–6 个月 52.94%，2 年以上 14.04% |
| `q05_contract_ladder.csv` | [Q05](../../sql/05_contract_ladder_lag.sql) | 3 | 月付 42.71% → 一年 11.27% → 两年 2.83% |
| `q06_high_value_above_avg.csv` | [Q06](../../sql/06_high_value_self_join.sql) | 10 | 月租高于同合同均价的流失用户 Top 10 |
| `q07_service_stack.csv` | [Q07](../../sql/07_service_stack_risk.sql) | 5 | 光纤 + 无安全 + 无支持：55.01% |
| `q08_fiber_bare_users.csv` | [Q08](../../sql/08_fiber_bare_user_rank.sql) | 9 | 每类合同各 3 名「裸奔光纤」高危用户 |
| `q09_payment_combo.csv` | [Q09](../../sql/09_payment_contract_combo.sql) | 5 | 月付 + 电子支票 53.73% |
| `q10_payment_rank.csv` | [Q10](../../sql/10_payment_rank_monthly.sql) | 4 | 月付用户内，电子支票排名第 1 |
| `q11_revenue_loss.csv` | [Q11](../../sql/11_revenue_loss_quant.sql) | 1 | 月损失 139,130.85 元，客单价 74.44 |
| `q12_pareto_ntile.csv` | [Q12](../../sql/12_pareto_ntile_decile.sql) | 2 | Top 10% 贡献 30.83%，其余 90% 贡献 69.17% |
| `q13_value_king.csv` | [Q13](../../sql/13_value_king_dense_rank.sql) | 4 | 新客/老客各自的消费之王 |
| `q14_high_risk_profile.csv` | [Q14](../../sql/14_high_risk_profile_cte.sql) | 5 | 四特征叠加的终极高危名单 |
| `q15_lead_tracking.csv` | [Q15](../../sql/15_lead_value_tracking.sql) | 20 | 相邻排名用户的消费差，用于分档定价 |

## 复现方式

```bash
# 1) 数据入库
python src/clean.py --data data/telco.csv --load-mysql

# 2) 逐条执行
mysql -u root -p churn < sql/q01_overall_churn_overview.sql

# 3) 与 CSV 对比（示例）
python -c "import pandas as pd; print(pd.read_csv('results/sql/q01_overall_churn.csv'))"
```

> 注意：`q12_pareto_ntile.csv` 的 `revenue_share_pct` 是**已经乘过 100 的百分比**，
> `30.83` 表示 30.83%，不是 0.3083。这是本项目早期最容易读错的地方。
