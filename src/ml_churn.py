# -*- coding: utf-8 -*-
"""ml_churn.py —— 流失预测：特征工程 → 三模型对比 → 阈值寻优 → 可解释性。

业务约束（写死在代码里，方便复算）：
    ARPU            = 74.44 元/月       （报告中流失用户平均月租）
    SAVE_RATE       = 0.35              （挽留动作触达后的挽回成功率，保守假设）
    OFFER_COST      = 20   元/次        （一次挽留动作的成本：权益 + 人力）
    REMAIN_MONTHS   = 12                （预测窗口内剩余生命周期，保守取 12 个月）

输出（默认 results/）：
    metrics.json            三模型交叉验证 + 留出集指标
    model_comparison.csv    模型对比表
    feature_importance.csv  置换重要性
    fig_roc.png / fig_pr.png / fig_importance.png / fig_threshold_profit.png
    best_model.joblib       最优模型（含预处理流水线）

用法：
    python src/ml_churn.py                       # 自动找 data/telco.csv，找不到则用 demo
    python src/ml_churn.py --data data/telco.csv --out results
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, confusion_matrix, f1_score,
                             precision_recall_curve, precision_score, recall_score,
                             roc_auc_score, roc_curve)
from sklearn.model_selection import (StratifiedKFold, cross_val_predict, cross_validate,
                                     train_test_split)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
RANDOM_STATE = 42

ARPU = 74.44
SAVE_RATE = 0.35
OFFER_COST = 20.0
REMAIN_MONTHS = 12

DROP = ["customerID", "Churn"]


def load_data(path: str | None) -> pd.DataFrame:
    candidates = [Path(path)] if path else [
        ROOT / "data" / "telco.csv",
        ROOT / "data" / "telco_clean.csv",
        ROOT / "data" / "telco_demo.csv",
    ]
    for p in candidates:
        if not p.exists():
            continue
        print(f"[data] reading {p}  ({p.stat().st_size:,} bytes)")
        try:
            df = pd.read_csv(p)
        except Exception as exc:                      # 便于在 CI 里定位坏文件
            head = p.read_bytes()[:120]
            print(f"[data] FAILED {p}: {type(exc).__name__}: {exc}")
            print(f"[data] first bytes = {head!r}")
            raise
        print(f"[data] OK {p}  shape={df.shape}")
        return df
    raise SystemExit("未找到数据：请先下载 data/telco.csv，或运行 python src/make_demo_data.py")


def build_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]

    # 目标变量：兼容 Yes/No 文本与 0/1 数值
    # 注意：pandas 3 会把文本列读成 str dtype，用 `dtype == object` 判断会失效
    if pd.api.types.is_string_dtype(df["Churn"]):
        df["Churn"] = df["Churn"].map({"Yes": 1, "No": 0})
    df["Churn"] = df["Churn"].astype(int)

    df["TotalCharges"] = pd.to_numeric(
        df["TotalCharges"].astype(str).str.strip().replace("", None), errors="coerce"
    )
    df["TotalCharges"] = df["TotalCharges"].fillna(df["MonthlyCharges"] * df["tenure"])

    # 文本列统一转成 object，避免 sklearn 对 pandas 扩展 dtype 的兼容问题
    for col in df.columns:
        if pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].astype(object)

    # 特征工程：把“服务数量”“客单价偏差”“生命周期阶段”显式化
    service_cols = ["OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport",
                    "StreamingTV", "StreamingMovies"]
    df["service_count"] = sum((df[c] == "Yes").astype(int) for c in service_cols)
    df["avg_monthly"] = df["TotalCharges"] / np.maximum(df["tenure"], 1)
    df["is_new"] = (df["tenure"] <= 6).astype(int)
    df["charge_ratio"] = df["MonthlyCharges"] / df["avg_monthly"].replace(0, np.nan)
    df["charge_ratio"] = df["charge_ratio"].replace([np.inf, -np.inf], np.nan).fillna(1.0)

    y = df["Churn"].astype(int).to_numpy()
    X = df.drop(columns=[c for c in DROP if c in df.columns])
    return X, y


def build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    num = [c for c in X.columns if pd.api.types.is_numeric_dtype(X[c])]
    cat = [c for c in X.columns if c not in num]
    try:
        ohe = OneHotEncoder(handle_unknown="ignore", sparse_output=False, min_frequency=20)
    except TypeError:  # scikit-learn < 1.2
        ohe = OneHotEncoder(handle_unknown="ignore", sparse=False)
    return ColumnTransformer(
        [("num", Pipeline([("imp", SimpleImputer(strategy="median")),
                           ("sc", StandardScaler())]), num),
         ("cat", ohe, cat)],
        remainder="drop",
    )


def make_models(n_jobs: int = -1) -> dict[str, object]:
    return {
        "LogisticRegression": LogisticRegression(max_iter=2000, class_weight="balanced",
                                                 random_state=RANDOM_STATE),
        "RandomForest": RandomForestClassifier(
            n_estimators=300, min_samples_leaf=5, max_features="sqrt",
            class_weight="balanced_subsample", n_jobs=n_jobs, random_state=RANDOM_STATE),
        "HistGradientBoosting": HistGradientBoostingClassifier(
            max_iter=300, learning_rate=0.06, max_leaf_nodes=31,
            l2_regularization=1.0, random_state=RANDOM_STATE),
    }


def expected_profit(y_true: np.ndarray, proba: np.ndarray, threshold: float) -> float:
    """按“只对预测会流失的人做挽留”计算净收益（元/预测窗口）。"""
    pred = proba >= threshold
    tp = int(((pred == 1) & (y_true == 1)).sum())
    fp = int(((pred == 1) & (y_true == 0)).sum())
    return tp * (ARPU * REMAIN_MONTHS * SAVE_RATE - OFFER_COST) - fp * OFFER_COST


def best_threshold(y_true: np.ndarray, proba: np.ndarray) -> tuple[float, float]:
    grid = np.round(np.arange(0.05, 0.96, 0.01), 2)
    scores = [(t, expected_profit(y_true, proba, t)) for t in grid]
    return max(scores, key=lambda x: x[1])


def evaluate(y_true, proba, threshold: float) -> dict:
    pred = (proba >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, pred, labels=[0, 1]).ravel()
    return {
        "roc_auc": round(float(roc_auc_score(y_true, proba)), 4),
        "pr_auc": round(float(average_precision_score(y_true, proba)), 4),
        "threshold": round(float(threshold), 2),
        "precision": round(float(precision_score(y_true, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, pred, zero_division=0)), 4),
        "tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn),
        "predicted_positive_rate": round(float(pred.mean()), 4),
        "expected_profit_yuan": round(expected_profit(y_true, proba, threshold), 2),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None)
    ap.add_argument("--out", default=str(ROOT / "results"))
    ap.add_argument("--no-plots", action="store_true")
    ap.add_argument("--n-jobs", type=int, default=-1,
                    help="并行进程数；受限环境（无法创建管道）用 1")
    args = ap.parse_args()

    # n_jobs=1 时传 None，让 sklearn/joblib 走纯串行，避免受限环境创建多进程管道
    nj = None if args.n_jobs == 1 else args.n_jobs

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    df = load_data(args.data)
    X, y = build_xy(df)
    print(f"[info] features={X.shape[1]}  positives={y.sum()}  rate={y.mean():.4f}")

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE)

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=RANDOM_STATE)
    scoring = {"roc_auc": "roc_auc", "average_precision": "average_precision",
               "f1": "f1", "precision": "precision", "recall": "recall"}

    results, fitted = {}, {}
    for name, model in make_models(nj).items():
        pipe = Pipeline([("prep", build_preprocessor(X)), ("clf", model)])
        cvres = cross_validate(pipe, X_tr, y_tr, cv=cv, scoring=scoring, n_jobs=nj)
        pipe.fit(X_tr, y_tr)

        # 阈值只在训练集 OOF 预测上寻优，再原样用到留出集，避免信息泄漏
        oof = cross_val_predict(pipe, X_tr, y_tr, cv=cv, method="predict_proba", n_jobs=nj)[:, 1]
        thr, _ = best_threshold(y_tr, oof)

        proba = pipe.predict_proba(X_te)[:, 1]
        metrics = evaluate(y_te, proba, thr)
        metrics["cv_roc_auc"] = round(float(cvres["test_roc_auc"].mean()), 4)
        metrics["cv_pr_auc"] = round(float(cvres["test_average_precision"].mean()), 4)
        metrics["cv_f1"] = round(float(cvres["test_f1"].mean()), 4)
        results[name] = metrics
        fitted[name] = (pipe, proba, thr)
        print(f"[{name:22s}] AUC={metrics['roc_auc']:.3f}  PR-AUC={metrics['pr_auc']:.3f}  "
              f"thr={thr:.2f}  P={metrics['precision']:.2f}  R={metrics['recall']:.2f}  "
              f"profit={metrics['expected_profit_yuan']:,.0f}元")

    best_name = max(results, key=lambda k: results[k]["pr_auc"])
    best_pipe, best_proba, best_thr = fitted[best_name]
    print(f"[best] {best_name}")

    # 置换重要性
    imp = permutation_importance(best_pipe, X_te, y_te, scoring="roc_auc",
                                 n_repeats=5, random_state=RANDOM_STATE, n_jobs=nj)
    imp_df = (pd.DataFrame({"feature": X.columns, "importance": imp.importances_mean,
                            "std": imp.importances_std})
              .sort_values("importance", ascending=False))
    imp_df.to_csv(out / "feature_importance.csv", index=False)

    pd.DataFrame(results).T.rename_axis("model").to_csv(out / "model_comparison.csv")
    summary = {
        "data_rows": int(len(df)),
        "churn_rate": round(float(y.mean()), 4),
        "business_assumption": {"arpu": ARPU, "save_rate": SAVE_RATE,
                                "offer_cost": OFFER_COST, "remain_months": REMAIN_MONTHS},
        "best_model": best_name,
        "models": results,
    }
    (out / "metrics.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    joblib.dump(best_pipe, out / "best_model.joblib")

    if not args.no_plots:
        fig, ax = plt.subplots(figsize=(6, 5), dpi=150)
        for name, (_, proba, _) in fitted.items():
            fpr, tpr, _ = roc_curve(y_te, proba)
            ax.plot(fpr, tpr, label=f"{name} (AUC={results[name]['roc_auc']:.3f})")
        ax.plot([0, 1], [0, 1], "k--", lw=1, label="Random")
        ax.set_xlabel("False Positive Rate"); ax.set_ylabel("True Positive Rate")
        ax.set_title("ROC Curve - Churn Prediction"); ax.legend(loc="lower right"); ax.grid(alpha=.3)
        fig.tight_layout(); fig.savefig(out / "fig_roc.png"); plt.close(fig)

        fig, ax = plt.subplots(figsize=(6, 5), dpi=150)
        for name, (_, proba, _) in fitted.items():
            p, r, _ = precision_recall_curve(y_te, proba)
            ax.plot(r, p, label=f"{name} (PR-AUC={results[name]['pr_auc']:.3f})")
        ax.set_xlabel("Recall"); ax.set_ylabel("Precision")
        ax.set_title("Precision-Recall Curve"); ax.legend(); ax.grid(alpha=.3)
        fig.tight_layout(); fig.savefig(out / "fig_pr.png"); plt.close(fig)

        top = imp_df.head(12).iloc[::-1]
        fig, ax = plt.subplots(figsize=(6.5, 4.5), dpi=150)
        ax.barh(top["feature"], top["importance"], xerr=top["std"], color="#2E5C8A")
        ax.set_xlabel("Permutation importance (Δ ROC-AUC)")
        ax.set_title(f"Top Features - {best_name}"); ax.grid(axis="x", alpha=.3)
        fig.tight_layout(); fig.savefig(out / "fig_importance.png"); plt.close(fig)

        grid = np.arange(0.05, 0.96, 0.01)
        profits = [expected_profit(y_te, best_proba, t) for t in grid]
        fig, ax = plt.subplots(figsize=(6.5, 4), dpi=150)
        ax.plot(grid, np.array(profits) / 10000, color="#C2410C", lw=2)
        ax.axvline(best_thr, ls="--", color="#12355B", label=f"optimal={best_thr:.2f}")
        ax.set_xlabel("Threshold"); ax.set_ylabel("Expected profit (万元)")
        ax.set_title("Threshold vs Profit"); ax.legend(); ax.grid(alpha=.3)
        fig.tight_layout(); fig.savefig(out / "fig_threshold_profit.png"); plt.close(fig)

    print(f"[done] outputs -> {out}")


if __name__ == "__main__":
    main()
