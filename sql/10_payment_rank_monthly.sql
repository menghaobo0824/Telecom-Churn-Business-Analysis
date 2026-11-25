-- =====================================================================
-- Q10 · 支付方式高危排名（RANK）
-- 业务目的：月付用户内部按流失率排名
-- 表：data（MySQL 8.0）
-- =====================================================================

-- 业务目的：在月付用户内部，对不同的支付方式按流失率排名。
SELECT 
    PaymentMethod,
    COUNT(*) AS total_users,
    ROUND(AVG(Churn) * 100, 2) AS churn_rate_pct,
    RANK() OVER(ORDER BY AVG(Churn) DESC) as danger_rank
FROM data
WHERE Contract = 'Month-to-month'
GROUP BY PaymentMethod;
