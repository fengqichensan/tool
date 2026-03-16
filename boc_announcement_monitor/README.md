# 中国银行公告监控工具

自动抓取中国银行 A 股公告页面，下载 PDF 文件并提取文本内容。

## 功能

- 爬取中国银行 A 股公告列表
- 只获取当日公告
- 自动下载公告 PDF 并提取文本
- 记录已处理公告，避免重复处理
- Docker 化部署，支持 Web 管理界面
- 定时任务管理（启动/停止、修改执行时间）

## 安装

### 方式一：直接运行

```bash
cd boc_announcement_monitor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 方式二：Docker

```bash
# 复制环境变量配置
cp boc_announcement_monitor/.env.example boc_announcement_monitor/.env
# 编辑 .env 填入 Telegram 配置

# 构建并启动
docker-compose up -d
```

Docker 容器会自动在工作日（周一至周五）的中国时间 9:30、11:30、14:30、16:30、18:30 执行监控任务。

## 使用

### 直接运行

```bash
python main.py
```

### Docker 运行

```bash
# 启动容器
docker-compose up -d

# 查看日志
docker-compose logs -f

# 手动执行一次监控
docker exec boc-announcement-monitor python /app/main.py
```

### Web 管理界面

Docker 容器启动后，访问 `http://localhost:8080` 进入管理界面，可以：

- 查看任务运行状态
- 启动/停止定时任务
- 添加/删除执行时间
- 选择执行日期（周一至周日）
- 立即执行一次监控
- 查看最近日志

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
├── admin.py       # Web 管理界面
├── scraper.py     # 网页爬取模块
├── pdf_reader.py  # PDF 下载和解析模块
├── storage.py     # 已发送记录存储模块
├── config.py      # 配置文件
├── requirements.txt
└── data/
    └── sent_records.json

docker/
├── cronjob        # Cron 定时任务配置
└── entrypoint.sh  # Docker 入口脚本

Dockerfile         # Docker 镜像构建文件
docker-compose.yaml # Docker Compose 配置
```