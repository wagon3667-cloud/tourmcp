#!/usr/bin/env python3
"""
MCP клиент для Claude Desktop с TourVisor API
"""

import asyncio
import json
import subprocess
from typing import Any, Dict, List

class TourVisorMCPClient:
    def __init__(self, api_url: str = "https://tourmcp.onrender.com"):
        self.api_url = api_url
    
    async def search_tours(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Поиск туров через HTTP API"""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/search_tours",
                json=params,
                headers={"Content-Type": "application/json"}
            ) as response:
                return await response.json()
    
    async def quick_search(self, query: str) -> Dict[str, Any]:
        """Быстрый поиск по текстовому запросу"""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.api_url}/quick_search",
                json={"query": query},
                headers={"Content-Type": "application/json"}
            ) as response:
                return await response.json()
    
    async def get_countries(self) -> List[str]:
        """Получить список стран"""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}/get_countries") as response:
                data = await response.json()
                return [country["name"] for country in data["countries"]]
    
    async def get_departures(self) -> List[str]:
        """Получить список городов вылета"""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}/get_departures") as response:
                data = await response.json()
                return [city["name"] for city in data["departures"]]

# Claude Desktop MCP Server
async def main():
    """Основная функция для MCP сервера"""
    import sys
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    
    client = TourVisorMCPClient()
    server = Server("tourvisor-http-client")
    
    @server.list_tools()
    async def list_tools() -> List[Tool]:
        return [
            Tool(
                name="search_tours",
                description="Поиск туров через TourVisor API",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "country": {"type": "string", "description": "Страна"},
                        "departure": {"type": "string", "description": "Город вылета"},
                        "nights_from": {"type": "integer", "description": "Ночей от"},
                        "adults": {"type": "integer", "description": "Взрослых"}
                    },
                    "required": ["country", "departure"]
                }
            ),
            Tool(
                name="quick_search",
                description="Быстрый поиск по тексту",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Текстовый запрос"}
                    },
                    "required": ["query"]
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: Dict[str, Any]):
        if name == "search_tours":
            result = await client.search_tours(arguments)
            return {"content": [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]}
        elif name == "quick_search":
            result = await client.quick_search(arguments["query"])
            return {"content": [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, indent=2))]}
    
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)

if __name__ == "__main__":
    asyncio.run(main())
