# 🦆 投研鸭 EdgeOne Pages 部署指南

> 版本: v1.0 | 日期: 2026-04-08 | 适合纯小白操作

## 📋 前置条件

- ✅ 腾讯云账号（你已经有了）
- ✅ CodeBuddy IDE（你正在用）
- ✅ 代码已准备好（`public/` + `edge-functions/`）

---

## 🚀 分步操作指南

### 第 1 步：通过 CodeBuddy 部署到 EdgeOne Pages

1. 看 CodeBuddy IDE **右侧边栏** 或 **对话框底部**
2. 找到 **EdgeOne Pages** 的图标/按钮（绿色，你昨天用过）
3. 点击 **"部署"**
4. 选择部署目录为 `touyanduck-api`（项目子目录）
   - **重要**：部署的是 `touyanduck-api/` 这个文件夹，不是项目根目录
   - 输出目录: `public`
5. 等待部署完成（通常 1-2 分钟）
6. 部署成功后会得到一个 URL，类似：`https://touyanduck-api-xxx.edgeone.run`

**记下这个 URL！** 后面要用。

### 第 2 步：验证静态文件可访问

在浏览器打开以下地址（把 `YOUR_DOMAIN` 替换为你刚得到的域名）：

```
https://YOUR_DOMAIN/               → 应该看到投研鸭 API 首页
https://YOUR_DOMAIN/briefing.md    → 应该看到今天的简报 Markdown
https://YOUR_DOMAIN/meta.json      → 应该看到 JSON 数据
```

如果都能看到，说明静态文件部署成功 ✅

### 第 3 步：配置 KV 存储（在腾讯云控制台）

这一步需要去网页操作：

1. 打开浏览器，访问 [EdgeOne Pages 控制台](https://pages.edgeone.ai)
2. 用你的腾讯云账号登录
3. 找到你刚部署的 `touyanduck-api` 项目
4. 点击左侧菜单 **"KV 存储"**
5. 点击 **"立即申请"**（第一次使用需要开通，免费）
6. 创建一个命名空间，名称填：`touyanduck-kv`
7. 创建后，点击 **"绑定项目"**
8. 选择你的 `touyanduck-api` 项目
9. **变量名** 填：`TOUYANDUCK_KV`（⚠️ 必须和代码里一致！）
10. 保存

### 第 4 步：设置环境变量（同步 Token）

1. 在 EdgeOne Pages 控制台，进入你的项目
2. 点击 **"设置"** → **"环境变量"**
3. 添加一个变量：
   - 变量名: `SYNC_TOKEN`
   - 变量值: `touyanduck-sync-2026`（你可以改成任意密码）
4. 保存

### 第 5 步：重新部署（让 KV 绑定和环境变量生效）

**重要**：绑定 KV 和设置环境变量后，需要重新部署一次才能生效！

- 在 CodeBuddy 里再点一次 EdgeOne Pages 的"部署"按钮
- 或者在控制台找到最近一次部署，点"重新部署"

### 第 6 步：测试 API 端点

部署成功后，在终端执行：

```bash
# 替换为你的实际域名
DOMAIN="https://touyanduck-api-xxx.edgeone.run"

# 测试日期列表（应该返回空数组，因为还没推数据）
curl -s "$DOMAIN/api/dates"

# 测试简报端点
curl -s "$DOMAIN/api/briefing"

# 测试预测市场
curl -s "$DOMAIN/api/predictions"
```

### 第 7 步：同步今天的数据到 KV

```bash
# 先设置环境变量（替换为你的实际域名）
export TOUYANDUCK_API_URL="https://touyanduck-api-xxx.edgeone.run"

# 执行同步脚本
python3 /Users/zewujiang/Desktop/AICo/codebuddy-invest/.codebuddy/skills/touyanduck-daily/scripts/sync_to_edgeone_kv.py \
  "/Users/zewujiang/Desktop/AICo/codebuddy-invest/workflows/investment_agent_data/miniapp_sync/" \
  "2026-04-08"
```

看到 `✅ 同步成功!` 就说明数据已经写入 KV 了。

### 第 8 步：验证完整 API

```bash
DOMAIN="https://touyanduck-api-xxx.edgeone.run"

# 再次测试（这次应该有数据了）
curl -s "$DOMAIN/api/briefing" | python3 -m json.tool | head -20
curl -s "$DOMAIN/api/dates" | python3 -m json.tool
curl -s "$DOMAIN/api/predictions" | python3 -m json.tool
curl -s "$DOMAIN/api/archive?date=2026-04-08" | python3 -m json.tool | head -20
```

---

## 🔧 常见问题

### Q: KV 变量名填错了怎么办？
A: 去控制台 → KV 存储 → 解绑 → 重新绑定，变量名必须是 `TOUYANDUCK_KV`

### Q: 部署后 /api/xxx 返回 404？
A: edge-functions 目录可能没有被识别，确认：
1. 目录名是 `edge-functions`（不是 `functions`）
2. 项目根目录是 `touyanduck-api/`
3. 重新部署一次

### Q: 同步脚本报"连接失败"？
A: 检查 URL 是否正确，确保包含 `https://`

### Q: 同步脚本报"鉴权失败"？
A: 检查环境变量 `SYNC_TOKEN` 和脚本里的 token 是否一致

---

## 📁 文件结构总览

```
touyanduck-api/
├── public/                        ← 静态文件（浏览器直接访问）
│   ├── index.html                 ← 首页
│   ├── briefing.md                ← 最新简报
│   ├── briefing.json              ← 简报 JSON
│   ├── markets.json               ← 市场数据
│   ├── watchlist.json             ← 板块追踪
│   ├── radar.json                 ← 风险雷达
│   └── meta.json                  ← 元数据
│
├── edge-functions/                ← 动态 API
│   └── api/
│       ├── briefing.js            ← GET /api/briefing
│       ├── dates.js               ← GET /api/dates
│       ├── archive.js             ← GET /api/archive?date=
│       ├── trend.js               ← GET /api/trend?days=
│       ├── smart-money.js         ← GET /api/smart-money?fund=
│       ├── search.js              ← GET /api/search?q=
│       ├── predictions.js         ← GET /api/predictions
│       └── sync.js                ← POST /api/sync（数据写入）
```
