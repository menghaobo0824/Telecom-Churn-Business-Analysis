-- =====================================================================
-- Q06 · 高客单价流失名单（SELF JOIN）
-- 业务目的：月租高于同合同均值的流失用户
-- 表：data（MySQL 8.0）
-- =====================================================================

-- 业务目的：找出那些月租费高于同类合同平均水平的流失用户，评估高价值客户的流失状况。
WITH avg_charges AS (
    SELECT Contract, AVG(MonthlyCharges) AS avg_monthly FROM data GROUP BY Contract
)
SELECT 
    d.customerID,
    d.Contract,
    d.MonthlyCharges,
    ROUND(a.avg_monthly, 2) AS avg_contract_monthly,
    ROUND(d.MonthlyCharges - a.avg_monthly, 2) AS diff_from_avg
FROM data d
INNER JOIN avg_charges a ON d.Contract = a.Contract
WHERE d.Churn = 1 AND d.MonthlyCharges > a.avg_monthly
ORDER BY diff_from_avg DESC
LIMIT 10;
