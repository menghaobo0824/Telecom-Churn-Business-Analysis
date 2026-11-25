-- =====================================================================
-- Q04 · 留存悬崖（生命周期）
-- 业务目的：0-6 个月新人期流失率最高
-- 表：data（MySQL 8.0）
-- =====================================================================

-- 业务目的：找出流失率最高的生命周期阶段，定位黄金干预窗口。
SELECT 
    CASE 
        WHEN tenure <= 6 THEN '1. 0-6个月'
        WHEN tenure <= 12 THEN '2. 6-12个月'
        WHEN tenure <= 24 THEN '3. 1-2年'
        ELSE '4. 2年以上'
    END AS lifecycle_stage,
    COUNT(*) AS total_users, 
    ROUND(AVG(Churn) * 100, 2) AS churn_rate_pct 
FROM data 
GROUP BY lifecycle_stage 
ORDER BY lifecycle_stage;
