"""
新闻获取模块 - RSS 多源聚合引擎 v3.0
- 直连 RSS（最可靠）
- Google News RSS（全球可访问的中文新闻聚合）
- RSSHub 多镜像轮换（一个不通自动换下一个）
- 天行数据兜底（可选）
"""
import hashlib
import re
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher

import feedparser
import requests

from config import (
    RSS_SOURCES,
    RSSHUB_MIRRORS,
    MAX_NEWS_PER_CATEGORY,
    CATEGORY_KEYWORDS,
    FALLBACK_NEWS,
    HEADERS,
    REQUEST_TIMEOUT,
    TIANAPI_KEY,
)


# ═══════════════════════════════════════════════════════════════
#  工具函数
# ═══════════════════════════════════════════════════════════════

def _strip_html(text: str) -> str:
    """去除 HTML 标签和多余空白"""
    clean = re.sub(r"<[^>]+>", "", text)
    clean = re.sub(r"&[a-z]+;", " ", clean)
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def _similar(a: str, b: str, threshold: float = 0.72) -> bool:
    """判断两个标题是否相似（去重用）"""
    if not a or not b:
        return False
    # 快速路径：短标题完全包含
    short, long = (a, b) if len(a) <= len(b) else (b, a)
    if len(short) >= 8 and short[:8] in long:
        return True
    return SequenceMatcher(None, a[:80], b[:80]).ratio() >= threshold


def _title_hash(title: str) -> str:
    """标题短哈希，快速去重"""
    return hashlib.md5(title[:100].encode()).hexdigest()[:12]


def _try_fetch_url(url: str, add_cache_buster: bool = False) -> list[dict]:
    """
    请求单个 URL 并解析 RSS/Atom
    自动过滤超过48小时的旧闻，按日期降序排列
    返回: [{"title", "url", "source", "summary", "published"}, ...]
    """
    try:
        # Google News 自动加时间戳防缓存（避免返回旧闻）
        fetch_url = url
        if "news.google.com" in url:
            sep = "&" if "?" in url else "?"
            fetch_url = f"{url}{sep}_nocache={int(datetime.now().timestamp())}"

        resp = requests.get(
            fetch_url, headers=HEADERS, timeout=REQUEST_TIMEOUT,
            allow_redirects=True
        )
        resp.raise_for_status()

        feed = feedparser.parse(resp.content)

        # bozo=1 表示非标准 feed，但有 entries 就还能用
        if feed.bozo and not feed.entries:
            return []

        entries = []
        for item in feed.entries:
            title = _strip_html(item.get("title") or "")
            if not title or len(title) < 4:
                continue

            # URL
            link = item.get("link", "")
            if not link:
                links = item.get("links", [])
                link = links[0].get("href", "") if links else ""

            # 摘要
            summary = _strip_html(
                item.get("summary") or
                item.get("description") or
                (item.get("content", [{}])[0].get("value", "") if item.get("content") else "")
            )[:200]

            # 来源
            source = ""
            if hasattr(item, "source") and item.source:
                source = item.source.get("title", "")
            if not source:
                source = feed.feed.get("title", "")

            # 发布日期（用于过滤旧闻）
            published = ""
            pub_dt = None
            pub_parsed = item.get("published_parsed") or item.get("updated_parsed")
            if pub_parsed:
                try:
                    pub_dt = datetime(*pub_parsed[:6], tzinfo=timezone.utc)
                    published = pub_dt.strftime("%m-%d %H:%M")
                except (ValueError, TypeError, OverflowError):
                    pass

            entries.append({
                "title": title,
                "url": link,
                "source": _strip_html(source),
                "summary": summary,
                "published": published,
                "pub_dt": pub_dt,
            })

        # ── 日期过滤：只保留最近48小时的新闻 ──
        cutoff = datetime.now(timezone.utc) - timedelta(hours=48)
        fresh = []
        for e in entries:
            if e["pub_dt"] is None:
                # 没有日期的先保留（RSSHub等源可能没日期）
                fresh.append(e)
            elif e["pub_dt"] >= cutoff:
                fresh.append(e)
            # 超过48小时的丢弃

        # 按日期降序（有日期的在前，没日期的在后）
        fresh.sort(
            key=lambda e: e.get("pub_dt") or datetime(2000, 1, 1, tzinfo=timezone.utc),
            reverse=True
        )

        return fresh

    except requests.RequestException:
        return []
    except Exception:
        return []


# ═══════════════════════════════════════════════════════════════
#  RSSHub 多镜像轮换
# ═══════════════════════════════════════════════════════════════

def _fetch_via_rsshub(path: str) -> list[dict]:
    """
    通过 RSSHub 获取内容，自动轮换多个镜像
    path 格式: "/thepaper/featured"（不含域名）
    """
    for i, mirror in enumerate(RSSHUB_MIRRORS):
        url = f"{mirror}{path}"
        print(f"         🔗 尝试 RSSHub 镜像{i+1}: {mirror[:35]}...")
        entries = _try_fetch_url(url)
        if entries:
            print(f"         ✅ 成功 ({len(entries)} 条)")
            return entries
        print(f"         ❌ 无响应")
    return []


# ═══════════════════════════════════════════════════════════════
#  去重 & 过滤
# ═══════════════════════════════════════════════════════════════

def _deduplicate(entries: list[dict], seen_titles: set) -> list[dict]:
    """去重：标题相似度 + 哈希双重检测"""
    result = []
    local_hashes = set()
    for entry in entries:
        h = _title_hash(entry["title"])
        if h in local_hashes:
            continue
        dup = False
        for existing in seen_titles:
            if _similar(entry["title"], existing):
                dup = True
                break
        if dup:
            continue
        local_hashes.add(h)
        seen_titles.add(entry["title"])
        result.append(entry)
    return result


def _filter_keywords(entries: list[dict], keywords: list[str]) -> list[dict]:
    """按关键词筛选"""
    if not keywords:
        return entries
    return [e for e in entries if any(kw in e["title"] for kw in keywords)]


# ═══════════════════════════════════════════════════════════════
#  单个分类获取
# ═══════════════════════════════════════════════════════════════

def _fetch_category(category: str, use_keywords: bool = False) -> list[dict]:
    """
    获取一个分类的新闻：
    1. 遍历所有配置的源（直连 → Google News → RSSHub镜像）
    2. 去重
    3. 关键词过滤（就业/职场/健身）
    4. 不够的话天行数据兜底
    5. 还不够用静态备用
    """
    sources = RSS_SOURCES.get(category, [])
    keywords = CATEGORY_KEYWORDS.get(category, []) if use_keywords else []

    all_entries = []
    seen_titles = set()

    for src in sources:
        if len(all_entries) >= MAX_NEWS_PER_CATEGORY:
            break

        name = src["name"]
        via = src.get("via", "rsshub")
        url_tpl = src["url"]

        print(f"      📡 [{via.upper()}] {name}")

        if via == "direct":
            # 直连 RSS（BBC、Google News、36kr 等）
            entries = _try_fetch_url(url_tpl)

        elif via == "rsshub":
            # RSSHub 路径，走多镜像轮换
            path = url_tpl.replace("{rsshub}", "")
            entries = _fetch_via_rsshub(path)

        else:
            entries = _try_fetch_url(url_tpl)

        if entries:
            # 关键词过滤
            if keywords and category in ("career", "workplace", "fitness"):
                before = len(entries)
                entries = _filter_keywords(entries, keywords)
                print(f"         → 获取 {before} 条，关键词匹配 {len(entries)} 条")

            new_entries = _deduplicate(entries, seen_titles)
            all_entries.extend(new_entries)
            print(f"         → 去重后新增 {len(new_entries)} 条 (累计 {len(all_entries)})")
        else:
            print(f"         → 无数据")

    # ── 兜底策略 ──
    if not all_entries and TIANAPI_KEY:
        print(f"      🔄 全部RSS源失败，尝试天行数据兜底...")
        all_entries = _tianapi_fallback(category)

    if not all_entries:
        fallback = FALLBACK_NEWS.get(category, [])
        if fallback:
            all_entries = fallback
            print(f"      ⚠️ 使用静态备用内容")

    return all_entries[:MAX_NEWS_PER_CATEGORY]


def _tianapi_fallback(category: str) -> list[dict]:
    """天行数据兜底"""
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
        resp = requests.get(
            url,
            params={"key": TIANAPI_KEY, "num": MAX_NEWS_PER_CATEGORY},
            headers=HEADERS, timeout=REQUEST_TIMEOUT
        )
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
        print(f"      天行数据兜底失败: {e}")
        return []


# ═══════════════════════════════════════════════════════════════
#  各分类入口
# ═══════════════════════════════════════════════════════════════

def fetch_domestic_news() -> list[dict]:
    """🏛️ 国内时事政治"""
    return _fetch_category("domestic")


def fetch_world_news() -> list[dict]:
    """🌍 国际时事政治"""
    return _fetch_category("world")


def fetch_finance_news() -> list[dict]:
    """💰 经济动态"""
    return _fetch_category("finance")


def fetch_career_news() -> list[dict]:
    """💼 就业资讯"""
    return _fetch_category("career", use_keywords=True)


def fetch_workplace_news() -> list[dict]:
    """🏢 职场动态"""
    return _fetch_category("workplace", use_keywords=True)


def fetch_food_news() -> list[dict]:
    """🍜 美食推荐"""
    return _fetch_category("food")


def fetch_travel_news() -> list[dict]:
    """✈️ 旅游资讯"""
    return _fetch_category("travel")


def fetch_fitness_news() -> list[dict]:
    """💪 健身健康"""
    return _fetch_category("fitness", use_keywords=False)


# ═══════════════════════════════════════════════════════════════
#  统一入口
# ═══════════════════════════════════════════════════════════════

def fetch_all_news() -> dict:
    """获取全部8个分类的新闻"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    total_sources = sum(len(v) for v in RSS_SOURCES.values())
    print(f"[{now}] 📡 开始 RSS 新闻采集")
    print(f"   RSSHub 镜像: {len(RSSHUB_MIRRORS)} 个")
    print(f"   分类: {len(RSS_SOURCES)} 个 | 总RSS源: {total_sources} 个")
    print(f"   天行数据兜底: {'✅ 已配置' if TIANAPI_KEY else '❌ 未配置'}")
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

    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] ✅ 采集完成，共 {total} 条新闻")
    return result
