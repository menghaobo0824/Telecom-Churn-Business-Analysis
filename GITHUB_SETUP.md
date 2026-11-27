# 上传到 GitHub：可直接复制的操作清单

> 前提：你已经在 GitHub 上建好了空仓库。下面的命令按顺序复制执行即可。
> 全程只需要改 **一处**：命令块开头的 `$GH_USER` 和 `$REPO`。

---

## 0. 先装 Git（当前电脑没装）

在 PowerShell 里执行（winget 已就绪）：

```powershell
winget install --id Git.Git -e --source winget
```

装完 **关掉当前 PowerShell 窗口，重新打开一个**，然后验证：

```powershell
git --version
```

> 如果 `winget` 不可用：到 https://git-scm.com/download/win 下载安装包，一路默认下一步即可。

---

## 1. 进入项目目录并初始化仓库

```powershell
# ===================== 只改这两行 =====================
$GH_USER = "你的GitHub用户名"
$REPO    = "你的仓库名"
# =====================================================

Set-Location "C:\Users\lenovo1\Documents\deepseek-harness\default-workspace\telecom-churn-analysis"

git init -b main
git config user.name  "孟浩博"
git config user.email "2026104662@ruc.edu.cn"
```

---

## 2. 提交前自检（强烈建议看一眼）

```powershell
git status --short
```

应该看到 `README.md`、`sql/`、`src/`、`docs/`、`experiments/` 等；
**不应该**出现 `data/*.csv`、`results/*`、`__pycache__/`（已被 `.gitignore` 屏蔽）。

```powershell
git add .
git status --short | Measure-Object -Line
```

---

## 3. 首次提交

```powershell
git commit -m "feat: 15 条 SQL 诊断 + 流失预测 + A/B 实验 + 完整报告"
```

---

## 4. 关联远程仓库并推送

```powershell
git remote add origin "https://github.com/$GH_USER/$REPO.git"
git push -u origin main
```

- 第一次推送会弹出浏览器窗口让你登录 GitHub（Git Credential Manager），授权即可。
- 之后可以用 `git push` 直接推。

---

## 5. 验证

```powershell
git remote -v
git log --oneline -3
git branch -vv
```

浏览器打开 `https://github.com/$GH_USER/$REPO`，确认 15 个 `.sql`、`src/`、`docs/report.pdf` 都在。

---

## 常见问题

### ① 推送被拒：`rejected (fetch first)` / `non-fast-forward`
建仓库时勾选了 README / LICENSE，远程已有一个提交。先合并再推：

```powershell
git pull --rebase origin main
git push -u origin main
```

如果提示 unrelated histories：

```powershell
git pull --rebase origin main --allow-unrelated-histories
git push -u origin main
```

### ② 默认分支叫 `master`，不是 `main`

```powershell
git branch -M main
git push -u origin main
```

### ③ `remote origin already exists`

```powershell
git remote set-url origin "https://github.com/$GH_USER/$REPO.git"
```

### ④ 提示要密码 / `Authentication failed`
GitHub 早已不支持账号密码。两种解法：

- 用 Git Credential Manager（重装 Git for Windows 时自带，推送时会弹浏览器）
- 或生成 Personal Access Token：GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic) → 勾 `repo`，
  推送时用户名填 GitHub 用户名、密码填 token

### ⑤ 推送卡住 / 超时（国内网络）

```powershell
git config --global http.lowSpeedLimit 1000
git config --global http.lowSpeedTime 30
```

仍失败则挂代理后再推（把端口改成你自己的）：

```powershell
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
# 用完记得取消：
# git config --global --unset http.proxy
# git config --global --unset https.proxy
```

### ⑥ 中文文件名显示成乱码

```powershell
git config --global core.quotepath false
```

### ⑦ 误把数据文件提交了

```powershell
git rm --cached data/telco.csv
git commit -m "chore: 移除原始数据，改由 data/README.md 说明获取方式"
```

---

## 不想用命令行？两个替代方案

### 方案 B：GitHub Desktop（图形化，5 分钟）

1. 下载安装 https://desktop.github.com/
2. 登录 GitHub 账号
3. `File → Add local repository` → 选择 `telecom-churn-analysis` 文件夹
4. 左下角填提交信息 → `Commit to main` → 右上角 `Publish repository`
5. 取消勾选 "Keep this code private" 前先确认要不要公开

### 方案 C：网页上传（最快，但没有提交历史）

1. 打开仓库页 → `Add file → Upload files`
2. 把 `telecom-churn-analysis` 里的文件/文件夹拖进去
3. 底部填 "Add project files" → `Commit changes`

> 注意：网页上传**不能**一次拖整个文件夹里嵌套的子目录（GitHub 支持拖文件夹，但空目录会丢失），
> 且 `data/`、`results/` 这类空目录不会上传，属正常现象。

---

## 推送完成后的 5 个加分动作

### 1. 填写仓库简介与 Topics

仓库首页右侧 `About` → 齿轮图标：

- Description：`电信用户流失归因与挽留策略分析 | SQL 15 条 + 机器学习 + A/B 实验 | Python / MySQL / FineBI`
- Topics（逐个添加）：`data-analysis` `sql` `mysql` `churn-prediction` `machine-learning` `ab-testing` `python` `business-analytics` `portfolio`

### 2. 打一个 Release，把报告挂上去

网页：`Releases → Draft a new release`

- Tag：`v1.0.0`
- Title：`v1.0.0 - 完整分析报告与 SQL 脚本`
- 附件：把 `docs/report.pdf` 拖进去

或用 gh CLI（需先 `winget install --id GitHub.cli`）：

```powershell
gh auth login
gh release create v1.0.0 "docs/report.pdf" --title "v1.0.0 完整分析报告" --notes "15 条 SQL + 流失预测 + A/B 实验"
```

### 3. 打开 CI 徽章

推送后 `Actions` 会自动跑一次。把徽章加到 README 顶部：

```markdown
![ci](https://github.com/你的用户名/你的仓库名/actions/workflows/ci.yml/badge.svg)
```

### 4. 保护主分支（可选）

GitHub → Settings → Branches → Add rule → 分支名 `main` → 勾选
`Require a pull request before merging` + `Require status checks to pass`（选 `pipeline / smoke-test`）。

### 5. 简历 / 作品集里怎么引用

> 电信用户流失归因与挽留策略分析｜GitHub: https://github.com/menghaobo0824/Telecom-Churn-Business-Analysis
> 用 15 条 SQL 完成分层-归因-量化-排序，定位 0–6 个月 52.94% 的留存悬崖与月付+电子支票 53.73% 的高危组合；
> 用 scikit-learn 建立流失预测并按业务收益寻优阈值；设计 A/B 实验（每组 2,451 人）验证挽留策略。

---

## 一页速查

```powershell
winget install --id Git.Git -e --source winget     # 装 Git（一次性）
# 重开 PowerShell
$GH_USER = "你的用户名"; $REPO = "你的仓库名"
Set-Location "C:\Users\lenovo1\Documents\deepseek-harness\default-workspace\telecom-churn-analysis"
git init -b main
git config user.name "孟浩博"; git config user.email "2026104662@ruc.edu.cn"
git add .
git commit -m "feat: 15 条 SQL 诊断 + 流失预测 + A/B 实验 + 完整报告"
git remote add origin "https://github.com/$GH_USER/$REPO.git"
git push -u origin main
```
