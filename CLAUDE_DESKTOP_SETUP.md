# 🔗 Claude Desktop + TourVisor API Integration

## 🎯 Твой API работает: https://tourmcp.onrender.com

## 📋 Установка для Claude Desktop

### 1. Установка зависимостей
```bash
pip install mcp aiohttp
```

### 2. Настройка Claude Desktop

Добавь в `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "tourvisor-api": {
      "command": "python3",
      "args": ["/Users/mironfedorovich/eto-parser/claude_mcp_client.py"]
    }
  }
}
```

### 3. Перезапуск Claude Desktop
- Закрой Claude Desktop
- Открой снова
- Проверь что сервер подключен

## 🤖 Примеры использования с Claude

### Поиск туров:
```
Пользователь: Найди туры в Египет из Москвы на 7 ночей для 2 взрослых

Claude: [Использует tourvisor-api]
✅ Найдено 24 тура:
- Sand Beach 3★ (Хургада) - 87,393 руб
- Sharm Cliff Resort 3★ - 89,192 руб
...
```

### Быстрый поиск:
```
Пользователь: Покажи 5-звездочные отели в Дубае до 150000

Claude: [Вызывает quick_search]
🏨 Найдены 5-звездочные отели:
- Beach Club Doganay 5★ - 66,504 руб
- Alp Pasa Hotel 5★ - 58,796 руб
...
```

## 🌐 Прямые HTTP запросы

### Python:
```python
import requests

response = requests.post('https://tourmcp.onrender.com/quick_search', json={
    "query": "Турция всеinclusive из Казани"
})

tours = response.json()
print(f"Найдено: {tours['count']} туров")
```

### JavaScript:
```javascript
const response = await fetch('https://tourmcp.onrender.com/search_tours', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        country: "ОАЭ",
        departure: "Москва",
        nights_from: 5,
        stars: 5
    })
});

const tours = await response.json();
```

## 📊 Доступные эндпоинты

- `GET /health` - проверка здоровья
- `POST /search_tours` - основной поиск
- `POST /quick_search` - быстрый поиск
- `GET /get_countries` - страны
- `GET /get_departures` - города вылета
- `GET /stats` - статистика

## 🎉 Готово к работе!

Твой TourVisor API теперь доступен для:
- ✅ Claude Desktop (MCP)
- ✅ Любых LLM (HTTP)
- ✅ Веб приложений
- ✅ Мобильных приложений
- ✅ Ботов и ассистентов

**Поздравляю! Твой MCP сервер в продакшене!** 🚀
