FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копирование зависимостей
COPY requirements_mcp.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements_mcp.txt

# Установка браузеров Playwright
RUN playwright install chromium
RUN playwright install-deps chromium

# Копирование исходного кода
COPY . .

# Создание start.sh
RUN echo '#!/bin/bash\n\
echo "🚀 Starting TourVisor MCP Server..."\n\
python3 http_server.py' > start.sh && chmod +x start.sh

# Открытие порта
EXPOSE 8080

# Запуск
CMD ["./start.sh"]
