"""
飞书消息发送模块
通过 Webhook 发送交互式卡片消息到飞书群聊
"""
import json
import requests
from config import FEISHU_WEBHOOK_URL


def send_to_feishu(card: dict) -> bool:
    """
    发送卡片消息到飞书群聊

    Args:
        card: 飞书交互式卡片消息的 card 部分

    Returns:
        bool: 发送是否成功
    """
    if not FEISHU_WEBHOOK_URL:
        print("[ERROR] 未配置 FEISHU_WEBHOOK_URL 环境变量，无法发送")
        return False

    # 构建完整消息体
    payload = {
        "msg_type": "interactive",
        "card": card
    }

    headers = {"Content-Type": "application/json"}

    try:
        print(f"[INFO] 正在发送消息到飞书...")
        resp = requests.post(
            FEISHU_WEBHOOK_URL,
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            timeout=30
        )
        resp.raise_for_status()

        result = resp.json()
        # 飞书返回格式: {"StatusCode": 0, "StatusMessage": "success"}
        status_code = result.get("StatusCode", result.get("code", -1))
        status_msg = result.get("StatusMessage", result.get("msg", "unknown"))

        if status_code == 0:
            print(f"[SUCCESS] 飞书消息发送成功! Status: {status_msg}")
            return True
        else:
            print(f"[ERROR] 飞书返回错误: code={status_code}, msg={status_msg}")
            print(f"[ERROR] 完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return False

    except requests.RequestException as e:
        print(f"[ERROR] 网络请求失败: {e}")
        return False
    except (ValueError, KeyError, TypeError) as e:
        print(f"[ERROR] 响应解析失败: {e}")
        return False
