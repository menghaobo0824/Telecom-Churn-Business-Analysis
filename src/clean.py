# -*- coding: utf-8 -*-
"""clean.py —— 数据清洗与入库（MySQL 表名：data）。

处理四类问题：
1. 字段名空格/大小写不统一      -> 统一 strip
2. TotalCharges 为文本且含空白   -> 数值强转 + 业务回填（月租 × 在网月数）
3. Churn 为 Yes/No 文本          -> 映射为 1/0，AVG(Churn) 即流失率
4. 月租极端值                    -> IQR 封顶（winsorize），**不删样本**，保证总数 7043 与报告口径一致
   （累计消费 TotalCharges 不做 IQR 截尾：它随在网时长增长，截尾会误伤高价值老客）

用法：
    python src/clean.py --data data/telco.csv                 # 只清洗，输出 data/telco_clean.csv
    python src/clean.py --data data/telco.csv --load-mysql     # 额外写入 MySQL
环境变量（写入 MySQL 时使用）：
    MYSQL_URL=mysql+pymysql://user:pass@localhost:3306/churn?charset=utf8mb4
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
NUMERIC = ["tenure", "MonthlyCharges", "TotalCharges"]


def iqr_bounds(s: pd.Series, k: float = 1.5) -> tuple[float, float]:
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    return q1 - k * iqr, q3 + k * iqr


def clean(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    out = df.copy()
    out.columns = [c.strip() for c in out.columns]

    # 1) 主键去重
    before = len(out)
    out = out.drop_duplicates(subset="customerID").reset_index(drop=True)
    if verbose and before != len(out):
        print(f"[dedup] {before - len(out)} duplicated rows removed")

    # 2) TotalCharges：文本 -> 数值，空白按“月租 × 在网月数”回填
    out["TotalCharges"] = pd.to_numeric(
        out["TotalCharges"].astype(str).str.strip().replace("", None), errors="coerce"
    )
    n_blank = int(out["TotalCharges"].isna().sum())
    out["TotalCharges"] = out["TotalCharges"].fillna(out["MonthlyCharges"] * out["tenure"])

    # 3) 目标变量二值化
    out["Churn"] = out["Churn"].map({"Yes": 1, "No": 0}).astype("int8")

    # 4) IQR 封顶（不删样本）：只对月租做，累计消费不做截尾
    #    原因：TotalCharges = 月租 × 在网时长，天然右偏；对它做 IQR 截尾会把
    #    “高价值老客”误判为异常值，而这类用户恰恰是挽留分析的主角。
    lo, hi = iqr_bounds(out["MonthlyCharges"])
    n_clip = int(((out["MonthlyCharges"] < lo) | (out["MonthlyCharges"] > hi)).sum())
    out["MonthlyCharges"] = out["MonthlyCharges"].clip(lo, hi).round(2)
    out["TotalCharges"] = out["TotalCharges"].clip(lower=0).round(2)

    if verbose:
        print(f"[iqr] MonthlyCharges: bounds=({lo:.2f}, {hi:.2f}) clipped={n_clip}")
        print(f"[null] TotalCharges blanks filled: {n_blank}")
        print(f"[shape] rows={len(out)} cols={out.shape[1]} churn_rate={out['Churn'].mean():.4f}")
    return out


def load_to_mysql(df: pd.DataFrame, url: str, table: str = "data") -> None:
    from sqlalchemy import create_engine

    engine = create_engine(url)
    df.to_sql(table, engine, if_exists="replace", index=False)
    print(f"[mysql] wrote {len(df)} rows -> {table}")


def main() -> None:
    ap = argparse.ArgumentParser(description="清洗 Telco Churn 数据")
    ap.add_argument("--data", default=str(ROOT / "data" / "telco.csv"))
    ap.add_argument("--out", default=str(ROOT / "data" / "telco_clean.csv"))
    ap.add_argument("--load-mysql", action="store_true")
    args = ap.parse_args()

    df = pd.read_csv(args.data)
    cleaned = clean(df)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(args.out, index=False)
    print(f"[save] {args.out}")

    if args.load_mysql:
        url = os.environ.get("MYSQL_URL")
        if not url:
            raise SystemExit("请先设置环境变量 MYSQL_URL，例如 mysql+pymysql://root:pass@localhost:3306/churn")
        load_to_mysql(cleaned, url)


if __name__ == "__main__":
    main()
