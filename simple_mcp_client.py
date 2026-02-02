#!/usr/bin/env python3
"""
Простой MCP клиент для TourVisor API без внешних зависимостей
Работает с системным Python
"""

import json
import sys
import urllib.request
import urllib.parse
import asyncio
import subprocess

class TourVisorAPI:
    def __init__(self, base_url="https://tourmcp.onrender.com"):
        self.base_url = base_url
    
    def search_tours(self, params):
        """Поиск туров через HTTP API"""
        try:
            data = json.dumps(params).encode('utf-8')
            req = urllib.request.Request(
                f"{self.base_url}/search_tours",
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def quick_search(self, query):
        """Быстрый поиск по текстовому запросу"""
        try:
            data = json.dumps({"query": query}).encode('utf-8')
            req = urllib.request.Request(
                f"{self.base_url}/quick_search",
                data=data,
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            return {"error": str(e), "success": False}
    
    def get_countries(self):
        """Получить список стран"""
        try:
            with urllib.request.urlopen(f"{self.base_url}/get_countries") as response:
                data = json.loads(response.read().decode('utf-8'))
                return [country["name"] for country in data.get("countries", [])]
        except Exception as e:
            return []
    
    def get_departures(self):
        """Получить список городов вылета"""
        try:
            with urllib.request.urlopen(f"{self.base_url}/get_departures") as response:
                data = json.loads(response.read().decode('utf-8'))
                return [city["name"] for city in data.get("departures", [])]
        except Exception as e:
            return []

def main():
    """Основная функция для обработки MCP запросов"""
    api = TourVisorAPI()
    
    # Бесконечный цикл для обработки запросов
    while True:
        try:
            # Читаем JSON из stdin
            line = sys.stdin.readline()
            if not line:
                continue
            
            request = json.loads(line.strip())
            
            # Обрабатываем запрос
            if request.get("method") == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "protocolVersion": "2025-06-18",
                        "capabilities": {
                            "tools": {
                                "listChanged": True
                            }
                        },
                        "serverInfo": {
                            "name": "tourvisor-api",
                            "version": "1.0.0"
                        }
                    }
                }
            
            elif request.get("method") == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "tools": [
                            {
                                "name": "search_tours",
                                "description": "Поиск туров через TourVisor API",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "country": {"type": "string", "description": "Страна"},
                                        "departure": {"type": "string", "description": "Город вылета"},
                                        "nights_from": {"type": "integer", "description": "Ночей от"},
                                        "adults": {"type": "integer", "description": "Взрослых"}
                                    },
                                    "required": ["country", "departure"]
                                }
                            },
                            {
                                "name": "quick_search",
                                "description": "Быстрый поиск по тексту",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "query": {"type": "string", "description": "Текстовый запрос"}
                                    },
                                    "required": ["query"]
                                }
                            }
                        ]
                    }
                }
            
            elif request.get("method") == "tools/call":
                params = request.get("params", {})
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                if tool_name == "search_tours":
                    result = api.search_tours(arguments)
                elif tool_name == "quick_search":
                    result = api.quick_search(arguments.get("query", ""))
                else:
                    result = {"error": f"Unknown tool: {tool_name}"}
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, ensure_ascii=False, indent=2)
                            }
                        ]
                    }
                }
            
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "error": {"code": -32601, "message": "Method not found"}
                }
            
            # Отправляем ответ
            print(json.dumps(response, ensure_ascii=False))
            sys.stdout.flush()
            
        except json.JSONDecodeError:
            continue
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {"code": -32603, "message": str(e)}
            }
            print(json.dumps(error_response, ensure_ascii=False))
            sys.stdout.flush()

if __name__ == "__main__":
    main()
