-- =====================================================================
-- Q15 · 消费排名追踪（LEAD）
-- 业务目的：相邻排名用户的合同与金额差
-- 表：data（MySQL 8.0）
-- =====================================================================

-- 业务目的：利用 LEAD 看排名前 20 的流失用户在列表中的下一个（消费稍微低一点的）用户是谁，对比两者的合同差异。
WITH revenue_ranking AS (
    SELECT 
        customerID,
        Contract,
        TotalCharges,
        LEAD(Contract, 1) OVER(ORDER BY TotalCharges DESC) AS next_user_contract,
        LEAD(TotalCharges, 1) OVER(ORDER BY TotalCharges DESC) AS next_user_charges
    FROM data
    WHERE Churn = 1
)
SELECT 
    customerID, 
    Contract, 
    TotalCharges, 
    next_user_contract, 
    next_user_charges,
    ROUND(TotalCharges - next_user_charges, 2) AS charge_gap
FROM revenue_ranking
LIMIT 20;
