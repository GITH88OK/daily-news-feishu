#!/usr/bin/env python3
"""
每日新闻汇总推送 - 主入口
通过 GitHub Actions 定时触发，自动获取新闻并推送到飞书群聊

本地运行: python src/main.py
GitHub Actions: 由 .github/workflows/daily-push.yml 在每日 UTC 1:00 触发
"""
import sys
import traceback
from datetime import datetime

from news_fetcher import fetch_all_news
from formatter import build_card
from feishu_sender import send_to_feishu


def main():
    print("=" * 60)
    print(f"📰 每日新闻汇总推送系统")
    print(f"⏰ 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (UTC)")
    print(f"🌏 北京时间: 约 {(datetime.now().strftime('%H'))} 点 (UTC+8)")
    print("=" * 60)

    # ── Step 1: 获取所有分类新闻 ──
    print("\n📡 [1/3] 获取新闻数据...")
    try:
        all_news = fetch_all_news()
    except Exception as e:
        print(f"[FATAL] 新闻获取阶段失败: {e}")
        traceback.print_exc()
        sys.exit(1)

    # 检查是否有任何新闻
    total_news = sum(len(v) for v in all_news.values())
    if total_news == 0:
        print("[WARN] 未获取到任何新闻，请检查 API Key 配置")
        # 仍然发送一条通知消息

    # ── Step 2: 构建飞书卡片 ──
    print("\n🎨 [2/3] 构建飞书卡片消息...")
    try:
        card = build_card(all_news)
    except Exception as e:
        print(f"[FATAL] 卡片构建失败: {e}")
        traceback.print_exc()
        sys.exit(1)

    # ── Step 3: 发送到飞书 ──
    print("\n📤 [3/3] 推送到飞书群聊...")
    try:
        success = send_to_feishu(card)
    except Exception as e:
        print(f"[FATAL] 发送阶段失败: {e}")
        traceback.print_exc()
        sys.exit(1)

    # ── 结果 ──
    print("\n" + "=" * 60)
    if success:
        print("✅ 推送成功! 共发送 {} 条新闻摘要".format(total_news))
    else:
        print("❌ 推送失败，请检查飞书 Webhook URL 配置")
    print("=" * 60)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
