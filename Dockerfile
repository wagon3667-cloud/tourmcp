FROM python:3.11-slim

# Установка системных зависимостей для Playwright (совместимо с Debian)
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    curl \
    unzip \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    libgdk-pixbuf-xlib-2.0-0 \
    fonts-liberation \
    libu2f-udev \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование зависимостей
COPY requirements_mcp.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements_mcp.txt

# Установка браузеров Playwright БЕЗ системных зависимостей
RUN playwright install chromium

# Копирование исходного кода
COPY . .

# Создание start.sh с переменными окружения
RUN echo '#!/bin/bash\n\
export PLAYWRIGHT_BROWSERS_PATH=/ms-playwright\n\
export DISPLAY=:99\n\
echo "🚀 Starting TourVisor MCP Server..."\n\
python3 http_server.py' > start.sh && chmod +x start.sh

# Открытие порта
EXPOSE 8080

# Запуск
CMD ["./start.sh"]
