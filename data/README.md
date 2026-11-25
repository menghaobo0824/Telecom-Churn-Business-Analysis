# 数据说明

## 1. 正式分析数据

本仓库**不包含**原始数据（版权归数据提供方）。请自行下载后放到本目录：

- 数据集：**Telco Customer Churn**（IBM Sample Data Sets）
- 文件：`WA_Fn-UseC_-Telco-Customer-Churn.csv` → 重命名为 `telco.csv`
- 常见获取途径：Kaggle `blastchar/telco-customer-churn`，或 IBM 官方 sample 数据集页面
- 规模：7,043 行 × 21 列

下载后目录结构应为：

```
data/
├── telco.csv          # 原始数据（git 忽略）
├── telco_clean.csv    # clean.py 输出（git 忽略）
└── README.md
```

## 2. 字段说明（分析实际用到的列）

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

## 3. 没有原始数据也能跑

```bash
python src/make_demo_data.py     # 生成 data/telco_demo.csv
python src/clean.py --data data/telco_demo.csv --out data/telco_clean.csv
python src/abtest_analysis.py
python src/ml_churn.py --data data/telco_demo.csv --no-plots
```

`make_demo_data.py` 生成的是**与真实数据结构同构的合成数据**（字段、取值域、量级一致，
整体流失率校准到 26.54%），仅用于跑通流水线与 CI 自检，**不能**用来复现报告中的业务结论。
