-- =====================================================================
-- Q12 · 营收二八定律（NTILE）
-- 业务目的：Top 10% 用户贡献的营收占比
-- 表：data（MySQL 8.0）
-- =====================================================================

-- 业务目的：将用户按历史消费分为 10 等份，看 Top 10% 用户贡献了多少营收。
WITH decile_revenue AS (
    SELECT 
        customerID,
        TotalCharges,
        -- 按 TotalCharges 降序分为 10 个桶（1代表最高）
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
WHERE revenue_decile = 1;
