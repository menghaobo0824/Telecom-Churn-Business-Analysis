-- =====================================================================
-- Q09 · 死亡组合（合同 × 支付）
-- 业务目的：月付 + 电子支票流失率最高
-- 表：data（MySQL 8.0）
-- =====================================================================

-- 业务目的：找出流失率极高的多重特征组合，锁定核心干预靶心。
SELECT 
    Contract, 
    PaymentMethod, 
    COUNT(*) AS total_users, 
    ROUND(AVG(Churn) * 100, 2) AS churn_rate_pct
FROM data 
GROUP BY Contract, PaymentMethod 
HAVING COUNT(*) > 100 
ORDER BY churn_rate_pct DESC 
LIMIT 5;
