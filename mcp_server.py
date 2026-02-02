#!/usr/bin/env python3
"""
MCP Server для TourVisor API
Позволяет искать туры через Model Context Protocol
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

# MCP импорты
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent
)

# Наш API
from fixed_departure_api import FixedTourvisorAPI, TourSearchParams, Country, Departure

class TourMCPServer:
    def __init__(self):
        self.server = Server("tourvisor-api")
        self.setup_handlers()
    
    def setup_handlers(self):
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            return [
                Tool(
                    name="search_tours",
                    description="Поиск туров через TourVisor API",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "country": {
                                "type": "string",
                                "description": "Страна назначения",
                                "enum": ["Турция", "Египет", "ОАЭ", "Таиланд", "Кипр", "Греция", "Испания", "Италия", "Франция"]
                            },
                            "departure": {
                                "type": "string", 
                                "description": "Город вылета",
                                "enum": ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань", 
                                       "Нижний Новгород", "Челябинск", "Омск", "Самара", "Ростов-на-Дону",
                                       "Алматы", "Астана", "Минск", "Брест", "Гродно", "Витебск", "Могилев", "Гомель"]
                            },
                            "date_from": {
                                "type": "string",
                                "description": "Дата начала (ДД.ММ.ГГГГ)",
                                "pattern": r"\d{2}\.\d{2}\.\d{4}"
                            },
                            "date_to": {
                                "type": "string", 
                                "description": "Дата окончания (ДД.ММ.ГГГГ)",
                                "pattern": r"\d{2}\.\d{2}\.\d{4}"
                            },
                            "nights_from": {
                                "type": "integer",
                                "description": "Количество ночей от",
                                "minimum": 1,
                                "maximum": 30
                            },
                            "nights_to": {
                                "type": "integer",
                                "description": "Количество ночей до", 
                                "minimum": 1,
                                "maximum": 30
                            },
                            "adults": {
                                "type": "integer",
                                "description": "Количество взрослых",
                                "minimum": 1,
                                "maximum": 10
                            },
                            "children": {
                                "type": "integer",
                                "description": "Количество детей",
                                "minimum": 0,
                                "maximum": 10
                            },
                            "price_max": {
                                "type": "integer",
                                "description": "Максимальная цена в рублях",
                                "minimum": 0
                            },
                            "stars": {
                                "type": "integer",
                                "description": "Количество звезд отеля",
                                "minimum": 1,
                                "maximum": 5
                            },
                            "meal": {
                                "type": "string",
                                "description": "Тип питания",
                                "enum": ["любой", "All Inclusive", "Ultra All Inclusive", "Full Board", "Half Board", "Bed & Breakfast"]
                            },
                            "resort": {
                                "type": "string",
                                "description": "Курорт (или 'любой')"
                            }
                        },
                        "required": ["country", "departure"]
                    }
                ),
                Tool(
                    name="get_countries",
                    description="Получить список доступных стран",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_departures", 
                    description="Получить список доступных городов вылета",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="quick_search",
                    description="Быстрый поиск туров по простым параметрам",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Текстовый запрос (например: 'Дубай из Москвы на 5 ночей 5 звезд')"
                            }
                        },
                        "required": ["query"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
            try:
                if name == "search_tours":
                    return await self.search_tours(arguments)
                elif name == "get_countries":
                    return await self.get_countries(arguments)
                elif name == "get_departures":
                    return await self.get_departures(arguments)
                elif name == "quick_search":
                    return await self.quick_search(arguments)
                else:
                    return CallToolResult(
                        content=[TextContent(type="text", text=f"Неизвестный инструмент: {name}")]
                    )
            except Exception as e:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Ошибка: {str(e)}")]
                )
    
    async def search_tours(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Основной поиск туров"""
        try:
            # Конвертируем аргументы в параметры
            country = arguments.get("country", "Турция")
            departure = arguments.get("departure", "Москва")
            
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
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Неизвестная страна: {country}")]
                )
            
            if not departure_enum:
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Неизвестный город вылета: {departure}")]
                )
            
            params = TourSearchParams(
                country=country_enum,
                departure=departure_enum,
                date_from=arguments.get("date_from", "01.12.2025"),
                date_to=arguments.get("date_to", "31.12.2025"),
                nights_from=arguments.get("nights_from", 7),
                nights_to=arguments.get("nights_to", 7),
                adults=arguments.get("adults", 2),
                children=arguments.get("children", 0),
                price_max=arguments.get("price_max"),
                stars=arguments.get("stars"),
                meal=arguments.get("meal", "любой"),
                resort=arguments.get("resort", "любой")
            )
            
            async with FixedTourvisorAPI() as api:
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
                        "date": tour.date,
                        "meal": tour.meal,
                        "operator": tour.operator,
                        "country": tour.country
                    })
                
                result = {
                    "success": True,
                    "count": len(tours),
                    "tours": tours_json,
                    "params": {
                        "country": country,
                        "departure": departure,
                        "date_from": params.date_from,
                        "date_to": params.date_to,
                        "nights_from": params.nights_from,
                        "nights_to": params.nights_to,
                        "adults": params.adults,
                        "children": params.children,
                        "price_max": params.price_max,
                        "stars": params.stars,
                        "meal": params.meal,
                        "resort": params.resort
                    }
                }
                
                return CallToolResult(
                    content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
                )
                
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Ошибка поиска: {str(e)}")]
            )
    
    async def get_countries(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Получить список стран"""
        countries = [country.value for country in Country]
        result = {
            "success": True,
            "countries": countries
        }
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        )
    
    async def get_departures(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Получить список городов вылета"""
        departures = [departure.value for departure in Departure]
        result = {
            "success": True,
            "departures": departures
        }
        return CallToolResult(
            content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
        )
    
    async def quick_search(self, arguments: Dict[str, Any]) -> CallToolResult:
        """Быстрый поиск по текстовому запросу"""
        query = arguments.get("query", "").lower()
        
        # Парсим текстовый запрос
        params = self.parse_query(query)
        
        async with FixedTourvisorAPI() as api:
            tours = await api.search_tours(params)
            
            tours_json = []
            for tour in tours:
                tours_json.append({
                    "hotel": tour.hotel,
                    "price": tour.price,
                    "stars": tour.stars,
                    "resort": tour.resort,
                    "rating": tour.rating,
                    "nights": tour.nights,
                    "date": tour.date,
                    "meal": tour.meal,
                    "operator": tour.operator,
                    "country": tour.country
                })
            
            result = {
                "success": True,
                "query": query,
                "parsed_params": {
                    "country": params.country.value if isinstance(params.country, Country) else params.country,
                    "departure": params.departure.value if isinstance(params.departure, Departure) else params.departure,
                    "nights_from": params.nights_from,
                    "adults": params.adults,
                    "stars": params.stars
                },
                "count": len(tours),
                "tours": tours_json
            }
            
            return CallToolResult(
                content=[TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]
            )
    
    def parse_query(self, query: str) -> TourSearchParams:
        """Парсинг текстового запроса"""
        import re
        
        # Значения по умолчанию
        country = Country.TURKEY
        departure = Departure.MOSCOW
        nights = 7
        adults = 2
        stars = None
        
        # Ищем страну
        for c in Country:
            if c.value.lower() in query:
                country = c
                break
        
        # Ищем город вылета
        for d in Departure:
            if d.value.lower() in query:
                departure = d
                break
        
        # Ищем количество ночей
        nights_match = re.search(r'(\d+)\s*(?:ночей|ночи|ночь)', query)
        if nights_match:
            nights = int(nights_match.group(1))
        
        # Ищем количество человек
        people_match = re.search(r'(\d+)\s*(?:человек|человека|чел)', query)
        if people_match:
            adults = int(people_match.group(1))
        
        # Ищем звезды
        stars_match = re.search(r'(\d+)\s*(?:звезд|звезды|звезда)', query)
        if stars_match:
            stars = int(stars_match.group(1))
        
        return TourSearchParams(
            country=country,
            departure=departure,
            nights_from=nights,
            nights_to=nights,
            adults=adults,
            stars=stars
        )

async def main():
    """Запуск MCP сервера"""
    server_instance = TourMCPServer()
    
    # Используем stdio_server для MCP
    async with stdio_server() as (read_stream, write_stream):
        await server_instance.server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="tourvisor-api",
                server_version="1.0.0",
                capabilities=server_instance.server.get_capabilities(
                    notification_options=None,
                    experimental_capabilities=None,
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
