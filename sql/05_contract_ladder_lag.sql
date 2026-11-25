-- =====================================================================
-- Q05 · 合同阶梯与 LAG 环比
-- 业务目的：合同期延长带来的流失率降幅
-- 表：data（MySQL 8.0）
-- =====================================================================

-- 业务目的：对比不同合同类型流失率的“环比差值”，看绑定期延长带来的边际效益。
WITH contract_churn AS (
    SELECT 
        Contract, 
        ROUND(AVG(Churn) * 100, 2) AS churn_rate_pct,
        -- 按合同流失率降序，获取上一行的流失率
        LAG(ROUND(AVG(Churn) * 100, 2), 1) OVER(ORDER BY AVG(Churn) DESC) AS previous_churn_rate
    FROM data
    GROUP BY Contract
)
SELECT 
    Contract, 
    churn_rate_pct,
    previous_churn_rate,
    -- 计算下降幅度
    ROUND(previous_churn_rate - churn_rate_pct, 2) AS rate_drop_pct
FROM contract_churn
ORDER BY churn_rate_pct DESC;
