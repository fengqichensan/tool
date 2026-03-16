"""Shared Telegram notification module."""

import logging
import os
from typing import Optional

import requests

log = logging.getLogger("monitor")

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


class TelegramNotifier:
    """Telegram Bot notification sender."""

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def is_configured(self) -> bool:
        """Check if Telegram is properly configured."""
        return bool(self.bot_token and self.chat_id)

    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Send a message to Telegram.

        Args:
            text: Message content
            parse_mode: Parse mode (Markdown, HTML, or None)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.is_configured():
            log.warning("Telegram not configured, skipping notification")
            return False

        url = TELEGRAM_API_URL.format(token=self.bot_token)
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
        }

        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            if result.get("ok"):
                log.info("Telegram message sent successfully")
                return True
            else:
                log.error(f"Telegram message failed: {result.get('description')}")
                return False
        except requests.RequestException as e:
            log.error(f"Telegram API request failed: {e}")
            return False

    def _escape_markdown(self, text: str) -> str:
        """Escape Markdown special characters.

        Args:
            text: Original text

        Returns:
            Escaped text
        """
        special_chars = ["_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"]
        for char in special_chars:
            text = text.replace(char, f"\\{char}")
        return text