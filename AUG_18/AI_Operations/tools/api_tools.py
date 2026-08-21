import requests
import datetime
from langchain_core.tools import tool

def _get_lat_lon(city: str) -> tuple[float, float, str]:
    """Helper to geocode city names into coordinates via Open-Meteo Geocoding API."""
    url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
    resp = requests.get(url, timeout=10)
    data = resp.json()
    if not data.get("results"):
        raise ValueError(f"Could not resolve coordinates for '{city}'.")
    res = data["results"][0]
    return (res["latitude"], res["longitude"], f"{res.get('name')}, {res.get('country')}")

@tool
def get_weather(city: str) -> str:
    """Fetch current real-time weather metrics for a city."""
    try:
        lat, lon, location = _get_lat_lon(city)
        url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            f"&current=temperature_2m,wind_speed_10m,precipitation"
            f"&daily=temperature_2m_max,temperature_2m_min"
            f"&timezone=auto"
        )
        resp = requests.get(url, timeout=10)
        data = resp.json()
        cur = data.get("current", {})
        daily = data.get("daily", {})
        
        return (
            f"--- Weather for {location} ---\n"
            f"Temperature: {cur.get('temperature_2m')}°C\n"
            f"Precipitation: {cur.get('precipitation')} mm\n"
            f"Wind Speed: {cur.get('wind_speed_10m')} km/h\n"
            f"Daily High/Low: {daily.get('temperature_2m_max', [None])[0]}°C / {daily.get('temperature_2m_min', [None])[0]}°C"
        )
    except Exception as e:
        return f"Error fetching weather: {e}"

@tool
def search_products(query: str) -> str:
    """Search for products to check SKU pricing, stock levels, and ratings."""
    url = f"https://dummyjson.com/products/search?q={query}"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        products = data.get("products", [])
        if not products:
            return f"No products found for query '{query}'."
        
        output = [f"--- Product Search Results for '{query}' ---"]
        for p in products[:5]:
            output.append(
                f"- [{p.get('sku', 'N/A')}] {p.get('title')} | Brand: {p.get('brand', 'N/A')} | "
                f"Price: ${p.get('price')} | Stock: {p.get('stock')} | Rating: {p.get('rating')}"
            )
        return "\n".join(output)
    except Exception as e:
        return f"Error searching products: {e}"

@tool
def get_country_and_holidays(country_code: str, year: int) -> str:
    """Get country capital, region, and upcoming public holidays."""
    try:
        # 1. World Bank Demographics
        wb_url = f"https://api.worldbank.org/v2/country/{country_code}?format=json"
        wb_resp = requests.get(wb_url, timeout=10)
        raw = wb_resp.json()
        country_info = ""
        if isinstance(raw, list) and len(raw) > 1 and raw[1]:
            data = raw[1][0]
            country_info = (
                f"Country: {data.get('name')}\n"
                f"Capital: {data.get('capitalCity')}\n"
                f"Region: {data.get('region', {}).get('value')}\n"
                f"Income Level: {data.get('incomeLevel', {}).get('value')}\n"
            )
        else:
            country_info = f"Country demographics not found for {country_code}.\n"

        # 2. Nager.Date Holidays
        nd_url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code}"
        nd_resp = requests.get(nd_url, timeout=10)
        holiday_info = ""
        if nd_resp.status_code == 200:
            holidays = nd_resp.json()
            today = datetime.date.today().isoformat()
            upcoming = [h for h in holidays if h.get("date") >= today][:5]
            if upcoming:
                holiday_info = "Upcoming Holidays:\n" + "\n".join([f"- {h['date']}: {h['name']}" for h in upcoming])
            else:
                holiday_info = "No upcoming holidays this year."
        else:
            holiday_info = f"Holiday data not available (Status {nd_resp.status_code})."
            
        return f"--- Demographics & Holidays for {country_code} ({year}) ---\n{country_info}\n{holiday_info}"
    except Exception as e:
        return f"Error fetching country/holidays: {e}"

@tool
def get_fx_and_crypto(currency_from: str, currency_to: str, crypto_id: str) -> str:
    """Get live FX exchange rates and cryptocurrency market values."""
    try:
        output = []
        # 1. FX
        if currency_from and currency_to:
            fx_url = f"https://open.er-api.com/v6/latest/{currency_from.upper()}"
            fx_resp = requests.get(fx_url, timeout=10)
            if fx_resp.status_code == 200:
                rates = fx_resp.json().get("rates", {})
                rate = rates.get(currency_to.upper())
                if rate:
                    output.append(f"FX Rate: 1 {currency_from.upper()} = {rate} {currency_to.upper()}")
                else:
                    output.append(f"FX Rate: {currency_to.upper()} not found.")
            else:
                output.append(f"FX Error: {fx_resp.status_code}")
                
        # 2. Crypto
        if crypto_id:
            crypto_url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_id.lower()}&vs_currencies=usd"
            crypto_resp = requests.get(crypto_url, timeout=10)
            if crypto_resp.status_code == 200:
                data = crypto_resp.json()
                price = data.get(crypto_id.lower(), {}).get("usd")
                if price:
                    output.append(f"Crypto Rate: 1 {crypto_id.title()} = ${price} USD")
                else:
                    output.append(f"Crypto Rate: {crypto_id} not found.")
            else:
                output.append(f"Crypto Error: {crypto_resp.status_code}")
                
        if not output:
            return "No parameters provided."
            
        return "--- FX & Crypto Rates ---\n" + "\n".join(output)
    except Exception as e:
        return f"Error fetching rates: {e}"

@tool
def get_hn_news(query_keyword: str) -> str:
    """Scan Hacker News for trending tech and supply chain headlines matching a keyword."""
    try:
        top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        response = requests.get(top_url, timeout=10)
        story_ids = response.json()[:20] # Check top 20 to save time
        
        alerts = []
        for sid in story_ids:
            story_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
            story_resp = requests.get(story_url, timeout=5)
            if story_resp.status_code == 200:
                story = story_resp.json()
                if story and story.get("title"):
                    if not query_keyword or query_keyword.lower() in story.get("title").lower():
                        alerts.append(f"- {story.get('title')} ({story.get('url', 'No URL')})")
                        
        if not alerts:
            return f"No trending news found for keyword '{query_keyword}' in the top 20 stories."
            
        return f"--- Hacker News alerts for '{query_keyword}' ---\n" + "\n".join(alerts)
    except Exception as e:
        return f"Error fetching news: {e}"

api_tools = [get_weather, search_products, get_country_and_holidays, get_fx_and_crypto, get_hn_news]
