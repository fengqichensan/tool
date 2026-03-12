"""配置模块"""

import os

# 获取当前脚本所在目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 公告页面URL
ANNOUNCEMENT_URL = "https://www.boc.cn/investor/ir5/"

# 请求配置
REQUEST_TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# 数据存储路径（使用绝对路径）
DATA_DIR = os.path.join(SCRIPT_DIR, "data")
SENT_RECORDS_FILE = "sent_records.json"