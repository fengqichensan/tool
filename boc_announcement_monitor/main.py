#!/usr/bin/env python3
"""中国银行公告监控工具 - 主程序"""

import json
import sys
from datetime import datetime
from typing import List, Dict

import logger
import pdf_reader
import scraper
import storage
import telegram_notifier

log = logger.setup_logger()


def process_new_announcements() -> List[Dict]:
    """处理新公告并返回结果。"""
    notifier = telegram_notifier.TelegramNotifier()
    notifier.send_start()

    try:
        return _do_process(notifier)
    except Exception as e:
        log.error(f"任务执行出错: {e}")
        notifier.send_error(str(e))
        return []


def _do_process(notifier: telegram_notifier.TelegramNotifier) -> List[Dict]:
    """执行公告处理的核心逻辑。"""
    # 清理旧日志
    logger.cleanup_old_logs()

    # 初始化各模块
    sc = scraper.AnnouncementScraper()
    reader = pdf_reader.PDFReader()
    store = storage.SentRecordsStorage()

    # 获取公告列表
    log.info("正在获取公告列表...")
    announcements = sc.get_announcements()

    log.info(f"共找到 {len(announcements)} 条公告")

    # 只保留今日公告
    today = datetime.now().strftime("%Y-%m-%d")
    today_announcements = [ann for ann in announcements if ann["date"] == today]
    log.info(f"其中 {len(today_announcements)} 条为今日公告")

    # 过滤已发送的新公告
    new_announcements = [
        ann for ann in today_announcements if not store.is_sent(ann["id"])
    ]

    log.info(f"其中 {len(new_announcements)} 条为新公告")

    # 处理每个新公告
    results = []
    for ann in new_announcements:
        log.info(f"正在处理: {ann['title']}")

        # 下载PDF并提取内容
        content = ""
        try:
            content = reader.download_and_extract(ann["pdf_url"])
            if not content:
                content = "[无法提取PDF内容]"
        except Exception as e:
            log.error(f"处理PDF失败: {e}")
            content = f"[PDF处理失败: {e}]"

        # 标记为已发送
        store.mark_sent(ann["id"], ann["title"], ann["date"])

        # 发送 Telegram 通知
        notifier.send_announcement(ann["title"], ann["pdf_url"], ann["date"])

        # 收集结果
        results.append(
            {
                "id": ann["id"],
                "title": ann["title"],
                "date": ann["date"],
                "pdf_url": ann["pdf_url"],
                "content": content,
            }
        )

    notifier.send_complete(len(results))
    return results


def main():
    """主入口"""
    results = process_new_announcements()

    # 输出JSON结果
    output = json.dumps(results, ensure_ascii=False, indent=2)
    print(output)

    return 0 if results else 0


if __name__ == "__main__":
    sys.exit(main())