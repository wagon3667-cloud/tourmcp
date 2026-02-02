#!/usr/bin/env python3
"""
Простой HTTP API сервер для TourVisor без Playwright
Возвращает моковые данные для демонстрации работы MCP
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Моковые данные туров
MOCK_TOURS = [
    {
        "hotel": "Beach Resort Hotel 5★",
        "price": 125000,
        "stars": 5,
        "resort": "Кемер",
        "rating": 4.8,
        "nights": 7,
        "date_from": "15.02.2026",
        "date_to": "22.02.2026",
        "meal": "Все включено",
        "operator": "Anex Tour",
        "link": "https://eto.travel/tour/123"
    },
    {
        "hotel": "Sea View Hotel 4★",
        "price": 89000,
        "stars": 4,
        "resort": "Алания",
        "rating": 4.5,
        "nights": 7,
        "date_from": "18.02.2026",
        "date_to": "25.02.2026",
        "meal": "Завтрак и ужин",
        "operator": "Pegas Touristik",
        "link": "https://eto.travel/tour/456"
    },
    {
        "hotel": "Mountain Paradise 5★",
        "price": 156000,
        "stars": 5,
        "resort": "Белек",
        "rating": 4.9,
        "nights": 7,
        "date_from": "20.02.2026",
        "date_to": "27.02.2026",
        "meal": "Ультра все включено",
        "operator": "TUI",
        "link": "https://eto.travel/tour/789"
    }
]

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка здоровья API"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0-simple"
    })

@app.route('/search_tours', methods=['POST'])
def search_tours():
    """Поиск туров"""
    try:
        params = request.get_json()
        
        # Фильтруем туры по параметрам
        filtered_tours = MOCK_TOURS.copy()
        
        if params.get('country'):
            # Имитация фильтрации по стране
            filtered_tours = [t for t in filtered_tours if t['price'] > 50000]
        
        if params.get('stars'):
            stars = params.get('stars')
            filtered_tours = [t for t in filtered_tours if t['stars'] == stars]
        
        if params.get('max_price'):
            max_price = params.get('max_price')
            filtered_tours = [t for t in filtered_tours if t['price'] <= max_price]
        
        return jsonify({
            "success": True,
            "tours": filtered_tours,
            "count": len(filtered_tours),
            "params": params
        })
        
    except Exception as e:
        logger.error(f"Error in search_tours: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/quick_search', methods=['POST'])
def quick_search():
    """Быстрый поиск по текстовому запросу"""
    try:
        data = request.get_json()
        query = data.get('query', '').lower()
        
        # Парсинг запроса
        filtered_tours = MOCK_TOURS.copy()
        
        if 'турция' in query or 'туреч' in query:
            filtered_tours = [t for t in filtered_tours if t['price'] < 200000]
        
        if '5 звезд' in query or '5★' in query:
            filtered_tours = [t for t in filtered_tours if t['stars'] == 5]
        
        if 'дешев' in query:
            filtered_tours = [t for t in filtered_tours if t['price'] < 100000]
        
        return jsonify({
            "success": True,
            "tours": filtered_tours,
            "count": len(filtered_tours),
            "query": query
        })
        
    except Exception as e:
        logger.error(f"Error in quick_search: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/get_countries', methods=['GET'])
def get_countries():
    """Получить список стран"""
    countries = [
        {"name": "Турция", "id": "turkey"},
        {"name": "Египет", "id": "egypt"},
        {"name": "ОАЭ", "id": "uae"},
        {"name": "Таиланд", "id": "thailand"},
        {"name": "Кипр", "id": "cyprus"},
        {"name": "Греция", "id": "greece"},
        {"name": "Испания", "id": "spain"},
        {"name": "Италия", "id": "italy"},
        {"name": "Франция", "id": "france"}
    ]
    
    return jsonify({
        "success": True,
        "countries": countries
    })

@app.route('/get_departures', methods=['GET'])
def get_departures():
    """Получить список городов вылета"""
    departures = [
        {"name": "Москва", "id": "moscow"},
        {"name": "Санкт-Петербург", "id": "spb"},
        {"name": "Казань", "id": "kazan"},
        {"name": "Екатеринбург", "id": "ekb"},
        {"name": "Новосибирск", "id": "nsk"},
        {"name": "Ростов-на-Дону", "id": "rnd"},
        {"name": "Уфа", "id": "ufa"},
        {"name": "Краснодар", "id": "krd"},
        {"name": "Алматы", "id": "almaty"},
        {"name": "Минск", "id": "minsk"}
    ]
    
    return jsonify({
        "success": True,
        "departures": departures
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    """Статистика API"""
    return jsonify({
        "success": True,
        "stats": {
            "total_tours": len(MOCK_TOURS),
            "countries": 9,
            "departures": 10,
            "api_version": "1.0.0-simple",
            "server": "Render"
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
