#!/usr/bin/env python3
"""
Feishu delivery script for cron health check reports.

Usage:
  python3 feishu-delivery.py --report <report_file> [--chat <chat_id>]

Sends the report via lark-cli --markdown for native Feishu post rendering
(headings, code blocks, bold, lists all render beautifully).

Default chat: oc_4b7bc3b652e8b27c8a3c683fa4b53aa0
"""
import os
import sys
import subprocess
import argparse


def lark_send(chat_id: str, content: str) -> bool:
    """Send markdown content to a Feishu chat via lark-cli.

    Uses lark-cli --markdown which sends via Feishu native post format
    for beautiful rendering of headings, code blocks, bold, lists.
    """
    try:
        proc = subprocess.run(
            ["lark-cli", "--as", "bot", "im", "+messages-send",
             "--chat-id", chat_id, "--markdown", "-"],
            input=content,
            capture_output=True,
            text=True,
            timeout=30,
        )
        result = proc.stdout.strip()
        err = proc.stderr.strip()

        if proc.returncode == 0:
            print(f"✅ Report delivered to Feishu (chat: {chat_id})")
            return True
        else:
            print(f"❌ lark-cli failed (exit={proc.returncode}): {err[:500]}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ lark-cli timed out after 30s")
        return False
    except FileNotFoundError:
        print("❌ lark-cli not found. Install: npm install -g @larksuite/cli")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def read_report(filepath: str) -> str:
    """Read the report file."""
    with open(os.path.expanduser(filepath), "r", encoding="utf-8") as f:
        return f.read()


def main():
    parser = argparse.ArgumentParser(description="Deliver health check report to Feishu via lark-cli")
    parser.add_argument("--report", required=True, help="Path to report file")
    parser.add_argument("--chat", default="oc_4b7bc3b652e8b27c8a3c683fa4b53aa0",
                        help="Feishu chat ID to deliver to")
    args = parser.parse_args()

    # Read report
    report = read_report(args.report)

    # Deliver via lark-cli
    lark_send(args.chat, report)


if __name__ == "__main__":
    main()
