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

# ── RSSHub 实例（可自建，默认用官方） ──
RSSHUB_BASE = os.getenv("RSSHUB_BASE", "https://rsshub.app")

# ── 新闻获取数量 ──
MAX_NEWS_PER_CATEGORY = 5

# ── 推送配置 ──
PUSH_TIME = "09:00"
TIMEZONE = "Asia/Shanghai"

# ── HTTP 请求配置 ──
REQUEST_TIMEOUT = 20  # 秒
HEADERS = {
    "User-Agent": "DailyNewsFeishu/2.0 (RSS Aggregator; GitHub Actions)"
}

# ── 各分类 RSS 源配置 ──
# 每个分类配置多个源，按优先级排序，失败时自动切换下一个
RSS_SOURCES = {
    "domestic": [
        # 国内时事政治
        {"url": f"{RSSHUB_BASE}/thepaper/featured",       "name": "澎湃新闻精选"},
        {"url": f"{RSSHUB_BASE}/cctv/world",              "name": "央视新闻"},
        {"url": f"{RSSHUB_BASE}/people/xjp",              "name": "人民网"},
        {"url": f"{RSSHUB_BASE}/huanqiu/china",           "name": "环球网"},
        {"url": f"{RSSHUB_BASE}/cls/telegraph",           "name": "财联社快讯"},
    ],
    "world": [
        # 国际时事政治
        {"url": "https://feeds.bbci.co.uk/zhongwen/simp/rss", "name": "BBC中文"},
        {"url": f"{RSSHUB_BASE}/huanqiu/global",              "name": "环球网国际"},
        {"url": f"{RSSHUB_BASE}/voa/chinese",                 "name": "VOA中文"},
        {"url": f"{RSSHUB_BASE}/nytimes/dual",                "name": "纽约时报双语"},
    ],
    "finance": [
        # 经济动态
        {"url": f"{RSSHUB_BASE}/wallstreetcn/global",    "name": "华尔街见闻"},
        {"url": f"{RSSHUB_BASE}/36kr/motif/最新",        "name": "36氪"},
        {"url": f"{RSSHUB_BASE}/cls/telegraph",           "name": "财联社电报"},
        {"url": f"{RSSHUB_BASE}/caixin/latest",           "name": "财新网"},
        {"url": f"{RSSHUB_BASE}/yicai/brief",             "name": "第一财经"},
    ],
    "career": [
        # 就业资讯
        {"url": f"{RSSHUB_BASE}/gov/mohrss/sy",          "name": "人社部"},
        {"url": f"{RSSHUB_BASE}/weibo/search/hot=就业",  "name": "微博就业话题"},
        {"url": f"{RSSHUB_BASE}/36kr/search/就业",       "name": "36氪就业"},
    ],
    "workplace": [
        # 职场动态
        {"url": f"{RSSHUB_BASE}/huxiu/channel/职场",    "name": "虎嗅职场"},
        {"url": f"{RSSHUB_BASE}/woshipm/popular",        "name": "人人都是产品经理"},
        {"url": f"{RSSHUB_BASE}/zhihu/daily",            "name": "知乎日报"},
    ],
    "food": [
        # 美食推荐
        {"url": f"{RSSHUB_BASE}/xiachufang/popular",     "name": "下厨房热门"},
        {"url": f"{RSSHUB_BASE}/meishitianxia/tag/家常菜", "name": "美食天下"},
    ],
    "travel": [
        # 旅游资讯
        {"url": f"{RSSHUB_BASE}/mafengwo/note",          "name": "马蜂窝游记"},
        {"url": f"{RSSHUB_BASE}/qyer/recommend",         "name": "穷游网推荐"},
    ],
    "fitness": [
        # 健身健康
        {"url": f"{RSSHUB_BASE}/zhihu/topic/19551207",   "name": "知乎健身"},
        {"url": f"{RSSHUB_BASE}/dxy/health",             "name": "丁香医生"},
        {"url": f"{RSSHUB_BASE}/keep/latest",            "name": "Keep精选"},
    ],
}

# ── 关键词过滤（就业/职场/健身的精确匹配） ──
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

# ── RSS 不可用时的静态备用内容 ──
FALLBACK_NEWS = {
    "domestic": [
        {"title": "📌 RSS源暂时不可用，请稍后刷新", "url": "", "source": "系统提示"},
    ],
    "world": [
        {"title": "📌 RSS源暂时不可用，请稍后刷新", "url": "", "source": "系统提示"},
    ],
}
