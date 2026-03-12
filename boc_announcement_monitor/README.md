# 中国银行公告监控工具

自动抓取中国银行 A 股公告页面，下载 PDF 文件并提取文本内容。

## 功能

- 爬取中国银行 A 股公告列表
- 只获取当日公告
- 自动下载公告 PDF 并提取文本
- 记录已处理公告，避免重复处理

## 安装

```bash
cd boc_announcement_monitor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 使用

```bash
python main.py
```

## 运行结果

程序输出 JSON 数组到标准输出，处理日志输出到标准错误。

### JSON 输出格式

程序输出 JSON 数组到标准输出，处理日志输出到标准错误。

#### 无新公告时

当所有公告都已处理过时，输出空数组：

```json
[]
```

#### 有新公告时

```json
[
  {
    "id": "2026-03-04_25651688",
    "title": "中国银行股份有限公司董事会决议公告",
    "date": "2026-03-04",
    "pdf_url": "https://pic.bankofchina.com/bocappd/report/202603/P020260304311742985016.pdf",
    "content": "证券代码：601988 证券简称：中国银行..."
  }
]
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | 公告唯一标识，格式为 `{日期}_{页面ID}` |
| `title` | string | 公告标题 |
| `date` | string | 公告日期，格式 `YYYY-MM-DD` |
| `pdf_url` | string | PDF 下载链接，可能为空字符串 |
| `content` | string | PDF 提取的文本内容，提取失败时为 `[无法提取PDF内容]` 或 `[PDF处理失败: {错误信息}]` |

### 示例输出

```json
[
  {
    "id": "2026-03-04_25651688",
    "title": "中国银行股份有限公司董事会决议公告",
    "date": "2026-03-04",
    "pdf_url": "https://pic.bankofchina.com/bocappd/report/202603/P020260304311742985016.pdf",
    "content": "证券代码：601988 证券简称：中国银行 公告编号：临2026-003\n中国银行股份有限公司董事会决议公告\n..."
  },
  {
    "id": "2026-02-13_25650253",
    "title": "中国银行股份有限公司董事会决议公告",
    "date": "2026-02-13",
    "pdf_url": "https://pic.bankofchina.com/bocappd/report/202602/P020260213600429299589.pdf",
    "content": "证券代码：601988 证券简称：中国银行 公告编号：临2026-002\n..."
  }
]
```

## 配置

编辑 `config.py` 修改配置：

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `ANNOUNCEMENT_URL` | `https://www.boc.cn/investor/ir5/` | 公告页面 URL |
| `REQUEST_TIMEOUT` | `30` | 请求超时时间（秒） |
| `DATA_DIR` | `{脚本目录}/data` | 数据存储目录（绝对路径） |

## 数据存储

- `data/sent_records.json`：已处理公告记录，用于去重

### 记录格式

```json
{
  "2026-03-04_25651688": {
    "title": "中国银行股份有限公司董事会决议公告",
    "date": "2026-03-04",
    "sent_at": "2026-03-12T23:28:20.125959"
  }
}
```

## 文件结构

```
boc_announcement_monitor/
├── main.py        # 主程序入口
├── scraper.py     # 网页爬取模块
├── pdf_reader.py  # PDF 下载和解析模块
├── storage.py     # 已发送记录存储模块
├── config.py      # 配置文件
├── requirements.txt
└── data/
    └── sent_records.json
```