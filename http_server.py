#!/usr/bin/env python3
"""
HTTP API сервер для TourVisor MCP
Позволяет любым LLM получать доступ к поиску туров через HTTP
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio
import json
import logging
from datetime import datetime
import traceback
import os

# Импортируем наш MCP сервер
from fixed_departure_api import FixedTourvisorAPI, TourSearchParams, Country, Departure

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для всех доменов

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Устанавливаем правильный путь к браузерам
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = '/root/.cache/ms-playwright'

class HTTPWrapper:
    def __init__(self):
        self.tour_api = FixedTourvisorAPI()
    
    async def search_tours_async(self, params):
        """Асинхронная обертка для поиска туров"""
        try:
            async with self.tour_api as api:
                # Запуск браузера с правильными путями
                browser = await api.p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                
                tours = await api.search_tours(params)
                
                # Конвертируем туры в JSON
                tours_json = []
                for tour in tours:
                    tours_json.append({
                        "hotel": tour.hotel,
                        "price": tour.price,
                        "stars": tour.stars,
                        "resort": tour.resort,
                        "rating": tour.rating,
                        "nights": tour.nights,
                        "date_from": tour.date_from,
                        "date_to": tour.date_to,
                        "meal": tour.meal,
                        "operator": tour.operator,
                        "link": tour.link
                    })
                
                await browser.close()
                return {"success": True, "tours": tours_json, "count": len(tours_json)}
                
        except Exception as e:
            logger.error(f"Error in search_tours_async: {str(e)}")
            logger.error(traceback.format_exc())
            return {"success": False, "error": str(e)}
    
    def parse_query(self, query):
        """Парсинг текстового запроса"""
        import re
        
        # Значения по умолчанию
        country = Country.TURKEY
        departure = Departure.MOSCOW
        nights = 7
        adults = 2
        stars = None
        price_max = None
        
        query_lower = query.lower()
        
        # Ищем страну
        for c in Country:
            if c.value.lower() in query_lower:
                country = c
                break
        
        # Ищем город вылета
        for d in Departure:
            if d.value.lower() in query_lower:
                departure = d
                break
        
        # Ищем количество ночей
        nights_match = re.search(r'(\d+)\s*(?:ночей|ночи|ночь)', query_lower)
        if nights_match:
            nights = int(nights_match.group(1))
        
        # Ищем количество человек
        people_match = re.search(r'(\d+)\s*(?:человек|человека|чел)', query_lower)
        if people_match:
            adults = int(people_match.group(1))
        
        # Ищем звезды
        stars_match = re.search(r'(\d+)\s*(?:звезд|звезды|звезда)', query_lower)
        if stars_match:
            stars = int(stars_match.group(1))
        
        # Ищем цену
        price_match = re.search(r'до\s*(\d+)\s*(?:руб|рублей)', query_lower)
        if price_match:
            price_max = int(price_match.group(1))
        
        return TourSearchParams(
            country=country,
            departure=departure,
            nights_from=nights,
            nights_to=nights,
            adults=adults,
            stars=stars,
            price_max=price_max
        )

# Создаем экземпляр обертки
http_wrapper = HTTPWrapper()

@app.route('/health', methods=['GET'])
def health_check():
    """Проверка здоровья сервера"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@app.route('/search_tours', methods=['POST'])
def search_tours():
    """Основной поиск туров"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error": "No JSON data provided"
            }), 400
        
        # Валидация обязательных полей
        if 'country' not in data:
            return jsonify({
                "success": False,
                "error": "Country is required"
            }), 400
        
        if 'departure' not in data:
            return jsonify({
                "success": False,
                "error": "Departure city is required"
            }), 400
        
        # Конвертируем аргументы
        country = data.get("country")
        departure = data.get("departure")
        
        # Ищем в Enum
        country_enum = None
        for c in Country:
            if c.value == country:
                country_enum = c
                break
        
        departure_enum = None
        for d in Departure:
            if d.value == departure:
                departure_enum = d
                break
        
        if not country_enum:
            return jsonify({
                "success": False,
                "error": f"Unknown country: {country}"
            }), 400
        
        if not departure_enum:
            return jsonify({
                "success": False,
                "error": f"Unknown departure city: {departure}"
            }), 400
        
        # Создаем параметры
        params = TourSearchParams(
            country=country_enum,
            departure=departure_enum,
            date_from=data.get("date_from", "01.12.2025"),
            date_to=data.get("date_to", "31.12.2025"),
            nights_from=data.get("nights_from", 7),
            nights_to=data.get("nights_to", 7),
            adults=data.get("adults", 2),
            children=data.get("children", 0),
            price_max=data.get("price_max"),
            stars=data.get("stars"),
            meal=data.get("meal", "любой"),
            resort=data.get("resort", "любой")
        )
        
        # Выполняем поиск
        result = asyncio.run(http_wrapper.search_tours_async(params))
        
        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.error(f"Error in search_tours: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/quick_search', methods=['POST'])
def quick_search():
    """Быстрый поиск по текстовому запросу"""
    try:
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                "success": False,
                "error": "Query is required"
            }), 400
        
        query = data['query']
        params = http_wrapper.parse_query(query)
        
        # Выполняем поиск
        result = asyncio.run(http_wrapper.search_tours_async(params))
        
        # Добавляем информацию о парсинге
        if result["success"]:
            result["query"] = query
            result["parsed_params"] = {
                "country": params.country.value if isinstance(params.country, Country) else params.country,
                "departure": params.departure.value if isinstance(params.departure, Departure) else params.departure,
                "nights_from": params.nights_from,
                "adults": params.adults,
                "stars": params.stars,
                "price_max": params.price_max
            }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in quick_search: {e}")
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/get_countries', methods=['GET'])
def get_countries():
    """Получить список стран"""
    countries = [{"name": country.value, "code": country.name} for country in Country]
    return jsonify({
        "success": True,
        "countries": countries,
        "count": len(countries)
    })

@app.route('/get_departures', methods=['GET'])
def get_departures():
    """Получить список городов вылета"""
    departures = [{"name": departure.value, "code": departure.name} for departure in Departure]
    return jsonify({
        "success": True,
        "departures": departures,
        "count": len(departures)
    })

@app.route('/stats', methods=['GET'])
def get_stats():
    """Статистика сервера"""
    return jsonify({
        "success": True,
        "server": "TourVisor HTTP API",
        "version": "1.0.0",
        "endpoints": [
            "GET /health - Проверка здоровья",
            "POST /search_tours - Основной поиск",
            "POST /quick_search - Поиск по тексту",
            "GET /get_countries - Список стран",
            "GET /get_departures - Список городов",
            "GET /stats - Статистика"
        ],
        "supported_countries": len(Country),
        "supported_departures": len(Departure),
        "timestamp": datetime.now().isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "available_endpoints": [
            "GET /health",
            "POST /search_tours", 
            "POST /quick_search",
            "GET /get_countries",
            "GET /get_departures",
            "GET /stats"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "timestamp": datetime.now().isoformat()
    }), 500

if __name__ == '__main__':
    print("🚀 Запуск TourVisor HTTP API сервера...")
    print("📍 Доступные эндпоинты:")
    print("  GET  /health - Проверка здоровья")
    print("  POST /search_tours - Основной поиск")
    print("  POST /quick_search - Поиск по тексту")
    print("  GET  /get_countries - Список стран")
    print("  GET  /get_departures - Список городов")
    print("  GET  /stats - Статистика")
    print("\n🌐 Сервер запущен на http://localhost:8080")
    
    app.run(host='0.0.0.0', port=8080, debug=False)
