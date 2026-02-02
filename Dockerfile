FROM python:3.11-slim

# Установка системных зависимостей для Playwright
RUN apt-get update && apt-get install -y \
    ca-certificates \
    wget \
    curl \
    gnupg \
    libnss3 \
    libatk1.0-0 \
    libdrm2 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    libgtk-3-0 \
    fonts-liberation \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Установка Python зависимостей
COPY requirements_mcp.txt .
RUN pip install --no-cache-dir -r requirements_mcp.txt

# Установка Playwright и браузеров
RUN playwright install chromium
RUN playwright install-deps chromium

# Настройка переменных окружения
ENV PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright
ENV DISPLAY=:99

# Копирование кода
COPY . .

# Запуск HTTP сервера
CMD ["python3", "http_server.py"]
