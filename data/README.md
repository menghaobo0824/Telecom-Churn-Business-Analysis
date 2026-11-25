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

## 3. 字段说明（分析实际用到的列）

| 字段 | 含义 | 类型 | 用途 |
|---|---|---|---|
| customerID | 用户唯一标识 | 文本 | 主键、名单 |
| tenure | 在网月数 | 整数 | 生命周期分箱 |
| Contract | 合同类型 | 枚举 | 归因主维度 |
| PaymentMethod | 支付方式 | 枚举 | 归因主维度 |
| InternetService | 网络类型 | 枚举 | 服务归因 |
| OnlineSecurity / TechSupport 等 | 增值服务 | 枚举 | 服务组合 |
| MonthlyCharges | 当前月租 | 浮点 | 金额量化 |
| TotalCharges | 历史累计消费 | 浮点 | 客户价值 |
| Churn | 是否流失 | Yes/No | 目标变量 |

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
