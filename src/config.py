"""
配置模块 - 从环境变量读取所有配置
本地开发使用 .env 文件，GitHub Actions 使用 Secrets
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ── 飞书配置 ──
FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "")

# ── 天行数据 API（可选兜底） ──
TIANAPI_KEY = os.getenv("TIANAPI_KEY", "")

# ── 新闻获取数量 ──
MAX_NEWS_PER_CATEGORY = 5

# ── 推送配置 ──
PUSH_TIME = "09:00"
TIMEZONE = "Asia/Shanghai"

# ── HTTP 请求配置 ──
REQUEST_TIMEOUT = 20  # 秒
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; DailyNewsBot/3.0; +https://github.com/news-bot)"
    )
}

# ── RSSHub 多镜像（按优先级排序，一个不通自动换下一个） ──
# 自建实例最稳定，建议有条件时用环境变量 RSSHUB_BASE 指向自建地址
_custom_rsshub = os.getenv("RSSHUB_BASE", "")
RSSHUB_MIRRORS = [_custom_rsshub] if _custom_rsshub else []
RSSHUB_MIRRORS += [
    "https://rsshub.rssforever.com",
    "https://rsshub.cry33.com",
    "https://rsshub.feeded.xyz",
    "https://rsshub.app",               # 官方实例，放最后
]

# ── Google News RSS 基础 URL ──
# Google News 从全球任何地方都能稳定访问，聚合多源新闻，支持中文
GOOGLE_NEWS_BASE = "https://news.google.com/rss"

# ── 各分类 RSS 源配置 ──
# 策略：直连RSS（最可靠）→ Google News（稳定聚合）→ RSSHub镜像（补充）
# 格式：{"url": "url或{rsshub}占位", "name": "来源名", "via": "direct|google|rsshub"}
RSS_SOURCES = {
    "domestic": [
        # ★ 直连 Google News 多角度搜索（最稳定，自动聚合最新新闻）
        {"url": f"{GOOGLE_NEWS_BASE}/search?q=中国+国内+时政&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
         "name": "Google新闻-国内时政", "via": "direct"},
        {"url": f"{GOOGLE_NEWS_BASE}/search?q=政治+政策+改革+发展&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
         "name": "Google新闻-政治政策", "via": "direct"},
        {"url": f"{GOOGLE_NEWS_BASE}/search?q=社会+民生+教育+医疗&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
         "name": "Google新闻-社会民生", "via": "direct"},
        # ★ RSSHub 镜像补充
        {"url": "{rsshub}/thepaper/featured",  "name": "澎湃新闻精选", "via": "rsshub"},
        {"url": "{rsshub}/people/xjp",         "name": "人民网", "via": "rsshub"},
        {"url": "{rsshub}/huanqiu/china",      "name": "环球网", "via": "rsshub"},
    ],
    "world": [
        # ★ 直连 RSS，多重保险
        {"url": f"{GOOGLE_NEWS_BASE}/search?q=国际新闻+世界&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
         "name": "Google新闻-国际", "via": "direct"},
        {"url": f"{GOOGLE_NEWS_BASE}/search?q=全球+外交+政治+冲突&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
         "name": "Google新闻-全球政治", "via": "direct"},
        {"url": "https://feeds.bbci.co.uk/zhongwen/simp/rss", "name": "BBC中文", "via": "direct"},
        {"url": "https://rss.dw.com/rdf/rss-chi-all", "name": "德国之声中文", "via": "direct"},
        # ★ RSSHub 镜像补充
        {"url": "{rsshub}/huanqiu/global",     "name": "环球网国际", "via": "rsshub"},
        {"url": "{rsshub}/voa/chinese",        "name": "VOA中文", "via": "rsshub"},
    ],
    "finance": [
        # ★ 36氪直连 RSS
        {"url": "https://36kr.com/feed",       "name": "36氪", "via": "direct"},
        {"url": f"{GOOGLE_NEWS_BASE}/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0JYcG9MVlJYS0FBUAE?hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
         "name": "Google新闻-财经", "via": "direct"},
        {"url": "{rsshub}/wallstreetcn/global","name": "华尔街见闻", "via": "rsshub"},
        {"url": "{rsshub}/cls/telegraph",      "name": "财联社电报", "via": "rsshub"},
        {"url": "{rsshub}/yicai/brief",        "name": "第一财经", "via": "rsshub"},
    ],
    "career": [
        {"url": f"{GOOGLE_NEWS_BASE}/search?q=就业+招聘+求职&hl=zh-CN&gl=CN&ceid=CN:zh-Hans",
         "name": "Google新闻-就业", "via": "direct"},
        {"url": "{rsshub}/gov/mohrss/sy",      "name": "人社部", "via": "rsshub"},
        {"url": "{rsshub}/weibo/search/hot=就业招聘", "name": "微博就业", "via": "rsshub"},
    ],
    "workplace": [
        # ★ 直连 RSS
        {"url": "https://www.huxiu.com/rss/0.xml", "name": "虎嗅网", "via": "direct"},
        # ★ Google News 多角度搜索
        {"url": f"{GOOGLE_NEWS_BASE}/search?q=职场&hl=zh-CN&gl=US&ceid=US:en",
         "name": "Google新闻-职场", "via": "direct"},
        {"url": f"{GOOGLE_NEWS_BASE}/search?q=工作+管理+创业&hl=zh-CN&gl=US&ceid=US:en",
         "name": "Google新闻-工作管理", "via": "direct"},
        {"url": f"{GOOGLE_NEWS_BASE}/search?q=career+job+workplace&hl=en&gl=US&ceid=US:en",
         "name": "Google News-workplace", "via": "direct"},
        # ★ RSSHub 镜像
        {"url": "{rsshub}/woshipm/popular",    "name": "人人都是产品经理", "via": "rsshub"},
        {"url": "{rsshub}/zhihu/daily",        "name": "知乎日报", "via": "rsshub"},
        {"url": "{rsshub}/huxiu/channel/职场", "name": "虎嗅职场", "via": "rsshub"},
    ],
    "food": [
        # ★ Google News 多角度（中美双区搜索）
        {"url": f"{GOOGLE_NEWS_BASE}/search?q=美食&hl=zh-CN&gl=US&ceid=US:en",
         "name": "Google新闻-美食", "via": "direct"},
        {"url": f"{GOOGLE_NEWS_BASE}/search?q=菜谱+烹饪+餐厅&hl=zh-CN&gl=US&ceid=US:en",
         "name": "Google新闻-烹饪", "via": "direct"},
        {"url": f"{GOOGLE_NEWS_BASE}/search?q=food+recipe+cooking&hl=en&gl=US&ceid=US:en",
         "name": "Google News-food", "via": "direct"},
        # ★ RSSHub 镜像
        {"url": "{rsshub}/xiachufang/popular",  "name": "下厨房热门", "via": "rsshub"},
        {"url": "{rsshub}/meishitianxia/tag/家常菜", "name": "美食天下", "via": "rsshub"},
        {"url": "{rsshub}/douban/explore/美食", "name": "豆瓣美食", "via": "rsshub"},
    ],
    "travel": [
        # ★ Google News 多角度
        {"url": f"{GOOGLE_NEWS_BASE}/search?q=旅游&hl=zh-CN&gl=US&ceid=US:en",
         "name": "Google新闻-旅游", "via": "direct"},
        {"url": f"{GOOGLE_NEWS_BASE}/search?q=旅行+攻略+景点&hl=zh-CN&gl=US&ceid=US:en",
         "name": "Google新闻-旅行攻略", "via": "direct"},
        {"url": f"{GOOGLE_NEWS_BASE}/search?q=travel+tourism+destination&hl=en&gl=US&ceid=US:en",
         "name": "Google News-travel", "via": "direct"},
        # ★ RSSHub 镜像
        {"url": "{rsshub}/mafengwo/note",       "name": "马蜂窝游记", "via": "rsshub"},
        {"url": "{rsshub}/qyer/recommend",      "name": "穷游网推荐", "via": "rsshub"},
    ],
    "fitness": [
        # ★ Google News 多角度
        {"url": f"{GOOGLE_NEWS_BASE}/search?q=健身&hl=zh-CN&gl=US&ceid=US:en",
         "name": "Google新闻-健身", "via": "direct"},
        {"url": f"{GOOGLE_NEWS_BASE}/search?q=运动+减肥+健康+养生&hl=zh-CN&gl=US&ceid=US:en",
         "name": "Google新闻-运动健康", "via": "direct"},
        {"url": f"{GOOGLE_NEWS_BASE}/search?q=fitness+exercise+health+workout&hl=en&gl=US&ceid=US:en",
         "name": "Google News-fitness", "via": "direct"},
        # ★ RSSHub 镜像
        {"url": "{rsshub}/zhihu/topic/19551207", "name": "知乎健身", "via": "rsshub"},
        {"url": "{rsshub}/dxy/health",           "name": "丁香医生", "via": "rsshub"},
        {"url": "{rsshub}/keep/latest",          "name": "Keep精选", "via": "rsshub"},
    ],
}

# ── 关键词过滤 ──
CATEGORY_KEYWORDS = {
    "career": [
        "就业", "招聘", "求职", "岗位", "人才", "毕业生", "薪资",
        "裁员", "校招", "社招", "公务员", "事业单位", "国企", "实习",
        "收入", "职业", "面试", "简历", "打工", "灵活就业", "创业",
    ],
    "workplace": [
        "职场", "上班", "加班", "领导", "管理", "跳槽", "副业",
        "远程办公", "OKR", "KPI", "涨薪", "年终奖", "晋升", "同事",
        "效率", "技能", "学习", "考证", "转行", "裸辞",
    ],
    "fitness": [
        "健身", "运动", "跑步", "瑜伽", "减肥", "瘦身", "增肌",
        "减脂", "健康", "锻炼", "体能", "马拉松", "游泳", "骑行",
        "饮食", "营养", "睡眠", "拉伸", "力量", "有氧",
    ],
}

# ── 静态备用内容 ──
FALLBACK_NEWS = {
    "domestic": [
        {"title": "📌 今日RSS源响应较慢，建议稍后手动刷新", "url": "", "source": "系统提示"},
    ],
    "world": [
        {"title": "📌 今日RSS源响应较慢，建议稍后手动刷新", "url": "", "source": "系统提示"},
    ],
}
