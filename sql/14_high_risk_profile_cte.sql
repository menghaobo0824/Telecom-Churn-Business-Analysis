-- =====================================================================
-- Q14 · 高危用户全景画像（CTE）
-- 业务目的：多条件叠加的终极高危名单
-- 表：data（MySQL 8.0）
-- =====================================================================

-- 业务目的：将前面查出的“高危特征”（月付、光纤、电子支票、新客）合并，拉出一份终极高危名单。
WITH high_risk_profile AS (
    SELECT customerID, Contract, PaymentMethod, InternetService, tenure
    FROM data
    WHERE Contract = 'Month-to-month'
      AND PaymentMethod = 'Electronic check'
      AND InternetService = 'Fiber optic'
      AND tenure <= 6
      AND Churn = 1
)
SELECT 
    h.customerID,
    h.tenure,
    d.MonthlyCharges,
    d.TotalCharges,
    h.InternetService
FROM high_risk_profile h
INNER JOIN data d ON h.customerID = d.customerID
ORDER BY d.TotalCharges DESC
LIMIT 5;
