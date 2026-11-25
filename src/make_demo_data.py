# -*- coding: utf-8 -*-
"""make_demo_data.py —— 生成与公开 Telco Churn 数据集同构的演示数据。

用途：在没有原始数据（Kaggle 需登录、且许可不允许随意分发）的情况下，
让 CI 与本地流水线可以端到端跑通。**字段、取值域、量级都与真实数据一致，
但每一行都是合成的**，因此其运行结果不能当作业务结论引用。

真实数据请按 data/README.md 的说明下载到 data/telco.csv。
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
N = 7043
TARGET_CHURN = 0.2654          # 与真实数据集一致的流失率
RNG = np.random.default_rng(42)


def _pick(values, probs, n=N):
    return RNG.choice(values, size=n, p=probs)


def build(n: int = N, seed: int = 42) -> pd.DataFrame:
    global RNG
    RNG = np.random.default_rng(seed)

    gender = _pick(["Female", "Male"], [0.493, 0.507], n)
    senior = _pick([0, 1], [0.838, 0.162], n)
    partner = _pick(["No", "Yes"], [0.517, 0.483], n)
    dependents = _pick(["No", "Yes"], [0.700, 0.300], n)

    # 在网时长：新客占比高，长尾拖到 72 个月
    tenure = np.clip(RNG.gamma(shape=1.05, scale=15.0, size=n), 0, 72).round().astype(int)

    contract = _pick(["Month-to-month", "One year", "Two year"], [0.550, 0.209, 0.241], n)
    payment = _pick(
        ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"],
        [0.336, 0.229, 0.219, 0.216], n,
    )
    paperless = _pick(["No", "Yes"], [0.407, 0.593], n)
    internet = _pick(["DSL", "Fiber optic", "No"], [0.344, 0.440, 0.216], n)
    phone = _pick(["No", "Yes"], [0.096, 0.904], n)

    def svc(p_yes: float):
        return _pick(["No", "Yes", "No internet service"], [p_yes, 1 - p_yes - 0.21, 0.21], n)

    online_security = np.where(internet == "No", "No internet service", svc(0.286))
    online_backup = np.where(internet == "No", "No internet service", svc(0.344))
    device_protection = np.where(internet == "No", "No internet service", svc(0.343))
    tech_support = np.where(internet == "No", "No internet service", svc(0.290))
    streaming_tv = np.where(internet == "No", "No internet service", svc(0.384))
    streaming_movies = np.where(internet == "No", "No internet service", svc(0.388))
    multiple_lines = np.where(phone == "No", "No phone service", _pick(["No", "Yes"], [0.482, 0.518], n))

    # 月租：由服务组合叠加而来
    base = np.where(internet == "Fiber optic", 70.0, np.where(internet == "DSL", 45.0, 21.0))
    addon = (
        (online_security == "Yes") * 4.5
        + (online_backup == "Yes") * 4.4
        + (device_protection == "Yes") * 4.4
        + (tech_support == "Yes") * 4.6
        + (streaming_tv == "Yes") * 5.2
        + (streaming_movies == "Yes") * 5.2
        + (multiple_lines == "Yes") * 5.0
    )
    monthly = np.clip(base + addon + RNG.normal(0, 3.2, n), 18.0, 120.0).round(2)
    total = (monthly * np.maximum(tenure, 1) * RNG.normal(1.0, 0.06, n)).round(2)
    total = np.where(tenure == 0, np.nan, total)
    blank_idx = RNG.choice(n, size=11, replace=False)
    total[blank_idx] = np.nan

    # 流失概率：与真实数据同向（月付/电子支票/光纤/无支持/新客更高）
    z = (
        -1.15
        + 1.30 * (contract == "Month-to-month")
        - 0.45 * (contract == "Two year")
        + 0.62 * (payment == "Electronic check")
        + 0.55 * (internet == "Fiber optic")
        - 0.30 * (internet == "DSL")
        - 0.055 * np.minimum(tenure, 60)
        + 0.30 * (senior == 1)
        - 0.22 * (partner == "Yes")
        + 0.42 * (tech_support == "No")
        + 0.38 * (online_security == "No")
        + 0.018 * (monthly - monthly.mean())
    )
    p = 1 / (1 + np.exp(-z))
    # 校准截距，使整体流失率贴近 26.54%
    lo, hi = -3.0, 3.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if (1 / (1 + np.exp(-(z + mid)))).mean() < TARGET_CHURN:
            lo = mid
        else:
            hi = mid
    p = 1 / (1 + np.exp(-(z + (lo + hi) / 2)))
    churn = RNG.binomial(1, p)

    ids = [f"{RNG.integers(1000, 9999)}-{''.join(RNG.choice(list('ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 5))}" for _ in range(n)]

    df = pd.DataFrame({
        "customerID": ids,
        "gender": gender,
        "SeniorCitizen": senior,
        "Partner": partner,
        "Dependents": dependents,
        "tenure": tenure,
        "PhoneService": phone,
        "MultipleLines": multiple_lines,
        "InternetService": internet,
        "OnlineSecurity": online_security,
        "OnlineBackup": online_backup,
        "DeviceProtection": device_protection,
        "TechSupport": tech_support,
        "StreamingTV": streaming_tv,
        "StreamingMovies": streaming_movies,
        "Contract": contract,
        "PaperlessBilling": paperless,
        "PaymentMethod": payment,
        "MonthlyCharges": monthly,
        "TotalCharges": total,
        "Churn": np.where(churn == 1, "Yes", "No"),
    })
    return df


def main() -> None:
    ap = argparse.ArgumentParser(description="生成演示数据")
    ap.add_argument("--rows", type=int, default=N)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default=str(ROOT / "data" / "telco_demo.csv"))
    args = ap.parse_args()

    df = build(args.rows, args.seed)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(args.out, index=False)
    rate = (df["Churn"] == "Yes").mean()
    print(f"saved {args.out}  rows={len(df)}  churn_rate={rate:.4f}")


if __name__ == "__main__":
    main()
