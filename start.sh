#!/bin/bash

# Railway deployment script for TourVisor MCP Server

echo "🚀 Starting TourVisor MCP Server on Railway..."

# Установка зависимостей
echo "📦 Installing dependencies..."
pip install -r requirements_mcp.txt

# Установка браузеров Playwright
echo "🌐 Installing Playwright browsers..."
playwright install chromium

# Запуск HTTP сервера
echo "🌍 Starting HTTP API server..."
python3 http_server.py
