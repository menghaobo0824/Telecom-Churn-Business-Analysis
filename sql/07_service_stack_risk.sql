-- =====================================================================
-- Q07 · 服务组合风险（多表关联）
-- 业务目的：网络类型 × 安全 × 技术支持
-- 表：data（MySQL 8.0）
-- =====================================================================

-- 业务目的：将网络类型、在线安全、技术支持关联，看哪些服务组合最留不住人。
WITH service_details AS (
    SELECT customerID, InternetService, OnlineSecurity, TechSupport FROM data
),
churn_status AS (
    SELECT customerID, Churn FROM data
)
SELECT 
    s.InternetService,
    s.OnlineSecurity,
    s.TechSupport,
    COUNT(*) AS total_users,
    ROUND(AVG(c.Churn) * 100, 2) AS churn_rate_pct
FROM service_details s
INNER JOIN churn_status c ON s.customerID = c.customerID
GROUP BY s.InternetService, s.OnlineSecurity, s.TechSupport
HAVING COUNT(*) > 50
ORDER BY churn_rate_pct DESC
LIMIT 5;
