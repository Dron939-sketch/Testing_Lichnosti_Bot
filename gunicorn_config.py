# gunicorn_config.py
import multiprocessing

# Количество воркеров
workers = multiprocessing.cpu_count() * 2 + 1

# Порт
bind = "0.0.0.0:10000"

# Таймауты
timeout = 120
keepalive = 5

# Логирование
accesslog = "-"  # stdout
errorlog = "-"   # stdout
loglevel = "info"

# Перезапуск при ошибках
max_requests = 1000
max_requests_jitter = 50
