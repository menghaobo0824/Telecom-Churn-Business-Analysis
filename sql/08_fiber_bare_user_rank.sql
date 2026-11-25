-- =====================================================================
-- Q08 · 光纤裸奔用户（ROW_NUMBER）
-- 业务目的：无任何增值服务的高危用户
-- 表：data（MySQL 8.0）
-- =====================================================================

-- 业务目的：没买任何增值服务的光纤用户流失最高。按合同类型分组，给这些高危用户打个排名。
WITH vulnerable_users AS (
    SELECT 
        customerID, 
        Contract, 
        MonthlyCharges,
        Churn,
        ROW_NUMBER() OVER(PARTITION BY Contract ORDER BY MonthlyCharges DESC) as risk_rank
    FROM data
    WHERE InternetService = 'Fiber optic' 
      AND OnlineSecurity = 'No' 
      AND TechSupport = 'No'
      AND Churn = 1
)
SELECT * FROM vulnerable_users WHERE risk_rank <= 3;
