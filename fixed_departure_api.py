from playwright.async_api import async_playwright
import asyncio
import json
import re
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

class Country(Enum):
    TURKEY = "Турция"
    EGYPT = "Египет" 
    UAE = "ОАЭ"
    THAILAND = "Таиланд"
    CYPRUS = "Кипр"
    GREECE = "Греция"
    SPAIN = "Испания"
    ITALY = "Италия"
    FRANCE = "Франция"

class Departure(Enum):
    MOSCOW = "Москва"
    SPB = "Санкт-Петербург"
    NOVOSIBIRSK = "Новосибирск"
    EKATERINBURG = "Екатеринбург"
    KAZAN = "Казань"
    NIZHNY_NOVGOROD = "Нижний Новгород"
    CHELYABINSK = "Челябинск"
    OMSK = "Омск"
    SAMARA = "Самара"
    ROSTOV = "Ростов-на-Дону"
    # Казахстан
    ALMATY = "Алматы"
    ASTANA = "Астана"
    SHYMKENT = "Шымкент"
    AKTOBE = "Актобе"
    # Беларусь
    MINSK = "Минск"
    BREST = "Брест"
    GRODNO = "Гродно"
    VITEBSK = "Витебск"
    MOGILEV = "Могилев"
    GOMEL = "Гомель"

@dataclass
class TourSearchParams:
    country: Union[Country, str] = Country.TURKEY
    departure: Union[Departure, str] = Departure.MOSCOW
    date_from: str = "01.12.2025"
    date_to: str = "31.12.2025"
    nights_from: int = 7
    nights_to: int = 7
    adults: int = 2
    children: int = 0
    meal: str = "любой"
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    resort: str = "любой"
    stars: Optional[int] = None

@dataclass
class Tour:
    hotel: str
    price: str
    nights: str
    date: str
    date_to: str
    meal: str
    operator: str
    resort: str
    stars: str
    rating: str
    country: str = "N/A"

class FixedTourvisorAPI:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        
        # Маппинг стран
        self.country_selectors = {
            Country.TURKEY.value: "text=Турция",
            Country.EGYPT.value: "text=Египет", 
            Country.UAE.value: "text=ОАЭ",
            Country.THAILAND.value: "text=Таиланд",
            Country.CYPRUS.value: "text=Кипр",
            Country.GREECE.value: "text=Греция",
            Country.SPAIN.value: "text=Испания",
            Country.ITALY.value: "text=Италия",
            Country.FRANCE.value: "text=Франция"
        }
    
    async def __aenter__(self):
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def start(self):
        if not self.browser:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless, 
                slow_mo=500
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1440, 'height': 900},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
                locale="ru-RU",
                timezone_id="Europe/Moscow",
            )
            self.page = await self.context.new_page()
    
    async def close(self):
        if self.browser:
            await self.browser.close()
            self.browser = None
    
    async def search_tours(self, params: TourSearchParams) -> List[Tour]:
        await self.start()
        
        try:
            await self.page.goto("https://eto.travel/search/", timeout=120000)
            await asyncio.sleep(8)
            
            await self.page.wait_for_selector('.tv-search-form.tv-loaded', timeout=30000)
            await asyncio.sleep(3)
            
            await self._fill_form_correctly(params)
            await asyncio.sleep(20)
            
            tours = await self._extract_tours(params)
            return tours
            
        except Exception as e:
            print(f"❌ Ошибка поиска: {e}")
            return []
    
    async def _fill_form_correctly(self, params: TourSearchParams):
        print(f"🔍 Заполняю форму: {params.country} из {params.departure}")
        
        # 1. Выбор страны
        country_value = params.country.value if isinstance(params.country, Country) else params.country
        country_selector = self.country_selectors.get(country_value, f"text={country_value}")
        
        try:
            await self.page.click('.TVCountrySelect')
            await asyncio.sleep(2)
            await self.page.click(country_selector)
            print(f"✅ Страна выбрана: {country_value}")
        except Exception as e:
            print(f"⚠️ Ошибка выбора страны: {e}")
        
        await asyncio.sleep(3)
        
        # 2. ВЫБОР ГОРОДА ВЫЛЕТА (ИСПРАВЛЕНО)
        departure_value = params.departure.value if isinstance(params.departure, Departure) else params.departure
        print(f"🔍 Ищу город вылета: {departure_value}")
        
        # Ищем поле "Город вылета" - оно ниже "Города присутствия"
        departure_field_selectors = [
            '.TVDepartureSelect',
            '.tv-departure-select',
            'div:has-text("Город вылета")',
            'select[name*="departure"]',
            'div[class*="departure"]'
        ]
        
        departure_field_clicked = False
        for selector in departure_field_selectors:
            try:
                departure_field = await self.page.wait_for_selector(selector, timeout=3000)
                if departure_field:
                    await departure_field.click()
                    print(f"✅ Поле вылета открыто: {selector}")
                    departure_field_clicked = True
                    break
            except:
                continue
        
        if not departure_field_clicked:
            print("⚠️ Поле вылета не найдено, пробую JavaScript...")
            # Пробуем найти и кликнуть по элементу с текстом "Город вылета"
            js_find_departure_field = '''
            () => {
                const elements = document.querySelectorAll('*');
                for (let elem of elements) {
                    const text = elem.textContent || '';
                    if (text.includes('Город вылета') && elem.offsetWidth > 0 && elem.offsetHeight > 0) {
                        elem.click();
                        return 'Found and clicked departure field';
                    }
                }
                
                // Ищем селект с атрибутами вылета
                const selects = document.querySelectorAll('select');
                for (let select of selects) {
                    if (select.name && select.name.includes('departure')) {
                        select.click();
                        return 'Found departure select';
                    }
                }
                
                return 'Departure field not found';
            }
            '''
            result = await self.page.evaluate(js_find_departure_field)
            print(f"🔍 JavaScript: {result}")
        
        await asyncio.sleep(2)
        
        # Теперь ищем нужный город в выпадающем списке
        departure_found = False
        
        # Пробуем прямые селекторы
        direct_selectors = [
            f"text={departure_value}",
            f"option:has-text('{departure_value}')",
            f"div:has-text('{departure_value}')",
            f"li:has-text('{departure_value}')"
        ]
        
        for selector in direct_selectors:
            try:
                departure_option = await self.page.wait_for_selector(selector, timeout=2000)
                if departure_option:
                    await departure_option.click()
                    print(f"✅ Город вылета выбран: {departure_value}")
                    departure_found = True
                    break
            except:
                continue
        
        if not departure_found:
            print("⚠️ Город не найден в прямых селекторах, пробую JavaScript...")
            js_find_city = f'''
            () => {{
                const elements = document.querySelectorAll('*');
                for (let elem of elements) {{
                    const text = elem.textContent || '';
                    if (text.includes('{departure_value}') && 
                        elem.offsetWidth > 0 && elem.offsetHeight > 0 &&
                        (elem.tagName === 'OPTION' || elem.tagName === 'DIV' || elem.tagName === 'LI')) {{
                        elem.click();
                        return `Found and clicked ${{departure_value}}`;
                    }}
                }}
                return 'City not found';
            }}
            '''
            result = await self.page.evaluate(js_find_city)
            print(f"🔍 Поиск города: {result}")
        
        await asyncio.sleep(3)
        
        # 3. Даты
        try:
            date_inputs = await self.page.query_selector_all('input[type="date"], input[placeholder*="дата"]')
            if len(date_inputs) >= 1:
                await date_inputs[0].fill(params.date_from)
                print(f"✅ Дата с: {params.date_from}")
            if len(date_inputs) >= 2:
                await date_inputs[1].fill(params.date_to)
                print(f"✅ Дата по: {params.date_to}")
        except Exception as e:
            print(f"⚠️ Ошибка дат: {e}")
        
        await asyncio.sleep(3)
        
        # 4. Ночи
        try:
            night_selects = await self.page.query_selector_all('select[name*="night"], select[name*="duration"]')
            if night_selects:
                await night_selects[0].select_option(str(params.nights_from))
                print(f"✅ Ночи: {params.nights_from}")
        except Exception as e:
            print(f"⚠️ Ошибка ночей: {e}")
        
        await asyncio.sleep(3)
        
        # 5. Туристы
        try:
            adult_selects = await self.page.query_selector_all('select[name*="adult"]')
            if adult_selects:
                await adult_selects[0].select_option(str(params.adults))
                print(f"✅ Взрослые: {params.adults}")
        except Exception as e:
            print(f"⚠️ Ошибка туристов: {e}")
        
        await asyncio.sleep(3)
        
        # 6. Кнопка поиска
        try:
            await self.page.click('.TVSearchButton')
            print("✅ Поиск запущен")
        except Exception as e:
            print(f"⚠️ Ошибка поиска: {e}")
            await self.page.keyboard.press('Enter')
    
    async def _extract_tours(self, params: TourSearchParams) -> List[Tour]:
        js_search = f'''
        () => {{
            const tours = [];
            const tvPanel = document.getElementById('TVResultPanel');
            
            if (tvPanel && tvPanel.children.length > 0) {{
                const hotelCards = tvPanel.querySelectorAll('.TVSHotelResultItem, .TVResultListViewItem');
                
                for (let card of hotelCards) {{
                    const text = card.textContent || '';
                    const hasPrice = /\\d{{1,3}}[\\s\\.]?\\d{{3}}\\s*(?:руб|₽)/i.test(text);
                    const hasHotelName = /^[A-ZА-ЯЁ][\\w\\s\\-\\.]{{3,50}}\\*/.test(text);
                    
                    if (hasPrice && hasHotelName) {{
                        const rect = card.getBoundingClientRect();
                        if (rect.height > 50 && rect.width > 150) {{
                            const tourData = {{
                                text: text.substring(0, 3000),
                                className: card.className,
                                id: card.id
                            }};
                            
                            tourData.hotel = extractHotelName(text);
                            tourData.price = extractPrice(text);
                            tourData.stars = extractStars(text);
                            tourData.resort = extractResort(text);
                            tourData.rating = extractRating(text);
                            tourData.nights = extractNights(text);
                            tourData.date = extractDate(text);
                            tourData.meal = extractMeal(text);
                            tourData.operator = extractOperator(text);
                            
                            if (tourData.hotel !== 'N/A' && tourData.hotel.length > 3) {{
                                tours.push(tourData);
                            }}
                        }}
                    }}
                }}
            }}
            
            function extractHotelName(text) {{
                const lines = text.split('\\n').map(l => l.trim()).filter(l => l);
                for (let line of lines) {{
                    const match = line.match(/^([A-ZА-ЯЁ][\\w\\s\\-\\.]{{3,50}})\\*([A-ZА-ЯЁ][\\w\\s\\-\\.,]{{3,30}}),\\s*([\\d.]+)/);
                    if (match) {{
                        return match[1].trim();
                    }}
                    const starMatch = line.match(/^([A-ZА-ЯЁ][\\w\\s\\-\\.]{{3,50}})\\*/);
                    if (starMatch) {{
                        return starMatch[1].trim();
                    }}
                    if (/^[A-ZА-ЯЁ]/.test(line) && line.length > 5 && line.length < 60 && 
                        !/\\d{{3,}}/.test(line) &&
                        !line.includes('Поделиться') && !line.includes('Найти')) {{
                        return line;
                    }}
                }}
                return 'N/A';
            }}
            
            function extractPrice(text) {{
                const match = text.match(/(\\d{{1,3}}[\\s\\.]?\\d{{3}})\\s*(?:руб|₽)/i);
                return match ? match[1].replace(/[\\s\\.]/g, '') + ' руб' : 'N/A';
            }}
            
            function extractStars(text) {{
                const lines = text.split('\\n').map(l => l.trim()).filter(l => l);
                for (let line of lines) {{
                    const match = line.match(/^([A-ZА-ЯЁ][\\w\\s\\-\\.]{{3,50}})\\*([\\d.]+)/);
                    if (match) {{
                        return match[2] + '★';
                    }}
                }}
                return 'N/A';
            }}
            
            function extractResort(text) {{
                const lines = text.split('\\n').map(l => l.trim()).filter(l => l);
                for (let line of lines) {{
                    const match = line.match(/^([A-ZА-ЯЁ][\\w\\s\\-\\.]{{3,50}})\\*([A-ZА-ЯЁ][\\w\\s\\-\\.,]{{3,30}}),/);
                    if (match) {{
                        return match[2].trim();
                    }}
                }}
                
                const resorts = ['Дубай', 'Абу-Даби', 'Шарджа', 'Рас-аль-Хайма', 'Аджман', 'Умм-аль-Кувейн',
                               'Анталия', 'Белек', 'Кемер', 'Сиде', 'Алания', 'Мармарис', 'Бодрум',
                               'Шарм-эль-Шейх', 'Хургада', 'Дахаб', 'Марса-Алам'];
                for (let resort of resorts) {{
                    if (text.includes(resort)) {{
                        return resort;
                    }}
                }}
                return 'N/A';
            }}
            
            function extractRating(text) {{
                const lines = text.split('\\n').map(l => l.trim()).filter(l => l);
                for (let line of lines) {{
                    const match = line.match(/,\\s*([\\d.]+)$/);
                    if (match) {{
                        return match[1] + '⭐';
                    }}
                }}
                return 'N/A';
            }}
            
            function extractNights(text) {{
                const match = text.match(/(\\d+)\\s*ноч/i);
                return match ? match[1] + ' ночей' : 'N/A';
            }}
            
            function extractDate(text) {{
                const match = text.match(/(\\d{{2}}[\\.\\/\\-]\\d{{2}}[\\.\\/\\-]\\d{{4}})/);
                return match ? match[1] : 'N/A';
            }}
            
            function extractMeal(text) {{
                if (/all\\s*inclusive|ai/i.test(text)) return 'All Inclusive';
                if (/ultra\\s*all\\s*inclusive|uai/i.test(text)) return 'Ultra All Inclusive';
                if (/full\\s*board|fb/i.test(text)) return 'Full Board';
                if (/half\\s*board|hb/i.test(text)) return 'Half Board';
                if (/bed\\s*breakfast|bb/i.test(text)) return 'Bed & Breakfast';
                return 'N/A';
            }}
            
            function extractOperator(text) {{
                if (/anex\\s*tour/i.test(text)) return 'Anex Tour';
                if (/tui/i.test(text)) return 'TUI';
                if (/coral\\s*travel/i.test(text)) return 'Coral Travel';
                if (/biblio[-\\s]?globus/i.test(text)) return 'Biblio-Globus';
                if (/pegas\\s*touristik/i.test(text)) return 'Pegas Touristik';
                return 'N/A';
            }}
            
            return tours;
        }}
        '''
        
        results = await self.page.evaluate(js_search)
        
        tours = []
        for result in results:
            tour = Tour(
                hotel=result['hotel'],
                price=result['price'],
                nights=result['nights'],
                date=result['date'],
                date_to='N/A',
                meal=result['meal'],
                operator=result['operator'],
                resort=result['resort'],
                stars=result['stars'],
                rating=result['rating'],
                country=params.country.value if isinstance(params.country, Country) else params.country
            )
            tours.append(tour)
        
        return tours
    
    def print_tours(self, tours: List[Tour], title: str = "НАЙДЕННЫЕ ТУРЫ"):
        if not tours:
            print("❌ Туры не найдены")
            return
        
        print(f"\n🎉 {title}: {len(tours)}")
        print("="*80)
        
        for i, tour in enumerate(tours[:15], 1):
            print(f"\n📍 Тур #{i}")
            print(f"🏨 {tour.hotel}")
            if tour.stars != 'N/A':
                print(f"⭐ {tour.stars}")
            if tour.resort != 'N/A':
                print(f"🏖️ {tour.resort}")
            if tour.rating != 'N/A':
                print(f"📊 Рейтинг: {tour.rating}")
            if tour.price != 'N/A':
                print(f"💰 Цена: {tour.price}")
            if tour.nights != 'N/A':
                print(f"🌙 Ночей: {tour.nights}")
            if tour.date != 'N/A':
                print(f"📅 Дата: {tour.date}")
            if tour.meal != 'N/A':
                print(f"🍽️ Питание: {tour.meal}")
            print("-" * 50)

# Тестовые функции
async def test_departure_cities():
    """Тест разных городов вылета"""
    cities_to_test = [
        (Departure.MOSCOW, "Москва"),
        (Departure.ALMATY, "Алматы"),
        (Departure.MINSK, "Минск"),
        (Departure.KAZAN, "Казань")
    ]
    
    for departure_enum, departure_name in cities_to_test:
        print(f"\n🔍 Тестирование города вылета: {departure_name}")
        
        params = TourSearchParams(
            country=Country.TURKEY,
            departure=departure_enum,
            date_from="01.06.2026",
            date_to="30.06.2026",
            nights_from=7,
            nights_to=7,
            adults=2,
            price_max=100000
        )
        
        async with FixedTourvisorAPI() as api:
            tours = await api.search_tours(params)
            api.print_tours(tours, f"ТУРЫ ИЗ {departure_name.upper()}")
            
            if tours:
                min_price = min([int(re.sub(r'\D', '', t.price)) for t in tours if t.price != 'N/A'])
                print(f"📊 {departure_name}: {len(tours)} туров, от {min_price:,} руб")
            else:
                print(f"❌ {departure_name}: туров не найдено")
        
        await asyncio.sleep(5)  # Пауза между тестами

if __name__ == "__main__":
    asyncio.run(test_departure_cities())
