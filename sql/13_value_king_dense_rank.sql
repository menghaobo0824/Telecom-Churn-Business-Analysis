-- =====================================================================
-- Q13 · 新老客消费之王（DENSE_RANK）
-- 业务目的：流失用户中的高价值个体
-- 表：data（MySQL 8.0）
-- =====================================================================

-- 业务目的：看流失用户中，不同在网时长里，哪种合同的用户最“值钱”。
WITH ranked_value AS (
    SELECT 
        customerID,
        Contract,
        CASE WHEN tenure <= 12 THEN '新客' ELSE '老客' END AS tenure_group,
        TotalCharges,
        DENSE_RANK() OVER(PARTITION BY (CASE WHEN tenure <= 12 THEN '新客' ELSE '老客' END) ORDER BY TotalCharges DESC) as dense_rank_val
    FROM data
    WHERE Churn = 1
)
SELECT * FROM ranked_value WHERE dense_rank_val <= 2;
