import os
import json
import datetime
from typing import TypedDict, Annotated, List, Dict, Any
import operator

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI

from tools import (
    get_latest_earthquake,
    reverse_geocode,
    get_country_demographics,
    get_weather_hazards,
    get_crypto_volatility,
    get_currency_stress,
    get_hacker_news_alerts,
    get_orbital_activity,
    get_historical_context,
    get_holiday_status,
    get_pokemon_data
)

# 1. Define State
class OmniCrisisState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    target_event: Dict[str, Any]       # Seismic & geo coords
    geo_intel: Dict[str, Any]          # Country, pop, holiday status
    weather_intel: Dict[str, Any]      # Meteorological compounding risks
    macro_cyber_intel: Dict[str, Any]  # Market drops, FX rates, HN alerts
    historical_context: Dict[str, Any] # Wikipedia summary
    defcon_level: int                  # 1 (Critical) to 5 (Normal)
    threat_summary: str                # Strategic synthesized report
    recommended_pokemon: str           # Pokemon name from LLM
    tactical_pokemon: Dict[str, Any]   # Full deployed pokemon data

# 2. Nodes
def gather_intel_node(state: OmniCrisisState):
    """
    Node 1: Sequentially gathers data from 10 APIs.
    """
    print("[O.M.N.I.] Scanning for global seismic anomalies...")
    eq_data = get_latest_earthquake.invoke({})
    
    lat = eq_data.get("latitude")
    lon = eq_data.get("longitude")
    place = eq_data.get("place", "Unknown")
    
    geo_data = {}
    demographics = {}
    holidays = {}
    weather = {}
    historical = {}
    
    if lat is not None and lon is not None:
        print(f"[O.M.N.I.] Anomaly detected at {lat}, {lon}. Running geo-recon...")
        geo_data = reverse_geocode.invoke({"lat": lat, "lon": lon})
        
        print("[O.M.N.I.] Assessing atmospheric hazards...")
        weather = get_weather_hazards.invoke({"lat": lat, "lon": lon})
        
        country_code = geo_data.get("country_code")
        if country_code:
            print(f"[O.M.N.I.] Fetching demographics for {country_code}...")
            demographics = get_country_demographics.invoke({"country_code": country_code})
            
            print(f"[O.M.N.I.] Checking emergency holiday schedules...")
            holidays = get_holiday_status.invoke({"year": datetime.date.today().year, "country_code": country_code})
            
        print(f"[O.M.N.I.] Retrieving historical context for '{place}'...")
        historical = get_historical_context.invoke({"location": place})
        
    print("[O.M.N.I.] Scanning macro-financial and cyber networks...")
    crypto = get_crypto_volatility.invoke({})
    currency = get_currency_stress.invoke({"currency": "EUR"}) # checking EUR vs USD as a proxy
    cyber = get_hacker_news_alerts.invoke({})
    orbit = get_orbital_activity.invoke({})
    
    return {
        "target_event": eq_data,
        "geo_intel": {
            "location": geo_data,
            "demographics": demographics,
            "holidays": holidays
        },
        "weather_intel": weather,
        "macro_cyber_intel": {
            "crypto": crypto,
            "currency_stress": currency,
            "cyber_alerts": cyber,
            "orbital_activity": orbit
        },
        "historical_context": historical
    }

def threat_synthesis_node(state: OmniCrisisState):
    """
    Node 2: Passes all data to LLM to synthesize a DEFCON rating and tactical strategy.
    """
    print("[O.M.N.I.] Synthesizing unified threat assessment...")
    
    # Bundle state
    data_blob = {
        "seismic_event": state.get("target_event"),
        "geo_intel": state.get("geo_intel"),
        "weather": state.get("weather_intel"),
        "macro_cyber": state.get("macro_cyber_intel"),
        "history": state.get("historical_context")
    }
    
    system_prompt = (
        "You are O.M.N.I., an Omni-Intelligence Global Crisis Command Center. "
        "Analyze the provided global intel (seismic, weather, cyber, financial). "
        "You MUST output a JSON response containing EXACTLY three keys:\n"
        '1. "defcon_level": an integer from 1 (Critical) to 5 (Normal).\n'
        '2. "threat_summary": A detailed, sci-fi strategic synthesis report of the overlapping crises.\n'
        '3. "tactical_pokemon": The name (string, e.g., "charizard", "mewtwo", "blastoise") of the ONE Pokemon best suited to mitigate this crisis.\n\n'
        "DO NOT output markdown formatting outside the JSON block. Output ONLY valid JSON."
    )
    
    user_prompt = f"Global Intel Payload:\n\n{json.dumps(data_blob, indent=2)}\n\nGenerate your JSON response."
    
    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.4,
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ])
    
    # Parse JSON
    try:
        content = response.content.strip()
        # strip markdown block if present
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        
        result = json.loads(content.strip())
        defcon = result.get("defcon_level", 5)
        summary = result.get("threat_summary", "Synthesis failed.")
        pokemon = result.get("tactical_pokemon", "pikachu").lower()
    except Exception as e:
        print(f"[ERROR] Failed to parse LLM JSON: {e}")
        defcon = 5
        summary = response.content
        pokemon = "ditto" # Fallback
        
    return {
        "defcon_level": defcon,
        "threat_summary": summary,
        "recommended_pokemon": pokemon
    }

def pokemon_deployment_node(state: OmniCrisisState):
    """
    Node 3: Fetches the tactical Pokemon unit data.
    """
    pokemon = state.get("recommended_pokemon", "pikachu")
    print(f"[O.M.N.I.] Deploying Tactical Intervention Unit: {pokemon.upper()}...")
    
    poke_data = get_pokemon_data.invoke({"pokemon_name": pokemon})
    if "error" in poke_data:
        # Fallback if LLM hallucinated a name
        print(f"           Fallback required. {pokemon} invalid.")
        poke_data = get_pokemon_data.invoke({"pokemon_name": "arceus"})
        
    return {"tactical_pokemon": poke_data}


# 3. Build Graph
workflow = StateGraph(OmniCrisisState)

workflow.add_node("gather_intel", gather_intel_node)
workflow.add_node("threat_synthesis", threat_synthesis_node)
workflow.add_node("pokemon_deployment", pokemon_deployment_node)

workflow.add_edge(START, "gather_intel")
workflow.add_edge("gather_intel", "threat_synthesis")
workflow.add_edge("threat_synthesis", "pokemon_deployment")
workflow.add_edge("pokemon_deployment", END)

graph = workflow.compile()
