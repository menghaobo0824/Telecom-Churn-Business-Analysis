-- =====================================================================
-- Q02 · 用户画像 JOIN 流失
-- 业务目的：老年 / 有伴侣群体的流失差异
-- 表：data（MySQL 8.0）
-- =====================================================================

-- 业务目的：将用户基础属性与账单关联，看特定弱势群体（老年/无伴侣）是否流失更高。
WITH customer_profile AS (
    SELECT customerID, gender, SeniorCitizen, Partner, Dependents FROM data
),
billing_fact AS (
    SELECT customerID, Churn FROM data
)
SELECT 
    c.SeniorCitizen, 
    c.Partner, 
    COUNT(*) AS total_users,
    SUM(b.Churn) AS churned_users,
    ROUND(AVG(b.Churn) * 100, 2) AS churn_rate_pct
FROM customer_profile c
INNER JOIN billing_fact b ON c.customerID = b.customerID
GROUP BY c.SeniorCitizen, c.Partner
ORDER BY churn_rate_pct DESC;
