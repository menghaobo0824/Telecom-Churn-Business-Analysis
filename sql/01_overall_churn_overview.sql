-- =====================================================================
-- Q01 · 整体流失大盘
-- 业务目的：全量用户规模、流失人数与流失率
-- 表：data（MySQL 8.0）
-- =====================================================================

SELECT 
    COUNT(*) AS total_users, 
    SUM(Churn) AS churned_users, 
    ROUND(AVG(Churn) * 100, 2) AS churn_rate_pct 
FROM data;
