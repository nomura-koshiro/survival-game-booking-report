"""LINE Messaging API でメッセージを送信する。"""

from __future__ import annotations

import json
import os
import urllib.request


LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"


def send_line_message(text: str) -> None:
    """LINE Messaging API でテキストメッセージを push 送信する。

    必要な環境変数:
        LINE_CHANNEL_ACCESS_TOKEN: チャネルアクセストークン (長期)
        LINE_USER_ID: 送信先のユーザーID (またはグループID)

    Raises:
        KeyError: 環境変数が未設定の場合。
        RuntimeError: LINE API がエラーを返した場合。
    """
    token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
    user_id = os.environ["LINE_USER_ID"]

    # LINE テキストメッセージの上限は 5000 文字
    if len(text) > 5000:
        text = text[:4990] + "\n...(省略)"

    body = json.dumps(
        {
            "to": user_id,
            "messages": [{"type": "text", "text": text}],
        }
    ).encode()

    req = urllib.request.Request(
        LINE_PUSH_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
    )

    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status != 200:
            error_body = resp.read().decode()
            raise RuntimeError(f"LINE API error ({resp.status}): {error_body}")
