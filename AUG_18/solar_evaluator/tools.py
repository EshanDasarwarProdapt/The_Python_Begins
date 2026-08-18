import requests
from langchain_core.tools import tool

@tool
def geocode_location(query: str) -> dict:
    """
    Geocodes a location query using the Nominatim OpenStreetMap API.
    Returns the latitude, longitude, display name, and country code.
    
    Args:
        query (str): The name of the city, region, or address.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": query,
        "format": "json",
        "limit": 1
    }
    headers = {
        "User-Agent": "SolarSiteEvaluatorApp/1.0"
    }
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    data = response.json()
    
    if not data:
        return {"error": "Location not found"}
        
    result = data[0]
    # We might need to make another request or reverse geocode to guarantee country code,
    # but the API supports adding 'addressdetails=1' to get country_code. Let's do that.
    params["addressdetails"] = 1
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    result = data[0]
    
    return {
        "lat": float(result["lat"]),
        "lon": float(result["lon"]),
        "display_name": result.get("display_name"),
        "country_code": result.get("address", {}).get("country_code", "")
    }

@tool
def get_country_info(country_code: str) -> dict:
    """
    Retrieves country demographics and regional information using the World Bank API.
    This is a free, keyless public API.
    
    Args:
        country_code (str): The 2-letter country code (e.g., 'us', 'in', 'ar').
    """
    if not country_code:
        return {"error": "Invalid country code provided"}
        
    url = f"https://api.worldbank.org/v2/country/{country_code.upper()}"
    params = {"format": "json"}
    response = requests.get(url, params=params)
    
    if response.status_code != 200:
        return {"error": f"API error: {response.status_code}"}
    
    raw = response.json()
    # World Bank returns: [ {pagination}, [ {country_data} ] ]
    if not isinstance(raw, list) or len(raw) < 2 or not raw[1]:
        return {"error": "No data found for this country code"}
    
    data = raw[1][0]
    return {
        "name": data.get("name"),
        "region": data.get("region", {}).get("value"),
        "subregion": data.get("adminregion", {}).get("value"),
        "income_level": data.get("incomeLevel", {}).get("value"),
        "capital": data.get("capitalCity"),
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
    }

@tool
def get_solar_data(lat: float, lon: float) -> dict:
    """
    Retrieves solar climatology and radiation data from the Open-Meteo API.
    Calculates average daily radiation (kWh/m²) and Peak Sun Hours (PSH).
    
    Args:
        lat (float): Latitude
        lon (float): Longitude
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "direct_normal_irradiance,shortwave_radiation,cloudcover,temperature_2m",
        "daily": "sunshine_duration,shortwave_radiation_sum",
        "timezone": "auto",
        "forecast_days": 7
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return {"error": f"API error: {response.status_code}"}
        
    data = response.json()
    daily = data.get("daily", {})
    
    # shortwave_radiation_sum is in MJ/m² by default for Open-Meteo
    # 1 MJ = 0.277778 kWh
    if "shortwave_radiation_sum" in daily:
        daily_radiation_mj = daily["shortwave_radiation_sum"]
        # filter out None values
        valid_rad = [r for r in daily_radiation_mj if r is not None]
        if valid_rad:
            avg_daily_mj = sum(valid_rad) / len(valid_rad)
            avg_daily_kwh = avg_daily_mj * 0.277778
            # Peak Sun Hours roughly equals average daily GHI in kWh/m²
            peak_sun_hours = avg_daily_kwh
        else:
            avg_daily_kwh = 0
            peak_sun_hours = 0
    else:
        avg_daily_kwh = 0
        peak_sun_hours = 0

    return {
        "avg_daily_ghi_kwh": round(avg_daily_kwh, 2),
        "peak_sun_hours": round(peak_sun_hours, 2),
        "cloudcover_avg_pct": sum(data["hourly"].get("cloudcover", [0])) / max(len(data["hourly"].get("cloudcover", [1])), 1),
        "avg_temperature_c": sum(data["hourly"].get("temperature_2m", [0])) / max(len(data["hourly"].get("temperature_2m", [1])), 1)
    }

@tool
def get_terrain_info(location: str) -> dict:
    """
    Retrieves regional, topographical, and terrain knowledge from Wikipedia.
    
    Args:
        location (str): The name of the region or city.
    """
    url = f"https://en.wikipedia.org/w/rest.php/v1/search/page"
    params = {
        "q": location,
        "limit": 3
    }
    headers = {
        "User-Agent": "SolarSiteEvaluatorApp/1.0"
    }
    response = requests.get(url, params=params, headers=headers)
    if response.status_code != 200:
        return {"error": f"API error: {response.status_code}"}
        
    data = response.json()
    summaries = []
    for page in data.get("pages", []):
        summaries.append(f"Title: {page.get('title')}\nSummary: {page.get('description', '')}\nExcerpt: {page.get('excerpt', '')}")
        
    return {
        "wikipedia_summaries": "\n---\n".join(summaries)
    }

@tool
def calculate_pv_yield(plant_capacity_mw: float, avg_daily_radiation_kwh: float) -> dict:
    """
    Evaluates the PV yield formula E = A * r * H * PR.
    
    Args:
        plant_capacity_mw (float): The desired plant capacity in Megawatts (MW).
        avg_daily_radiation_kwh (float): Average daily solar radiation on tilted panels (kWh/m²).
    """
    # Assumptions
    r = 0.20 # Solar panel efficiency (20%)
    pr = 0.75 # Performance ratio
    
    # Calculate Area A:
    # A standard 1 MW plant requires approx 5000 m² of panels at 20% efficiency.
    # Because Capacity = A * r * 1000 W/m² (Standard Test Condition Irradiance)
    # So 1,000,000 W = A * 0.20 * 1000 W/m² => A = 1,000,000 / 200 = 5000 m²
    a_m2 = (plant_capacity_mw * 1_000_000) / (r * 1000)
    
    # E = A * r * H * PR
    # E is Energy output per day in kWh
    h = avg_daily_radiation_kwh
    
    daily_energy_kwh = a_m2 * r * h * pr
    annual_energy_kwh = daily_energy_kwh * 365
    
    return {
        "estimated_panel_area_m2": round(a_m2, 2),
        "panel_efficiency": r,
        "performance_ratio": pr,
        "daily_energy_yield_kwh": round(daily_energy_kwh, 2),
        "annual_energy_yield_mwh": round(annual_energy_kwh / 1000, 2)
    }
