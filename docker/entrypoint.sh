#!/bin/bash
set -e

echo "Starting BOC Announcement Monitor..."
echo "Timezone: $TZ"
echo "Current time: $(date)"

# Initialize config if not exists
if [ ! -f /app/data/schedule_config.json ]; then
    echo '{"enabled": true, "times": ["9:30", "11:30", "14:30", "16:30", "18:30"], "weekdays": [1, 2, 3, 4, 5]}' > /app/data/schedule_config.json
fi

# Initialize cron from config
python -c "
import json
import subprocess

config = json.load(open('/app/data/schedule_config.json'))
if config.get('enabled', True):
    times = config.get('times', [])
    weekdays = ','.join(str(d) for d in config.get('weekdays', [1,2,3,4,5]))

    # Group hours by minute for correct cron syntax
    minute_hours = {}
    for t in times:
        parts = t.split(':')
        if len(parts) == 2:
            minute = parts[1]
            hour = int(parts[0])
            if minute not in minute_hours:
                minute_hours[minute] = []
            if hour not in minute_hours[minute]:
                minute_hours[minute].append(hour)

    if minute_hours:
        cron_lines = []
        for minute, hours in minute_hours.items():
            hours_str = ','.join(str(h) for h in sorted(hours))
            cron_lines.append(f'{minute} {hours_str} * * {weekdays} cd /app && /usr/local/bin/python main.py >> /app/data/logs/cron.log 2>&1')
        cron_content = chr(10).join(cron_lines) + chr(10)
        subprocess.run(['crontab', '-'], input=cron_content.encode())
"

# Start admin web server in background
python /app/admin.py &

# Start cron in foreground
exec cron -f