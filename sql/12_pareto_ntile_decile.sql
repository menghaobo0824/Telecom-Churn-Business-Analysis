-- =====================================================================
-- Q12 · 营收二八定律（NTILE）
-- 业务目的：Top 10% 用户贡献的营收占比，以及其余 90% 的对比
-- 表：data（MySQL 8.0）
-- 输出：2 行（Top 10% / 其余 90%），合计 7,043 人、16,056,168.70 元
-- 注意：revenue_share_pct 已经 ×100，30.83 表示 30.83%，不是 0.3083
-- =====================================================================

-- 业务目的：将用户按历史消费分为 10 等份，看头部与长尾各贡献多少营收。
WITH decile_revenue AS (
    SELECT
        customerID,
        TotalCharges,
        -- 按 TotalCharges 降序分为 10 个桶（1 代表最高）
        NTILE(10) OVER(ORDER BY TotalCharges DESC) AS revenue_decile,
        SUM(TotalCharges) OVER() AS total_revenue
    FROM data
)
SELECT
    'Top 10% 高净值用户' AS user_tier,
    COUNT(*) AS user_count,
    ROUND(SUM(TotalCharges), 2) AS tier_revenue,
    ROUND(SUM(TotalCharges) / MAX(total_revenue) * 100, 2) AS revenue_share_pct
FROM decile_revenue
WHERE revenue_decile = 1

UNION ALL

SELECT
    '其余 90% 用户' AS user_tier,
    COUNT(*) AS user_count,
    ROUND(SUM(TotalCharges), 2) AS tier_revenue,
    ROUND(SUM(TotalCharges) / MAX(total_revenue) * 100, 2) AS revenue_share_pct
FROM decile_revenue
WHERE revenue_decile > 1;
