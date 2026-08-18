"""
graph.py - LangGraph StateGraph for Solar Site Evaluation

Architecture:
  START -> geocode -> country_info -> solar_data -> terrain -> pv_yield -> report -> END

Each node calls its respective tool directly (no LLM-driven tool selection).
The final 'report' node sends ALL collected data to the LLM in a single
HumanMessage to generate a comprehensive evaluation report.
This avoids ToolMessage/FunctionMessage schemas that custom proxies may not support.
"""

import os
import json
import operator
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI

from tools import (
    geocode_location,
    get_country_info,
    get_solar_data,
    get_terrain_info,
    calculate_pv_yield,
)


# ──────────────────────────────────────────────
# 1. State Schema
# ──────────────────────────────────────────────
class SolarEvaluationState(TypedDict):
    messages: Annotated[list[BaseMessage], operator.add]
    location_query: str
    coordinates: dict          # {'lat': float, 'lon': float, 'country_code': str, 'display_name': str}
    country_info: dict         # {'region': str, 'subregion': str, 'area_km2': float, ...}
    climate_metrics: dict      # {'avg_daily_ghi_kwh': float, 'peak_sun_hours': float, ...}
    terrain_summary: str
    pv_yield: dict             # {'daily_energy_yield_kwh': float, 'annual_energy_yield_mwh': float, ...}
    plant_capacity_mw: float


# ──────────────────────────────────────────────
# 2. Pipeline Nodes  (each calls one tool)
# ──────────────────────────────────────────────

def geocode_node(state: SolarEvaluationState):
    """Node 1: Geocode the user's location query."""
    query = state["location_query"]
    print(f"  [Step 1/6] Geocoding location: '{query}' ...")
    result = geocode_location.invoke({"query": query})
    print(f"             [OK] Found: {result.get('display_name', 'N/A')}")
    return {
        "coordinates": result,
        "messages": [HumanMessage(content=f"Geocode result: {json.dumps(result)}")]
    }


def country_info_node(state: SolarEvaluationState):
    """Node 2: Fetch country demographics using the country code from geocoding."""
    cc = state.get("coordinates", {}).get("country_code", "")
    if not cc:
        print("  [Step 2/6] Skipping country info (no country code found)")
        return {"country_info": {}}

    print(f"  [Step 2/6] Fetching country info for '{cc.upper()}' ...")
    result = get_country_info.invoke({"country_code": cc})
    print(f"             [OK] Region: {result.get('region')}, Subregion: {result.get('subregion')}")
    return {
        "country_info": result,
        "messages": [HumanMessage(content=f"Country info: {json.dumps(result)}")]
    }


def solar_data_node(state: SolarEvaluationState):
    """Node 3: Fetch 7-day solar radiation forecast from Open-Meteo."""
    coords = state.get("coordinates", {})
    lat = coords.get("lat", 0)
    lon = coords.get("lon", 0)

    print(f"  [Step 3/6] Fetching solar data for ({lat}, {lon}) ...")
    result = get_solar_data.invoke({"lat": lat, "lon": lon})
    print(f"             [OK] Avg Daily GHI: {result.get('avg_daily_ghi_kwh')} kWh/m2  |  PSH: {result.get('peak_sun_hours')} h")
    return {
        "climate_metrics": result,
        "messages": [HumanMessage(content=f"Solar data: {json.dumps(result)}")]
    }


def terrain_node(state: SolarEvaluationState):
    """Node 4: Fetch terrain and regional info from Wikipedia."""
    query = state["location_query"]
    print(f"  [Step 4/6] Searching Wikipedia for terrain info on '{query}' ...")
    result = get_terrain_info.invoke({"location": query})
    summary = result.get("wikipedia_summaries", "")[:500]
    print(f"             [OK] Retrieved {len(summary)} chars of terrain context")
    return {
        "terrain_summary": summary,
        "messages": [HumanMessage(content=f"Terrain info: {summary}")]
    }


def pv_yield_node(state: SolarEvaluationState):
    """Node 5: Calculate PV energy yield using the formula E = A x r x H x PR."""
    capacity = state.get("plant_capacity_mw", 50.0)
    avg_rad = state.get("climate_metrics", {}).get("avg_daily_ghi_kwh", 0)

    print(f"  [Step 5/6] Calculating PV yield for {capacity} MW plant ...")
    result = calculate_pv_yield.invoke({
        "plant_capacity_mw": capacity,
        "avg_daily_radiation_kwh": avg_rad,
    })
    print(f"             [OK] Daily: {result.get('daily_energy_yield_kwh')} kWh  |  Annual: {result.get('annual_energy_yield_mwh')} MWh")
    return {
        "pv_yield": result,
        "messages": [HumanMessage(content=f"PV yield: {json.dumps(result)}")]
    }


def report_node(state: SolarEvaluationState):
    """
    Node 6 (Final): Send ALL collected data to the LLM in a single
    standard chat message and ask it to write the evaluation report.
    No ToolMessages are used - just a plain HumanMessage with the data.
    """
    print("  [Step 6/6] Generating AI evaluation report ...")

    # Assemble all data into one prompt
    data_blob = {
        "location_query": state["location_query"],
        "coordinates": state.get("coordinates", {}),
        "country_info": state.get("country_info", {}),
        "climate_metrics": state.get("climate_metrics", {}),
        "terrain_summary": state.get("terrain_summary", ""),
        "plant_capacity_mw": state.get("plant_capacity_mw"),
        "pv_yield": state.get("pv_yield", {}),
    }

    system_prompt = (
        "You are an expert Solar Energy Consultant. "
        "You have been given real data collected from public APIs about a candidate location "
        "for a solar power plant. Write a comprehensive, well-structured feasibility evaluation "
        "report based ONLY on the provided data. Include sections for: "
        "Location Overview, Regional Demographics, Solar Resource Assessment, "
        "Terrain & Infrastructure, PV Yield Estimate, and a Final Recommendation. "
        "Use the actual numbers from the data - do not make up values."
    )

    user_prompt = (
        f"Here is all the collected data for the solar site evaluation:\n\n"
        f"```json\n{json.dumps(data_blob, indent=2)}\n```\n\n"
        f"Please write the full evaluation report."
    )

    llm = ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        temperature=0.3,
        base_url=os.getenv("OPENAI_BASE_URL"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])

    print("             [OK] Report generated!")
    return {"messages": [response]}


# ----------------------------------------------
# 3. Build the StateGraph
# ----------------------------------------------
workflow = StateGraph(SolarEvaluationState)

# Add nodes
workflow.add_node("geocode", geocode_node)
workflow.add_node("country_info", country_info_node)
workflow.add_node("solar_data", solar_data_node)
workflow.add_node("terrain", terrain_node)
workflow.add_node("pv_yield", pv_yield_node)
workflow.add_node("report", report_node)

# Sequential edges:  START -> geocode -> country_info -> solar_data -> terrain -> pv_yield -> report -> END
workflow.add_edge(START, "geocode")
workflow.add_edge("geocode", "country_info")
workflow.add_edge("country_info", "solar_data")
workflow.add_edge("solar_data", "terrain")
workflow.add_edge("terrain", "pv_yield")
workflow.add_edge("pv_yield", "report")
workflow.add_edge("report", END)

graph = workflow.compile()
