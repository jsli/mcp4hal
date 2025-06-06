#!/usr/bin/env bash

echo "本地启动fastapi服务"

.venv/bin/uvicorn server:app --reload  --host 0.0.0.0 --port 8881 --log-level debug
# gunicorn --workers 4 --worker-class uvicorn.workers.UvicornWorker --timeout 300 --keep-alive 1000 server:app --log-level debug -b 127.0.0.1:8881
