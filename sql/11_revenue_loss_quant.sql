-- =====================================================================
-- Q11 · 流失金额量化（MRR 损失）
-- 业务目的：流失人数折算成真金白银
-- 表：data（MySQL 8.0）
-- =====================================================================

-- 业务目的：将流失人数折算成真金白银（MRR损失）。
SELECT 
    COUNT(*) AS churned_users, 
    ROUND(SUM(MonthlyCharges), 2) AS monthly_revenue_loss, 
    ROUND(AVG(MonthlyCharges), 2) AS avg_arpu_lost
FROM data 
WHERE Churn = 1;
