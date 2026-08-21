import requests
import datetime
from langchain_core.tools import tool

# 1. Seismic Threat Sensor
@tool
def get_latest_earthquake() -> dict:
    """
    Detects the latest earthquake with magnitude >= 4.5.
    Returns magnitude, coordinates, and timestamp.
    """
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Filter for magnitude >= 4.5
        features = data.get("features", [])
        significant = [f for f in features if f.get("properties", {}).get("mag", 0) >= 4.5]
        
        if not significant:
            # Fallback to the largest earthquake if none are >= 4.5
            significant = sorted(features, key=lambda x: x.get("properties", {}).get("mag", 0), reverse=True)
            
        if not significant:
            return {"error": "No earthquake data found today."}
            
        latest = significant[0]
        props = latest.get("properties", {})
        coords = latest.get("geometry", {}).get("coordinates", [])
        
        return {
            "title": props.get("title"),
            "magnitude": props.get("mag"),
            "place": props.get("place"),
            "time": props.get("time"),
            "url": props.get("url"),
            "longitude": coords[0] if len(coords) > 0 else None,
            "latitude": coords[1] if len(coords) > 1 else None,
            "depth": coords[2] if len(coords) > 2 else None,
        }
    except Exception as e:
        return {"error": str(e)}

# 2. Geographical Recon
@tool
def reverse_geocode(lat: float, lon: float) -> dict:
    """
    Reverse-geocodes coordinates into country, state, city, and nearest urban zones.
    """
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    headers = {"User-Agent": "OmniCrisisCenter/1.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        address = data.get("address", {})
        return {
            "display_name": data.get("display_name"),
            "country": address.get("country"),
            "country_code": address.get("country_code"),
            "state": address.get("state"),
            "city": address.get("city") or address.get("town") or address.get("village"),
        }
    except Exception as e:
        return {"error": str(e)}

# 3. Demographics & Geopolitics
@tool
def get_country_demographics(country_code: str) -> dict:
    """
    Pulls country demographics. Uses World Bank API as REST Countries v3.1 is deprecated.
    """
    if not country_code:
        return {"error": "No country code provided"}
    
    url = f"https://api.worldbank.org/v2/country/{country_code.upper()}?format=json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        raw = response.json()
        if not isinstance(raw, list) or len(raw) < 2 or not raw[1]:
            return {"error": "No data found for this country code"}
            
        data = raw[1][0]
        return {
            "name": data.get("name"),
            "region": data.get("region", {}).get("value"),
            "income_level": data.get("incomeLevel", {}).get("value"),
            "capital": data.get("capitalCity"),
        }
    except Exception as e:
        return {"error": str(e)}

# 4. Atmospheric Threat Radar
@tool
def get_weather_hazards(lat: float, lon: float) -> dict:
    """
    Assesses whether the disaster zone is undergoing compound hazards using Open-Meteo API.
    """
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&hourly=windspeed_10m,precipitation,cloudcover"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        current = data.get("current_weather", {})
        return {
            "temperature_c": current.get("temperature"),
            "windspeed_kmh": current.get("windspeed"),
            "winddirection": current.get("winddirection"),
            "weathercode": current.get("weathercode"),
            "is_day": current.get("is_day"),
        }
    except Exception as e:
        return {"error": str(e)}

# 5. Financial Contagion Monitor
@tool
def get_crypto_volatility() -> dict:
    """
    Tracks crypto market volatility and 24-hour crash signals using CoinGecko API.
    """
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd&include_24hr_change=true"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        return {"error": str(e)}

# 6. Currency Stress Sensor
@tool
def get_currency_stress(currency: str = "EUR") -> dict:
    """
    Evaluates local currency devaluation against USD using Frankfurter API.
    """
    if not currency:
        currency = "EUR" # Default
    url = f"https://api.frankfurter.app/latest?from={currency}&to=USD"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return data
    except Exception as e:
        return {"error": str(e)}

# 7. Cyber & Public Sentiment Scanner
@tool
def get_hacker_news_alerts() -> dict:
    """
    Scans top 15 trending stories for keywords like 'outage', 'cyberattack', 'collapse', 'hack', or 'emergency'.
    """
    try:
        # Get top stories
        top_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        response = requests.get(top_url, timeout=10)
        response.raise_for_status()
        story_ids = response.json()[:15]
        
        keywords = ["outage", "cyberattack", "collapse", "hack", "emergency", "breach", "fail"]
        alerts = []
        
        for sid in story_ids:
            story_url = f"https://hacker-news.firebaseio.com/v0/item/{sid}.json"
            story_resp = requests.get(story_url, timeout=5)
            if story_resp.status_code == 200:
                story = story_resp.json()
                if story and story.get("title"):
                    title = story.get("title").lower()
                    if any(kw in title for kw in keywords):
                        alerts.append(story.get("title"))
                        
        return {"alerts": alerts, "top_stories_scanned": 15, "threats_found": len(alerts)}
    except Exception as e:
        return {"error": str(e)}

# 8. Orbital Asset Tracker
@tool
def get_orbital_activity() -> dict:
    """
    Fetches recent launch payload, mission details, and orbit state via SpaceX API.
    """
    url = "https://api.spacexdata.com/v4/launches/latest"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {
            "mission_name": data.get("name"),
            "date_utc": data.get("date_utc"),
            "success": data.get("success"),
            "details": data.get("details"),
        }
    except Exception as e:
        return {"error": str(e)}

# 9. Historical Threat Archivist
@tool
def get_historical_context(location: str) -> dict:
    """
    Fetches historical natural disaster vulnerability context from Wikipedia.
    """
    if not location:
        return {"error": "No location provided"}
    
    query = f"{location} disaster history"
    url = f"https://en.wikipedia.org/w/rest.php/v1/search/page?q={query}&limit=2"
    headers = {"User-Agent": "OmniCrisisCenter/1.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        pages = data.get("pages", [])
        summaries = []
        for p in pages:
            summaries.append({
                "title": p.get("title"),
                "excerpt": p.get("excerpt")
            })
        return {"historical_summaries": summaries}
    except Exception as e:
        return {"error": str(e)}

# 10. Emergency Response Calendar
@tool
def get_holiday_status(year: int, country_code: str) -> dict:
    """
    Checks if local emergency services are operating under holiday schedules via Nager.Date.
    """
    if not country_code:
        return {"error": "No country code provided"}
        
    url = f"https://date.nager.at/api/v3/PublicHolidays/{year}/{country_code.upper()}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 404:
            return {"status": "No holiday data available for this country."}
        response.raise_for_status()
        data = response.json()
        
        # Check if today is a holiday
        today = datetime.date.today().isoformat()
        today_holidays = [h for h in data if h.get("date") == today]
        
        return {
            "is_holiday_today": len(today_holidays) > 0,
            "holidays_today": [h.get("name") for h in today_holidays]
        }
    except Exception as e:
        return {"error": str(e)}

# 11. Tactical Pokémon Deployment Unit
@tool
def get_pokemon_data(pokemon_name: str) -> dict:
    """
    Dynamically evaluates Pokémon stats, abilities, typings, and extracts sprite artwork.
    """
    if not pokemon_name:
        return {"error": "No Pokemon name provided"}
        
    url = f"https://pokeapi.co/api/v2/pokemon/{pokemon_name.lower()}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 404:
            return {"error": f"Pokemon '{pokemon_name}' not found."}
        response.raise_for_status()
        data = response.json()
        
        stats = {s.get("stat", {}).get("name"): s.get("base_stat") for s in data.get("stats", [])}
        types = [t.get("type", {}).get("name") for t in data.get("types", [])]
        abilities = [a.get("ability", {}).get("name") for a in data.get("abilities", [])]
        sprite = data.get("sprites", {}).get("front_default")
        
        return {
            "name": data.get("name"),
            "types": types,
            "stats": stats,
            "abilities": abilities,
            "sprite_url": sprite
        }
    except Exception as e:
        return {"error": str(e)}
