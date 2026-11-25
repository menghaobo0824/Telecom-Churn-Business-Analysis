# -*- coding: utf-8 -*-
"""abtest_analysis.py —— 挽留策略 A/B 实验：功效分析 → 模拟投放 → 统计检验 → 分层归因。

设计背景：针对“0–6 个月新客流失率 52.94%”这一问题，测试「新客护航计划」
（第 7/30/60/90 天四次触达 + 首月账单体检）能否把该人群流失率显著压低。

本脚本做三件事：
1. 功效分析（power analysis）：给定基线、MDE、α、power，反解每组所需样本量；
2. 模拟一次实验（可复现的随机抽样），并用双样本比例检验 + 置信区间 + 自助法给出结论；
3. 分层分析（heterogeneity）：不同合同类型的处理效应差异，用于判断下一步策略。

说明：实验数据为**模拟**（仓库不包含真实投放记录），因此结论仅用于演示统计口径与决策流程。

用法：
    python src/abtest_analysis.py --out results
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]

# ---------------- 实验参数 ----------------
BASELINE = 0.5294        # 对照组流失率：0–6 个月人群（来自报告结论）
MDE_ABS = 0.04           # 最小可检测绝对差异 4pp（52.94% -> 48.94%）
ALPHA = 0.05
POWER = 0.80
RANDOM_STATE = 42
SEGMENT_SEED = 325       # 分层模拟固定种子，保证结果可复现


def z_value(p: float) -> float:
    """标准正态分位数（Abramowitz-Stegun 逆误差函数近似，精度 1e-6 足够）。"""
    lo, hi = -10.0, 10.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if 0.5 * (1 + math.erf(mid / math.sqrt(2))) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def required_sample_size(p0: float, mde: float, alpha: float = ALPHA, power: float = POWER,
                         two_sided: bool = True) -> int:
    """两组比例检验所需样本量（每组），用迭代避免近似式在小样本下偏差。"""
    p1 = p0 - mde                     # 实验组流失率（下降 mde）
    za = z_value(1 - alpha / 2) if two_sided else z_value(1 - alpha)
    zb = z_value(power)
    n = 1000
    for _ in range(60):
        pbar = (p0 + p1) / 2
        num = (za * math.sqrt(2 * pbar * (1 - pbar)) + zb * math.sqrt(p0 * (1 - p0) + p1 * (1 - p1))) ** 2
        n_new = int(math.ceil(num / (mde ** 2)))
        if n_new == n:
            break
        n = n_new
    return n


def two_proportion_test(x_c: int, n_c: int, x_t: int, n_t: int) -> dict:
    """双侧双样本比例 z 检验（合并方差）+ Wald 置信区间 + 自助法区间。"""
    p_c, p_t = x_c / n_c, x_t / n_t
    diff = p_t - p_c
    p_pool = (x_c + x_t) / (n_c + n_t)

    se_pool = math.sqrt(p_pool * (1 - p_pool) * (1 / n_c + 1 / n_t))
    z = diff / se_pool if se_pool else 0.0
    p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))

    se_unpooled = math.sqrt(p_c * (1 - p_c) / n_c + p_t * (1 - p_t) / n_t)
    z_crit = z_value(1 - ALPHA / 2)
    ci_low, ci_high = diff - z_crit * se_unpooled, diff + z_crit * se_unpooled

    rel = diff / p_c
    rel_se = se_unpooled / p_c
    rel_ci = (rel - z_crit * rel_se, rel + z_crit * rel_se)

    # 自助法（对单位记录重抽样，不假设正态）
    rng = np.random.default_rng(RANDOM_STATE)
    boot = np.empty(4000)
    for i in range(4000):
        bc = rng.binomial(n_c, p_c) / n_c
        bt = rng.binomial(n_t, p_t) / n_t
        boot[i] = bt - bc
    boot_ci = (float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5)))

    # 卡方（2×2）
    obs = np.array([[x_t, n_t - x_t], [x_c, n_c - x_c]], dtype=float)
    exp = obs.sum(axis=1, keepdims=True) * obs.sum(axis=0, keepdims=True) / obs.sum()
    chi2 = float(((obs - exp) ** 2 / exp).sum())

    nnt = 1 / abs(diff) if diff else float("inf")
    return {
        "p_control": round(p_c, 4), "p_treatment": round(p_t, 4),
        "abs_lift": round(diff, 4), "rel_lift": round(rel, 4),
        "z": round(z, 3), "p_value": round(p_value, 6),
        "ci_abs": [round(ci_low, 4), round(ci_high, 4)],
        "ci_rel": [round(rel_ci[0], 4), round(rel_ci[1], 4)],
        "ci_bootstrap": [round(boot_ci[0], 4), round(boot_ci[1], 4)],
        "chi2": round(chi2, 3),
        "nnt": round(nnt, 1),
        "significant": bool(p_value < ALPHA and ci_high < 0),
    }


def srm_check(n_c: int, n_t: int, expected_ratio: float = 0.5) -> dict:
    """Sample Ratio Mismatch：分流比例是否符合预期（卡方拟合优度）。"""
    n = n_c + n_t
    exp_c, exp_t = n * expected_ratio, n * (1 - expected_ratio)
    chi2 = (n_c - exp_c) ** 2 / exp_c + (n_t - exp_t) ** 2 / exp_t
    # 自由度 1 的卡方 -> p 值
    p = math.erfc(math.sqrt(chi2 / 2))
    return {"ratio": round(n_t / n, 4), "chi2": round(chi2, 3), "p_value": round(p, 4),
            "pass": bool(p > 0.01)}


def simulate(n_per_arm: int, true_lift: float, seed: int = RANDOM_STATE):
    """模拟一次实验：对照组 p0，实验组 p0 - true_lift。"""
    rng = np.random.default_rng(seed)
    p0 = BASELINE
    p1 = p0 - true_lift
    x_c = int(rng.binomial(n_per_arm, p0))
    x_t = int(rng.binomial(n_per_arm, p1))
    return x_c, x_t


def segment_analysis(n_per_arm: int, seed: int = SEGMENT_SEED) -> list[dict]:
    """分层效应：不同合同类型的挽留效果（模拟真实异质性）。"""
    segments = [
        ("Month-to-month", 0.60, 0.06),   # 高基线、效果最好
        ("One year", 0.35, 0.02),
        ("Two year", 0.14, 0.005),
    ]
    rng = np.random.default_rng(seed)
    n = max(int(n_per_arm * 0.6), 500)
    out = []
    for name, base, lift in segments:
        x_c = int(rng.binomial(n, base))
        x_t = int(rng.binomial(n, base - lift))
        res = two_proportion_test(x_c, n, x_t, n)
        out.append({"segment": name, "n_per_arm": n, "baseline": base,
                    "observed_lift": res["abs_lift"], "p_value": res["p_value"],
                    "ci_abs": res["ci_abs"]})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "results"))
    ap.add_argument("--true-lift", type=float, default=0.04, help="模拟时实验组真实提升幅度")
    args = ap.parse_args()

    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    n_req = required_sample_size(BASELINE, MDE_ABS)
    print(f"[power] 基线={BASELINE:.2%}  MDE={MDE_ABS:.2%}  alpha={ALPHA}  power={POWER}")
    print(f"[power] 每组所需样本量 = {n_req:,}（两组共 {2 * n_req:,}）")

    x_c, x_t = simulate(n_req, args.true_lift)
    print(f"[sim] control {x_c}/{n_req}  treatment {x_t}/{n_req}")
    res = two_proportion_test(x_c, n_req, x_t, n_req)
    print(f"[test] 对照 {res['p_control']:.2%} vs 实验 {res['p_treatment']:.2%}  "
          f"diff={res['abs_lift']:+.2%}  95%CI={res['ci_abs']}  p={res['p_value']:.4f}")

    srm = srm_check(n_req, n_req)
    print(f"[srm] ratio={srm['ratio']}  p={srm['p_value']}  pass={srm['pass']}")

    seg = segment_analysis(n_req)
    for s in seg:
        print(f"[segment] {s['segment']:<16} lift={s['observed_lift']:+.2%}  p={s['p_value']:.4f}")

    summary = {
        "design": {"baseline": BASELINE, "mde_abs": MDE_ABS, "alpha": ALPHA,
                   "power": POWER, "n_per_arm": n_req, "total": 2 * n_req},
        "simulated_outcome": {"control": x_c, "treatment": x_t, "n_per_arm": n_req,
                              "true_lift": args.true_lift},
        "test": res, "srm": srm, "segments": seg,
        "note": "实验数据为模拟数据，仅用于演示统计口径，不代表真实投放效果。",
    }
    (out / "abtest_results.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                                             encoding="utf-8")

    md = [
        "# A/B 实验结论（模拟）",
        "",
        f"- 每组样本：{n_req:,}（总 {2 * n_req:,}）",
        f"- 对照组流失率：{res['p_control']:.2%}；实验组：{res['p_treatment']:.2%}",
        f"- 绝对提升：{res['abs_lift']:+.2%}（95% CI {res['ci_abs'][0]:+.2%} ~ {res['ci_abs'][1]:+.2%}）",
        f"- 相对提升：{res['rel_lift']:+.2%}（95% CI {res['ci_rel'][0]:+.2%} ~ {res['ci_rel'][1]:+.2%}，"
        f"自助法 {res['ci_bootstrap'][0]:+.2%} ~ {res['ci_bootstrap'][1]:+.2%}）",
        f"- p 值：{res['p_value']:.4f}；NNT：{res['nnt']}",
        f"- SRM 检查：({'通过' if srm['pass'] else '异常'})，实验组占比 {srm['ratio']:.2%}",
        "",
        "| 分层 | 每组样本 | 基线 | 观测提升 | p 值 | 95% CI |",
        "|---|---|---|---|---|---|",
    ]
    for s in seg:
        md.append(f"| {s['segment']} | {s['n_per_arm']:,} | {s['baseline']:.0%} | "
                  f"{s['observed_lift']:+.2%} | {s['p_value']:.4f} | "
                  f"[{s['ci_abs'][0]:+.2%}, {s['ci_abs'][1]:+.2%}] |")
    (out / "abtest_results.md").write_text("\n".join(md), encoding="utf-8")
    print(f"[done] -> {out/'abtest_results.json'}")


if __name__ == "__main__":
    main()
