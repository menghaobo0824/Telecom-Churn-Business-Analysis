-- =====================================================================
-- Q03 · 性别内合同流失占比
-- 业务目的：窗口函数 PARTITION BY
-- 表：data（MySQL 8.0）
-- =====================================================================

-- 业务目的：不折叠数据的情况下，看不同性别内部，哪种合同流失人数最多。
WITH user_contract AS (
    SELECT gender, Contract, Churn FROM data
)
SELECT 
    gender,
    Contract,
    SUM(Churn) AS churned_users,
    -- 计算该性别内部所有合同流失人数的总和
    SUM(SUM(Churn)) OVER(PARTITION BY gender) AS total_gender_churn,
    -- 计算当前合同类型流失人数占该性别的百分比
    ROUND(SUM(Churn) / SUM(SUM(Churn)) OVER(PARTITION BY gender) * 100, 2) AS pct_in_gender
FROM user_contract
GROUP BY gender, Contract
ORDER BY gender, pct_in_gender DESC;
