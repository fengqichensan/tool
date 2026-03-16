FROM python:3.11-slim-bookworm

LABEL maintainer="Monitor"
LABEL description="Multi-monitor system with Telegram notifications"

ENV TZ=Asia/Shanghai
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    cron \
    && rm -rf /var/lib/apt/lists/* \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY monitors/ ./monitors/
COPY admin.py .
COPY config.py .
COPY logger.py .

RUN mkdir -p /app/data/logs

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

VOLUME ["/app/data"]

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]