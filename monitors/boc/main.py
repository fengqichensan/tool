#!/usr/bin/env python3
"""BOC announcement monitor - main program."""

import json
import sys
from datetime import datetime
from typing import Dict, List

import logger
from monitors.boc import pdf_reader, scraper, storage
from monitors.telegram_notifier import TelegramNotifier

log = logger.setup_logger("boc_monitor")


def process_new_announcements() -> List[Dict]:
    """Process new announcements and return results."""
    notifier = TelegramNotifier()
    notifier.send_message("BOC 公告监控任务开始执行")

    try:
        return _do_process(notifier)
    except Exception as e:
        log.error(f"Task execution error: {e}")
        notifier.send_message(f"BOC 公告监控任务执行出错\n错误: {e}")
        return []


def _do_process(notifier: TelegramNotifier) -> List[Dict]:
    """Execute core announcement processing logic."""
    logger.cleanup_old_logs()

    sc = scraper.AnnouncementScraper()
    reader = pdf_reader.PDFReader()
    store = storage.SentRecordsStorage()

    log.info("Fetching announcement list...")
    announcements = sc.get_announcements()

    log.info(f"Found {len(announcements)} announcements")

    today = datetime.now().strftime("%Y-%m-%d")
    today_announcements = [ann for ann in announcements if ann["date"] == today]
    log.info(f"Today's announcements: {len(today_announcements)}")

    new_announcements = [
        ann for ann in today_announcements if not store.is_sent(ann["id"])
    ]

    log.info(f"New announcements: {len(new_announcements)}")

    results = []
    for ann in new_announcements:
        log.info(f"Processing: {ann['title']}")

        content = ""
        try:
            content = reader.download_and_extract(ann["pdf_url"])
            if not content:
                content = "[无法提取PDF内容]"
        except Exception as e:
            log.error(f"PDF processing failed: {e}")
            content = f"[PDF处理失败: {e}]"

        store.mark_sent(ann["id"], ann["title"], ann["date"])

        title = ann['title'].replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']', '\\]')
        notifier.send_message(f"*{title}*\n日期: {ann['date']}\n\n[查看PDF]({ann['pdf_url']})")

        results.append(
            {
                "id": ann["id"],
                "title": ann["title"],
                "date": ann["date"],
                "pdf_url": ann["pdf_url"],
                "content": content,
            }
        )

    notifier.send_message(f"BOC 公告监控任务执行完成\n发现 {len(results)} 条新公告")
    return results


def main():
    """Main entry point."""
    results = process_new_announcements()

    output = json.dumps(results, ensure_ascii=False, indent=2)
    print(output)

    return 0 if results else 0


if __name__ == "__main__":
    sys.exit(main())