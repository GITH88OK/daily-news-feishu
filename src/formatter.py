"""
飞书卡片消息格式化模块
构建可视化、排版美观的交互式卡片消息
"""
import json
from datetime import datetime, timezone, timedelta


# ── 飞书卡片颜色常量 ──
COLORS = {
    "header": "blue",           # 卡片头部颜色
    "divider": "default",       # 分割线
}

# ── 分类元数据：emoji + 颜色 + 中文名 ──
CATEGORY_META = {
    "domestic":    ("🏛️", "国内时事", "blue"),
    "world":       ("🌍", "国际时事", "purple"),
    "finance":     ("💰", "经济动态", "orange"),
    "career":      ("💼", "就业资讯", "green"),
    "workplace":   ("🏢", "职场动态", "turquoise"),
    "food":        ("🍜", "美食推荐", "red"),
    "travel":      ("✈️", "旅游资讯", "yellow"),
    "fitness":     ("💪", "健身健康", "wathet"),
}


def _beijing_time() -> str:
    """获取当前北京时间字符串"""
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)
    weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday = weekdays[now.weekday()]
    return f"{now.strftime('%Y年%m月%d日')} {weekday}"


def _build_news_lines(news_list: list[dict], max_items: int = 5) -> str:
    """构建新闻列表的 markdown 文本，含日期标注"""
    if not news_list:
        return "> 今日暂无相关资讯，稍后更新 📌"

    lines = []
    for i, item in enumerate(news_list[:max_items], 1):
        title = item.get("title", "无标题").strip()
        url = item.get("url", "").strip()
        published = item.get("published", "").strip()

        # 截断过长的标题
        if len(title) > 48:
            title = title[:46] + "..."

        # 日期标记
        date_tag = f" `{published}`" if published else ""

        if url:
            lines.append(f"{i}. [{title}]({url}){date_tag}")
        else:
            lines.append(f"{i}. {title}{date_tag}")

    return "\n".join(lines)


def build_card(all_news: dict) -> dict:
    """
    构建飞书交互式卡片消息

    布局结构:
    ┌────────────────────────────────────┐
    │  📰 每日新闻汇总 | 日期 星期        │  ← header
    ├────────────────────────────────────┤
    │  🏛 国内时事 (5条)                  │
    │  1. [标题](链接)                    │
    │  ...                                │
    ├────────────────────────────────────┤
    │  🌍 国际时事 (5条)                  │
    ├────────────────────────────────────┤
    │  💰 经济动态 (5条)                  │
    ├────────────────────────────────────┤
    │  💼 就业 (左) | 🏢 职场 (右)       │  ← 双列
    ├────────────────────────────────────┤
    │  🍜 美食 | ✈️ 旅游 | 💪 健身       │  ← 三列
    ├────────────────────────────────────┤
    │  📌 数据来源 | 每日早9点自动推送    │  ← footer
    └────────────────────────────────────┘
    """
    date_str = _beijing_time()

    # ── 构建卡片元素列表 ──
    elements = []

    # ── 第一组：国内时事（全宽） ──
    elements.append(_section_block("🏛️ 国内时事政治", all_news.get("domestic", [])))
    elements.append({"tag": "hr"})

    # ── 第二组：国际时事（全宽） ──
    elements.append(_section_block("🌍 国际时事政治", all_news.get("world", [])))
    elements.append({"tag": "hr"})

    # ── 第三组：经济动态（全宽） ──
    elements.append(_section_block("💰 经济动态", all_news.get("finance", [])))
    elements.append({"tag": "hr"})

    # ── 第四组：就业 + 职场（双列并排） ──
    elements.append({
        "tag": "column_set",
        "flex_mode": "bisect",
        "background_style": "default",
        "columns": [
            _column_section("💼 就业资讯", all_news.get("career", []), "green"),
            _column_section("🏢 职场动态", all_news.get("workplace", []), "turquoise"),
        ]
    })
    elements.append({"tag": "hr"})

    # ── 第五组：美食 + 旅游 + 健身（三列并排） ──
    elements.append({
        "tag": "column_set",
        "flex_mode": "trisect",
        "background_style": "default",
        "columns": [
            _column_section("🍜 美食推荐", all_news.get("food", []), "red"),
            _column_section("✈️ 旅游资讯", all_news.get("travel", []), "yellow"),
            _column_section("💪 健身健康", all_news.get("fitness", []), "wathet"),
        ]
    })

    # ── 底部注释 ──
    elements.append({"tag": "hr"})
    elements.append({
        "tag": "note",
        "elements": [
            {
                "tag": "plain_text",
                "content": f"📌 数据来源：天行数据 API 及公开信息 | 仅供参考，请以原文为准 | ⏰ 每日早9:00 自动推送 | {date_str}"
            }
        ]
    })

    # ── 组装卡片 ──
    card = {
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {
                "tag": "plain_text",
                "content": f"📰 每日新闻汇总 · {date_str}"
            },
            "template": "blue"
        },
        "elements": elements
    }

    return card


def _section_block(title: str, news_list: list[dict]) -> dict:
    """构建一个全宽的新闻板块"""
    content = _build_news_lines(news_list)
    return {
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": f"**{title}**\n\n{content}"
        }
    }


def _column_section(title: str, news_list: list[dict], color: str) -> dict:
    """构建一个列内的新闻板块"""
    content = _build_news_lines(news_list, max_items=3)
    return {
        "tag": "column",
        "width": "weighted",
        "weight": 1,
        "vertical_align": "top",
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": f"**{title}**\n\n{content}"
                }
            }
        ]
    }


def card_to_json_str(card: dict) -> str:
    """将卡片转为 JSON 字符串"""
    return json.dumps(card, ensure_ascii=False)


def build_message_body(card: dict) -> dict:
    """
    构建发送给飞书 Webhook 的消息体
    飞书机器人 Webhook 支持的消息类型: text, post, image, share_chat, interactive
    """
    return {
        "msg_type": "interactive",
        "card": card
    }
