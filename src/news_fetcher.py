"""
新闻获取模块 - RSS 多源聚合（主力）
支持 RSS 2.0 / Atom 格式解析，自动去重、多源容错
天行数据 API 作为可选兜底
"""
import hashlib
from datetime import datetime
from difflib import SequenceMatcher

import feedparser
import requests

from config import (
    RSS_SOURCES,
    MAX_NEWS_PER_CATEGORY,
    CATEGORY_KEYWORDS,
    FALLBACK_NEWS,
    HEADERS,
    REQUEST_TIMEOUT,
    TIANAPI_KEY,
)


# ── 工具函数 ──

def _similar(a: str, b: str, threshold: float = 0.75) -> bool:
    """判断两个标题是否相似（用于去重）"""
    if not a or not b:
        return False
    # 快速路径：其中一个包含另一个
    short, long = (a, b) if len(a) <= len(b) else (b, a)
    if len(short) >= 6 and short[:6] in long:
        return True
    return SequenceMatcher(None, a[:60], b[:60]).ratio() >= threshold


def _title_hash(title: str) -> str:
    """标题的短哈希，用于快速去重"""
    return hashlib.md5(title[:80].encode()).hexdigest()[:12]


def _fetch_rss(url: str) -> list[dict]:
    """
    获取并解析单个 RSS 源
    返回: [{"title": str, "url": str, "source": str, "summary": str}, ...]
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        resp.raise_for_status()

        # feedparser 可以直接解析字符串
        feed = feedparser.parse(resp.content)

        if feed.bozo and not feed.entries:
            print(f"      [WARN] RSS 解析异常: {feed.bozo_exception}")
            return []

        entries = []
        for item in feed.entries:
            title = (item.get("title") or "").strip()
            if not title:
                continue

            # 清理 HTML 标签
            title = _strip_html(title)

            # 获取链接
            link = item.get("link", "")
            if not link:
                links = item.get("links", [])
                link = links[0].get("href", "") if links else ""

            # 获取摘要
            summary = _strip_html(
                item.get("summary") or
                item.get("description") or
                item.get("content", [{}])[0].get("value", "") if item.get("content") else ""
            )
            # 截断摘要
            summary = summary[:200] if summary else ""

            # 获取来源名
            source = ""
            if hasattr(item, "source"):
                source = item.source.get("title", "") if item.source else ""
            if not source:
                source = feed.feed.get("title", "")

            entries.append({
                "title": title,
                "url": link,
                "source": source.strip(),
                "summary": summary,
            })

        return entries

    except requests.RequestException as e:
        print(f"      [WARN] 网络请求失败: {e}")
        return []
    except Exception as e:
        print(f"      [WARN] 解析失败: {e}")
        return []


def _strip_html(text: str) -> str:
    """去除 HTML 标签和多余空白"""
    import re
    clean = re.sub(r"<[^>]+>", "", text)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def _deduplicate(entries: list[dict], seen: set) -> list[dict]:
    """去重：去除与 seen 中相似的内容和自身重复"""
    result = []
    hashes = set()
    for entry in entries:
        h = _title_hash(entry["title"])
        if h in hashes:
            continue
        # 检查与已收录内容的相似度
        is_dup = False
        for existing_title in seen:
            if _similar(entry["title"], existing_title):
                is_dup = True
                break
        if is_dup:
            continue
        hashes.add(h)
        seen.add(entry["title"])
        result.append(entry)
    return result


def _filter_keywords(entries: list[dict], keywords: list[str]) -> list[dict]:
    """按关键词筛选（用于就业/职场/健身等分类）"""
    if not keywords:
        return entries
    return [e for e in entries if any(kw in e["title"] for kw in keywords)]


# ── 分类获取函数 ──

def _fetch_category(category: str, use_keywords: bool = False, use_tianapi_fallback: bool = True) -> list[dict]:
    """
    通用分类获取：遍历该分类的所有 RSS 源，收集到足够数量后返回

    Args:
        category: 分类key（对应 RSS_SOURCES 中的key）
        use_keywords: 是否对结果做关键词过滤
        use_tianapi_fallback: RSS失败时是否用天行数据兜底

    Returns:
        [{"title": str, "url": str, "source": str}, ...]
    """
    sources = RSS_SOURCES.get(category, [])
    keywords = CATEGORY_KEYWORDS.get(category, []) if use_keywords else []

    all_entries = []
    seen_titles = set()

    for src in sources:
        if len(all_entries) >= MAX_NEWS_PER_CATEGORY:
            break

        print(f"      📡 {src['name']} ({src['url'][:60]}...)")
        entries = _fetch_rss(src["url"])

        if entries:
            # 关键词过滤
            if keywords and category in ("career", "workplace", "fitness"):
                filtered = _filter_keywords(entries, keywords)
                print(f"         → 获取 {len(entries)} 条，关键词匹配 {len(filtered)} 条")
                entries = filtered

            new_entries = _deduplicate(entries, seen_titles)
            all_entries.extend(new_entries)
            print(f"         → 去重后新增 {len(new_entries)} 条")
        else:
            print(f"         → 无数据，切换下一个源")

    # 如果RSS源全部失败，尝试天行数据兜底
    if not all_entries and use_tianapi_fallback and TIANAPI_KEY:
        print(f"      🔄 RSS全部失败，尝试天行数据兜底...")
        all_entries = _tianapi_fallback(category)

    # 仍然没有数据，使用静态备用
    if not all_entries:
        fallback = FALLBACK_NEWS.get(category, [])
        if fallback:
            all_entries = fallback
            print(f"      ⚠️ 使用静态备用内容")

    return all_entries[:MAX_NEWS_PER_CATEGORY]


def _tianapi_fallback(category: str) -> list[dict]:
    """天行数据兜底 - 仅在RSS完全失败时调用"""
    # 分类到天行数据端点的映射
    endpoint_map = {
        "domestic": "/guonei/index",
        "world": "/world/index",
        "finance": "/caijing/index",
        "food": "/meishi/index",
        "travel": "/travel/index",
        "fitness": "/health/index",
        "career": "/weibohot/index",
        "workplace": "/weibohot/index",
    }
    endpoint = endpoint_map.get(category)
    if not endpoint:
        return []

    try:
        url = f"https://apis.tianapi.com{endpoint}"
        resp = requests.get(url, params={"key": TIANAPI_KEY, "num": MAX_NEWS_PER_CATEGORY},
                          headers=HEADERS, timeout=REQUEST_TIMEOUT)
        data = resp.json()
        if data.get("code") != 200:
            return []

        result_data = data.get("result", {})
        news_list = result_data.get("newslist") or result_data.get("list") or []
        return [
            {
                "title": (item.get("title") or item.get("hotword") or "").strip(),
                "url": (item.get("url") or item.get("murl") or "").strip(),
                "source": (item.get("source") or "天行数据").strip(),
            }
            for item in news_list[:MAX_NEWS_PER_CATEGORY]
            if (item.get("title") or item.get("hotword"))
        ]
    except Exception as e:
        print(f"      天行数据兜底也失败: {e}")
        return []


# ── 各分类入口 ──

def fetch_domestic_news() -> list[dict]:
    """🏛️ 国内时事政治 - RSS多源聚合"""
    return _fetch_category("domestic")


def fetch_world_news() -> list[dict]:
    """🌍 国际时事政治 - RSS + BBC中文等"""
    return _fetch_category("world")


def fetch_finance_news() -> list[dict]:
    """💰 经济动态 - 财联社/36氪/第一财经"""
    return _fetch_category("finance")


def fetch_career_news() -> list[dict]:
    """💼 就业资讯 - RSS获取 + 关键词过滤"""
    return _fetch_category("career", use_keywords=True)


def fetch_workplace_news() -> list[dict]:
    """🏢 职场动态 - RSS获取 + 关键词过滤"""
    return _fetch_category("workplace", use_keywords=True)


def fetch_food_news() -> list[dict]:
    """🍜 美食推荐 - 下厨房/美食天下"""
    return _fetch_category("food")


def fetch_travel_news() -> list[dict]:
    """✈️ 旅游资讯 - 马蜂窝/穷游网"""
    return _fetch_category("travel")


def fetch_fitness_news() -> list[dict]:
    """💪 健身健康 - 知乎健身/丁香医生 + 关键词过滤"""
    return _fetch_category("fitness", use_keywords=True)


# ── 统一入口 ──

def fetch_all_news() -> dict:
    """
    获取所有分类新闻
    返回: {category_key: [{"title", "url", "source"}, ...], ...}
    """
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 📡 开始 RSS 新闻采集...")
    print(f"   数据源: RSSHub ({len(RSS_SOURCES)} 个分类, 共 {sum(len(v) for v in RSS_SOURCES.values())} 个RSS源)")
    print()

    categories = {
        "domestic":   ("🏛️ 国内时事政治", fetch_domestic_news),
        "world":      ("🌍 国际时事政治", fetch_world_news),
        "finance":    ("💰 经济动态",     fetch_finance_news),
        "career":     ("💼 就业资讯",     fetch_career_news),
        "workplace":  ("🏢 职场动态",     fetch_workplace_news),
        "food":       ("🍜 美食推荐",     fetch_food_news),
        "travel":     ("✈️ 旅游资讯",     fetch_travel_news),
        "fitness":    ("💪 健身健康",     fetch_fitness_news),
    }

    result = {}
    total = 0
    for key, (label, fetcher) in categories.items():
        try:
            print(f"  {label}")
            news = fetcher()
            result[key] = news
            total += len(news)
            print(f"    ✅ 共 {len(news)} 条\n")
        except Exception as e:
            print(f"    ❌ 异常: {e}\n")
            result[key] = FALLBACK_NEWS.get(key, [])

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 采集完成，共 {total} 条新闻")
    return result
