# TourVisor MCP Server

MCP (Model Context Protocol) сервер для поиска туров через TourVisor API.

## 🚀 Возможности

- **Поиск туров** по 70+ странам и городам вылета
- **Обход блокировок** TourVisor
- **Параметризированный поиск**: даты, ночи, туристы, цены, звезды
- **Быстрый поиск** по текстовым запросам
- **Полные данные**: отели, цены, курорты, питание, операторы

## 📦 Установка

```bash
# Установка зависимостей
pip install -r requirements_mcp.txt

# Установка Playwright браузеров
playwright install chromium
```

## 🔧 Использование

### 1. Запуск MCP сервера

```bash
python3 mcp_server.py
```

### 2. Интеграция с нейросетями

#### 🔹 Claude Desktop (локально)
Добавьте в `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "tourvisor-api": {
      "command": "python3",
      "args": ["/путь/к/mcp_server.py"]
    }
  }
}
```

#### 🔹 OpenAI GPT (через MCP)
Для интеграции с GPT используйте MCP-клиент:
```python
from mcp import Client

async def search_with_gpt():
    client = Client()
    await client.connect_to_server("tourvisor-api", ["python3", "mcp_server.py"])
    
    result = await client.call_tool("search_tours", {
        "country": "Египет",
        "departure": "Москва",
        "nights_from": 7,
        "adults": 2
    })
    
    return result
```

#### 🔹 Anthropic Claude (API)
```python
import anthropic
from mcp import Client

client = anthropic.Anthropic()

async def claude_with_tour_search():
    # MCP клиент для туров
    mcp_client = Client()
    await mcp_client.connect_to_server("tourvisor-api", ["python3", "mcp_server.py"])
    
    response = client.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=1000,
        tools=[await mcp_client.list_tools()],
        messages=[{
            "role": "user", 
            "content": "Найди туры в Турцию из Москвы на 7 ночей для 2 взрослых"
        }]
    )
    
    return response
```

#### 🔹 Google Gemini (MCP интеграция)
```python
import google.generativeai as genai
from mcp import Client

async def gemini_tour_search():
    mcp_client = Client()
    await mcp_client.connect_to_server("tourvisor-api", ["python3", "mcp_server.py"])
    
    model = genai.GenerativeModel('gemini-pro')
    
    # Получаем инструменты от MCP сервера
    tools = await mcp_client.list_tools()
    
    response = model.generate_content(
        "Покажи лучшие отели в Дубае 5 звезд из Санкт-Петербурга",
        tools=tools
    )
    
    return response
```

#### 🔹 Llama 3 / Local LLM (Ollama + MCP)
```python
import ollama
from mcp import Client

async def llama_tour_search():
    mcp_client = Client()
    await mcp_client.connect_to_server("tourvisor-api", ["python3", "mcp_server.py"])
    
    response = ollama.chat(
        model='llama3',
        messages=[{
            'role': 'user',
            'content': 'Найди бюджетные туры в Египет из Казани'
        }],
        tools=await mcp_client.list_tools()
    )
    
    return response
```

#### 🔹 VPS HTTP API (для любых LLM)
Для VPS деплоя создай HTTP обертку:
```python
# http_server.py
from flask import Flask, request, jsonify
from mcp_server import TourMCPServer
import asyncio

app = Flask(__name__)
tour_server = TourMCPServer()

@app.route('/search_tours', methods=['POST'])
def search_tours():
    try:
        result = asyncio.run(tour_server.search_tours(request.json))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/quick_search', methods=['POST']) 
def quick_search():
    try:
        result = asyncio.run(tour_server.quick_search(request.json))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

Использование с любой LLM:
```bash
curl -X POST http://your-vps:8080/search_tours \
  -H "Content-Type: application/json" \
  -d '{
    "country": "ОАЭ",
    "departure": "Москва", 
    "nights_from": 5,
    "stars": 5
  }'
```

### 3. Доступные инструменты

#### `search_tours` - Основной поиск
```json
{
  "country": "Египет",
  "departure": "Казань", 
  "date_from": "01.02.2026",
  "date_to": "28.02.2026",
  "nights_from": 3,
  "nights_to": 3,
  "adults": 1,
  "price_max": 100000,
  "stars": 4
}
```

#### `quick_search` - Быстрый поиск
```json
{
  "query": "Дубай из Москвы на 5 ночей 5 звезд"
}
```

#### `get_countries` - Список стран
```json
{}
```

#### `get_departures` - Список городов вылета
```json
{}
```

## 🌍 Поддерживаемые направления

### Страны
- Турция, Египет, ОАЭ, Таиланд
- Кипр, Греция, Испания, Италия, Франция

### Города вылета
**Россия:** Москва, СПб, Новосибирск, Екатеринбург, Казань, Нижний Новгород, Челябинск, Омск, Самара, Ростов-на-Дону

**Казахстан:** Алматы, Астана

**Беларусь:** Минск, Брест, Гродно, Витебск, Могилев, Гомель

## 🤖 Примеры использования с разными LLM

### Claude Desktop
```
Пользователь: Найди туры из Казани в Египет на 3 ночи в феврале для 1 человека до 100000 рублей

Claude: [Использует MCP сервер] 
✅ Найдено 10 туров от 87,393 руб:
- Sand Beach 3★ (Хургада) - 87,393 руб
- Sharm Cliff Resort 3★ - 89,192 руб
- Fortuna 3★ - 91,791 руб
...
```

### OpenAI GPT
```python
# GPT вызывает инструменты MCP
result = await client.call_tool("quick_search", {
    "query": "Дубай из Москвы на 5 ночей 5 звезд до 150000"
})

# GPT анализирует результат и рекомендует:
"Найдено 24 тура. Рекомендую Beach Club Doganay 5★ за 66,504 руб - лучший рейтинг и Aqua Park"
```

### Google Gemini
```python
response = model.generate_content(
    "Сравни цены на туры в Турцию из Москвы и Казани",
    tools=mcp_tools
)

# Gemini получает данные и создает сравнительную таблицу
```

### Llama 3 (Local)
```python
response = ollama.chat(
    model='llama3',
    messages=[{
        'role': 'user',
        'content': 'Покажи всеinclusive туры в ОАЭ из Новосибирска'
    }],
    tools=tools
)
```

## 🌐 VPS Деплой

### 1. Подготовка VPS
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python и зависимостей
sudo apt install python3 python3-pip python3-venv -y

# Клонирование репозитория
git clone https://github.com/ТВОЙ_НИК/tourvisor-mcp-server.git
cd tourvisor-mcp-server

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements_mcp.txt

# Установка браузеров Playwright
playwright install chromium
```

### 2. Запуск HTTP сервера
```bash
# Запуск напрямую
python3 http_server.py

# Или через Gunicorn (рекомендуется)
gunicorn -w 4 -b 0.0.0.0:8080 http_server:app
```

### 3. Systemd сервис (24/7)
Создай файл `/etc/systemd/system/tourvisor-api.service`:
```ini
[Unit]
Description=TourVisor HTTP API Server
After=network.target

[Service]
Type=exec
User=ubuntu
WorkingDirectory=/home/ubuntu/tourvisor-mcp-server
Environment=PATH=/home/ubuntu/tourvisor-mcp-server/venv/bin
ExecStart=/home/ubuntu/tourvisor-mcp-server/venv/bin/gunicorn -w 4 -b 0.0.0.0:8080 http_server:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Запуск сервиса:
```bash
sudo systemctl daemon-reload
sudo systemctl enable tourvisor-api
sudo systemctl start tourvisor-api
sudo systemctl status tourvisor-api
```

### 4. Nginx прокси (опционально)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 5. Примеры использования с разных LLM

#### Python (OpenAI/Anthropic/Claude)
```python
import requests

# Поиск туров
response = requests.post('http://your-vps:8080/search_tours', json={
    "country": "Египет",
    "departure": "Казань",
    "nights_from": 3,
    "adults": 1,
    "price_max": 100000
})

tours = response.json()
print(f"Найдено туров: {tours['count']}")

# Быстрый поиск
response = requests.post('http://your-vps:8080/quick_search', json={
    "query": "Дубай из Москвы на 5 ночей 5 звезд"
})
```

#### JavaScript/Node.js
```javascript
const response = await fetch('http://your-vps:8080/search_tours', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        country: "ОАЭ",
        departure: "Москва",
        nights_from: 5,
        stars: 5
    })
});

const tours = await response.json();
console.log(`Найдено: ${tours.count} туров`);
```

#### cURL
```bash
curl -X POST http://your-vps:8080/quick_search \
  -H "Content-Type: application/json" \
  -d '{"query": "Турция всеinclusive из СПб на 7 ночей"}'
```

### 6. Мониторинг
```bash
# Проверка здоровья
curl http://your-vps:8080/health

# Статистика
curl http://your-vps:8080/stats

# Логи
sudo journalctl -u tourvisor-api -f
```

### Поиск туров из Казани в Египет
```
Найди туры из Казани в Египет на 3 ночи в феврале для 1 человека до 100000 рублей
```

### Поиск 5-звездочных отелей в Дубае
```
Покажи 5-звездочные отели в Дубае из Москвы на 5 ночей до 150000 рублей
```

### Сравнение цен
```
Сравни цены на туры в Турцию из Москвы и Казани на 7 ночей
```

## 🎯 Результаты поиска

Каждый тур содержит:
- **Отель**: название и звездность
- **Цена**: в рублях
- **Курорт**: город/регион
- **Даты**: вылета и возвращения
- **Питание**: тип (AI, HB, BB и т.д.)
- **Оператор**: туроператор
- **Рейтинг**: отеля

## 🔍 Особенности

- **Обход блокировок**: автоматическое заполнение форм TourVisor
- **Real-time данные**: актуальные цены и наличие
- **Гибкая фильтрация**: по цене, звездам, питанию, курортам
- **Мультигородской поиск**: сравнение из разных городов вылета

## 🛠️ API Структура

```
TourMCPServer
├── search_tours()     # Основной поиск
├── quick_search()     # Текстовый поиск  
├── get_countries()    # Список стран
└── get_departures()   # Список городов
```

## 📝 Логирование

Сервер логирует:
- Успешные поиски
- Ошибки заполнения форм
- Найденные туры
- Статистику поиска

## 🚨 Важно

- Сервер работает в headless режиме
- Автоматически обходит CAPTCHA и блокировки
- Использует реальные браузеры для точности данных
- Поддерживает одновременные запросы

---

**TourVisor MCP Server** - твой персональный API для поиска туров! 🌴✈️
