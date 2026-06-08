# 📰 每日新闻汇总推送到飞书

每日早 9:00 自动汇总国内外时事政治、经济、就业、职场、美食、旅游、健身等 8 大类资讯，通过飞书机器人推送到群聊。

> 🖥️ 基于 GitHub Actions 定时运行，**电脑关机也能正常推送**
> 📡 **RSS 多源聚合**，直接从权威媒体获取一手资讯，准确可靠

---

## 🏗️ 架构

```
GitHub Actions (每日 UTC 1:00 = 北京时间 9:00)
    │
    ▼
┌─────────────────────────────────────────┐
│          news_fetcher.py (RSS 多源聚合)  │
│                                          │
│  🏛️ 国内: 澎湃新闻 / 央视 / 人民网 / 环球网   │
│  🌍 国际: BBC中文 / 环球网国际 / VOA中文    │
│  💰 经济: 华尔街见闻 / 36氪 / 财联社 / 财新  │
│  💼 就业: 人社部 / 微博就业话题 / 36氪      │
│  🏢 职场: 虎嗅 / 人人都是产品经理 / 知乎    │
│  🍜 美食: 下厨房 / 美食天下                │
│  ✈️ 旅游: 马蜂窝 / 穷游网                  │
│  💪 健身: 知乎健身 / 丁香医生 / Keep       │
│                                          │
│  来源不可用时 → 自动切换备用源 → 天行数据兜底  │
└─────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────┐
│   formatter.py + feishu_sender.py        │
│   飞书交互式卡片消息 → 群聊 Webhook        │
└─────────────────────────────────────────┘
```

---

## 🚀 快速开始（只需 2 步）

### 第1步：获取飞书 Webhook URL

1. 打开飞书 PC 端，进入目标群聊
2. 群设置 → 群机器人 → 添加机器人 → **自定义机器人**
3. 设置机器人名称（如「每日新闻」）和头像
4. **安全设置**：选择「自定义关键词」，填写 `每日新闻`
5. 复制 Webhook URL（格式：`https://open.feishu.cn/open-apis/bot/v2/hook/xxx`）

> ✅ RSS 方案**无需注册天行数据**，飞书 Webhook 是唯一必填项。

### 第2步：配置 GitHub 并部署

1. 将本项目上传到 GitHub 仓库（推荐**公开**仓库，Actions 无限免费）
2. 仓库 → **Settings** → **Secrets and variables** → **Actions**
3. 点击 **New repository secret**，添加：

   | Secret 名称 | 值 |
   |---|---|
   | `FEISHU_WEBHOOK_URL` | 你的飞书 Webhook URL |

4. 进入 **Actions** → **每日新闻推送到飞书** → **Run workflow** 手动测试
5. 约 1 分钟后检查飞书群是否收到消息

✅ **完成！之后每天早上 9:00 自动推送，电脑关机也能运行。**

---

## 📡 RSS 新闻来源（全部免费、直接、一手）

| 分类 | 主要来源 | 备用来源 | 可靠性 |
|------|---------|---------|--------|
| 🏛️ 国内时事 | 澎湃新闻、央视新闻 | 人民网、环球网 | ⭐⭐⭐⭐⭐ |
| 🌍 国际时事 | BBC中文、环球网国际 | VOA中文、NYT双语 | ⭐⭐⭐⭐⭐ |
| 💰 经济动态 | 华尔街见闻、36氪、财联社 | 财新网、第一财经 | ⭐⭐⭐⭐⭐ |
| 💼 就业资讯 | 人社部、微博就业话题 | 36氪就业 | ⭐⭐⭐⭐ |
| 🏢 职场动态 | 虎嗅、人人都是产品经理 | 知乎日报 | ⭐⭐⭐⭐ |
| 🍜 美食推荐 | 下厨房、美食天下 | — | ⭐⭐⭐⭐ |
| ✈️ 旅游资讯 | 马蜂窝、穷游网 | — | ⭐⭐⭐⭐ |
| 💪 健身健康 | 知乎健身、丁香医生、Keep | 健康知识 | ⭐⭐⭐⭐ |

> 💡 每个分类配置了 3-5 个 RSS 源，一个源失败自动切换下一个。全部失败时启用天行数据兜底（需配置 `TIANAPI_KEY`）。多源之间有标题相似度去重，保证不重复。

---

## 📂 项目结构

```
daily-news-feishu/
├── .github/workflows/
│   └── daily-push.yml          # GitHub Actions 定时任务 (UTC 1:00)
├── src/
│   ├── main.py                 # 主入口，编排流程
│   ├── news_fetcher.py         # RSS 多源聚合引擎
│   ├── formatter.py            # 飞书交互式卡片格式化
│   ├── feishu_sender.py        # 飞书 Webhook 发送
│   └── config.py               # RSS源配置 + 关键词 + 环境变量
├── .env.example                # 本地开发密钥模板
├── requirements.txt            # Python 依赖
└── README.md
```

---

## 🖥️ 本地运行

```bash
git clone <your-repo-url> && cd daily-news-feishu
cp .env.example .env             # 编辑 .env 填飞书 Webhook
pip install -r requirements.txt  # 安装 feedparser + requests + lxml
python src/main.py               # 立即运行一次
```

`.env` 文件：
```
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/xxx
# TIANAPI_KEY=          # 可选：RSS全部失败时的兜底
# RSSHUB_BASE=https://rsshub.app  # 可选：自建RSSHub实例
```

---

## ⚙️ 自定义

| 需求 | 操作 |
|------|------|
| 改推送时间 | 编辑 `daily-push.yml` cron 表达式（UTC时间，+8=北京） |
| 改新闻条数 | 编辑 `config.py` → `MAX_NEWS_PER_CATEGORY` |
| 换 RSS 源 | 编辑 `config.py` → `RSS_SOURCES`，增删改源 |
| 自建 RSSHub | 设置环境变量 `RSSHUB_BASE=https://你的域名` |
| 只工作日推送 | cron 改为 `0 1 * * 1-5` |

---

## 🔒 安全与合法

- 仅抓取各媒体公开的 **RSS/Atom Feed**，不涉及爬虫侵权
- 每条新闻保留**原文链接**和来源标注
- API 密钥存储在 **GitHub Secrets** 加密环境变量中
- 飞书 Webhook 通过**自定义关键词**防滥用

---

## ❓ FAQ

**Q: RSS 比天行数据好在哪里？**
A: 直接来自原始媒体，来源透明可查证；免费无限制；不依赖第三方聚合商。

**Q: RSSHub 是什么？需要自己部署吗？**
A: [RSSHub](https://github.com/DIYgod/RSSHub) 是一个开源项目，为没有 RSS 的网站生成 RSS。默认使用官方实例 `rsshub.app`，稳定性尚可。如果追求极致稳定，建议自建（一键 Docker 部署）。

**Q: 某天没收到推送？**
A: GitHub Actions → 查看运行日志。常见原因：RSSHub 官方实例限流（自建可解决）、飞书 Webhook 过期。

**Q: 公开仓库 vs 私有仓库？**
A: 推荐公开仓库（Actions 无限免费）。私有仓库每月 2000 分钟，每天 1 分钟推送绰绰有余。
