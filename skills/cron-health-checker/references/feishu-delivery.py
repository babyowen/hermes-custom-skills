#!/usr/bin/env python3
"""
Feishu delivery script for cron health check reports.

Usage:
  python3 feishu-delivery.py --report <report_file> [--chat <chat_id>]

Reads FEISHU_APP_ID and FEISHU_APP_SECRET from ~/.hermes/.env.
Sends the report content as a text message to the specified Feishu chat.

Default chat: oc_4b7bc3b652e8b27c8a3c683fa4b53aa0
"""
import os
import re
import json
import sys
import argparse
import requests


def load_env(path="~/.hermes/.env"):
    """Load specific vars from .env file."""
    env_path = os.path.expanduser(path)
    if not os.path.exists(env_path):
        print(f"❌ .env not found at {env_path}")
        sys.exit(1)
    
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Strip inline comments (e.g. FOO=bar # comment)
            if "=" in line:
                key, _, val = line.partition("=")
                key = key.strip()
                # Remove trailing inline comments
                val = re.sub(r"\s+#.*$", "", val).strip()
                os.environ[key] = val


def get_tenant_token(app_id, app_secret):
    """Get Feishu tenant_access_token."""
    resp = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": app_id, "app_secret": app_secret},
        timeout=10,
    )
    if resp.status_code != 200:
        print(f"❌ Failed to get token: {resp.status_code} {resp.text}")
        sys.exit(1)
    data = resp.json()
    token = data.get("tenant_access_token")
    if not token:
        print(f"❌ No token in response: {json.dumps(data, ensure_ascii=False)}")
        sys.exit(1)
    return token


def send_message(token, chat_id, text):
    """Send a text message to a Feishu chat."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "receive_id": chat_id,
        "msg_type": "text",
        "content": json.dumps({"text": text}, ensure_ascii=False),
    }
    resp = requests.post(
        "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
        headers=headers,
        json=payload,
        timeout=15,
    )
    result = resp.json()
    if result.get("code") == 0:
        msg_id = result.get("data", {}).get("message_id", "unknown")
        print(f"✅ Report delivered to Feishu (message_id: {msg_id})")
        return True
    else:
        print(f"❌ Failed to deliver: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return False


def read_report(filepath):
    """Read the report file."""
    with open(os.path.expanduser(filepath), "r", encoding="utf-8") as f:
        return f.read()


def main():
    parser = argparse.ArgumentParser(description="Deliver health check report to Feishu")
    parser.add_argument("--report", required=True, help="Path to report file")
    parser.add_argument("--chat", default="oc_4b7bc3b652e8b27c8a3c683fa4b53aa0",
                        help="Feishu chat ID to deliver to")
    args = parser.parse_args()

    # Load credentials
    load_env()
    app_id = os.environ.get("FEISHU_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET")
    
    if not app_id or not app_secret:
        print("❌ FEISHU_APP_ID or FEISHU_APP_SECRET not set in .env")
        sys.exit(1)

    # Read report
    report = read_report(args.report)

    # Deliver
    token = get_tenant_token(app_id, app_secret)
    send_message(token, args.chat, report)


if __name__ == "__main__":
    main()
