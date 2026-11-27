# 数据说明

## 1. 仓库内置的原始数据

`data/telco.csv` 已随仓库提供，**7,043 行 × 21 列**，是公开样本数据集
**Telco Customer Churn**（IBM Sample Data Sets）的原始文件，未做任何修改。

- 来源：IBM 公开样本数据集，常见分发渠道为 Kaggle `blastchar/telco-customer-churn`
- 许可：**CC BY-NC-ND 4.0** —— 允许原样转载并署名，禁止商用、禁止分发衍生作品
- 因此本仓库只内置**原始文件**；清洗后的数据由 `src/clean.py` 现场生成，不入库

> 如果你的用途涉及商业场景，请自行到上游获取数据并遵守其许可。

## 2. 目录约定

```
data/
├── telco.csv          # 原始数据（仓库内置）
├── telco_clean.csv    # clean.py 输出（git 忽略，本地生成）
├── telco_demo.csv     # make_demo_data.py 生成的演示数据（git 忽略）
└── README.md
```

## 3. 字段字典（21 列全量）

| # | 字段 | 类型 | 取值 / 说明 | 分析用途 |
|---|---|---|---|---|
| 1 | customerID | 文本 | 形如 `7590-VHVEG` | 主键、名单 |
| 2 | gender | 枚举 | Female / Male | 分组维度（Q03） |
| 3 | SeniorCitizen | 0/1 | 1 = 老年用户 | 人群归因（Q02） |
| 4 | Partner | 枚举 | Yes / No 是否有伴侣 | 人群归因（Q02） |
| 5 | Dependents | 枚举 | Yes / No 是否有家属 | 人群归因 |
| 6 | tenure | 整数 | 在网月数，0–72 | **生命周期分箱（Q04）** |
| 7 | PhoneService | 枚举 | Yes / No | 服务组合 |
| 8 | MultipleLines | 枚举 | Yes / No / No phone service | 服务组合 |
| 9 | InternetService | 枚举 | DSL / Fiber optic / No | **网络类型归因（Q07）** |
| 10 | OnlineSecurity | 枚举 | Yes / No / No internet service | 增值服务、模型特征 |
| 11 | OnlineBackup | 枚举 | 同上 | 增值服务 |
| 12 | DeviceProtection | 枚举 | 同上 | 增值服务 |
| 13 | TechSupport | 枚举 | 同上 | 增值服务（Q07） |
| 14 | StreamingTV | 枚举 | 同上 | 增值服务 |
| 15 | StreamingMovies | 枚举 | 同上 | 增值服务 |
| 16 | Contract | 枚举 | Month-to-month / One year / Two year | **核心归因维度（Q05、Q09）** |
| 17 | PaperlessBilling | 枚举 | Yes / No 是否电子账单 | 模型特征 |
| 18 | PaymentMethod | 枚举 | Electronic check / Mailed check / Bank transfer (automatic) / Credit card (automatic) | **核心归因维度（Q09、Q10）** |
| 19 | MonthlyCharges | 浮点 | 当前月租，18.80–118.75 元 | 金额量化（Q11） |
| 20 | TotalCharges | 浮点（原始为文本） | 历史累计消费，含 11 条空白 | 客户价值（Q12、Q13、Q15） |
| 21 | Churn | Yes / No | 是否流失，清洗后映射为 0/1 | 目标变量 |

> 早期版本的本表只列了 9 个核心字段，这里补全 21 列，方便读者对照原始 CSV。

## 4. 数据质量（真实数据实测）

| 检查项 | 结果 |
|---|---|
| 行数 × 列数 | 7,043 × 21 |
| 主键重复 | 0 |
| `Churn = Yes` | 1,869（26.54%） |
| `TotalCharges` 空白 | 11 条（均为在网 0 个月的新客），按 `月租 × 在网月数` 回填 |
| `TotalCharges` 类型 | 原始为字符串，已强转为数值 |
| `MonthlyCharges` IQR 边界 | (−46.02, 171.38)，实际取值 18.80–118.75，**无封顶** |

## 5. 没有原始数据也能跑

```bash
python src/make_demo_data.py     # 生成 data/telco_demo.csv
python src/clean.py --data data/telco_demo.csv --out data/telco_clean.csv
python src/abtest_analysis.py
```

`make_demo_data.py` 生成的是**与真实数据结构同构的合成数据**（字段、取值域、量级一致，
整体流失率校准到 26.54%），仅用于跑通流水线与 CI 自检，**不能**用来复现报告中的业务结论。
