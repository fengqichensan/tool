"""Telegram 通知模块"""

import logging
import os
from typing import Optional

import requests

log = logging.getLogger("boc_monitor")

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


class TelegramNotifier:
    """Telegram Bot 通知发送器"""

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def is_configured(self) -> bool:
        """检查 Telegram 配置是否完整"""
        return bool(self.bot_token and self.chat_id)

    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """发送消息到 Telegram。

        Args:
            text: 消息内容
            parse_mode: 解析模式 (Markdown, HTML, 或 None)

        Returns:
            发送成功返回 True，失败返回 False
        """
        if not self.is_configured():
            log.warning("Telegram 未配置，跳过发送通知")
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
                log.info("Telegram 消息发送成功")
                return True
            else:
                log.error(f"Telegram 消息发送失败: {result.get('description')}")
                return False
        except requests.RequestException as e:
            log.error(f"Telegram API 请求失败: {e}")
            return False

    def send_announcement(self, title: str, pdf_url: str, date: str) -> bool:
        """发送公告通知到 Telegram。

        Args:
            title: 公告标题
            pdf_url: PDF 文件链接
            date: 公告日期

        Returns:
            发送成功返回 True，失败返回 False
        """
        if not pdf_url:
            text = f"*{self._escape_markdown(title)}*\n日期: {date}"
        else:
            text = (
                f"*{self._escape_markdown(title)}*\n"
                f"日期: {date}\n\n"
                f"[查看PDF]({pdf_url})"
            )
        return self.send_message(text)

    def send_start(self) -> bool:
        """发送任务开始通知。

        Returns:
            发送成功返回 True，失败返回 False
        """
        text = "BOC 公告监控任务开始执行"
        return self.send_message(text)

    def send_complete(self, new_count: int) -> bool:
        """发送任务完成通知。

        Args:
            new_count: 新公告数量

        Returns:
            发送成功返回 True，失败返回 False
        """
        text = f"BOC 公告监控任务执行完成\n发现 {new_count} 条新公告"
        return self.send_message(text)

    def send_error(self, error_msg: str) -> bool:
        """发送错误通知。

        Args:
            error_msg: 错误信息

        Returns:
            发送成功返回 True，失败返回 False
        """
        text = f"BOC 公告监控任务执行出错\n错误: {self._escape_markdown(error_msg)}"
        return self.send_message(text)

    def _escape_markdown(self, text: str) -> str:
        """转义 Markdown 特殊字符。

        Args:
            text: 原始文本

        Returns:
            转义后的文本
        """
        special_chars = ["_", "*", "[", "]", "(", ")", "~", "`", ">", "#", "+", "-", "=", "|", "{", "}", ".", "!"]
        for char in special_chars:
            text = text.replace(char, f"\\{char}")
        return text