import operator
import os
import sys
from typing import Annotated, List, TypedDict

import requests
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

# =====================================================================
# 1. API Tools Definition (Open-Meteo & Free Geocoding)
# =====================================================================


def _get_lat_lon(city: str) -> tuple[float, float, str]:
  """Helper to geocode city names into coordinates via Open-Meteo Geocoding API."""
  url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
  resp = requests.get(url, timeout=10)
  data = resp.json()
  if not data.get("results"):
    raise ValueError(f"Could not resolve coordinates for '{city}'.")
  res = data["results"][0]
  return (
      res["latitude"],
      res["longitude"],
      f"{res.get('name')}, {res.get('country')}",
  )


@tool
def weather_tool(city: str) -> str:
  """Fetch current real-time weather metrics for a city (temperature, feels-like, rain, wind, humidity)."""
  try:
    lat, lon, location = _get_lat_lon(city)
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,apparent_temperature,precipitation,rain,wind_speed_10m,relative_humidity_2m"
    )
    resp = requests.get(url, timeout=10)
    cur = resp.json().get("current", {})
    return (
        f"--- Current Weather for {location} ---\n"
        f"Temperature: {cur.get('temperature_2m')}°C (Feels like: {cur.get('apparent_temperature')}°C)\n"
        f"Active Rain: {cur.get('rain', 0)} mm\n"
        f"Wind Speed: {cur.get('wind_speed_10m')} km/h\n"
        f"Humidity: {cur.get('relative_humidity_2m')}%"
    )
  except Exception as e:
    return f"Error fetching current weather: {e}"


@tool
def forecast_tool(city: str) -> str:
  """Fetch today's full-day forecast trends (Max/Min temp, max precipitation probability %, total rain mm, UV index)."""
  try:
    lat, lon, location = _get_lat_lon(city)
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,uv_index_max"
        f"&forecast_days=1&timezone=auto"
    )
    resp = requests.get(url, timeout=10)
    daily = resp.json().get("daily", {})

    max_temp = daily.get("temperature_2m_max", [None])[0]
    min_temp = daily.get("temperature_2m_min", [None])[0]
    rain_prob = daily.get("precipitation_probability_max", [0])[0]
    precip_sum = daily.get("precipitation_sum", [0])[0]
    uv_index = daily.get("uv_index_max", [0])[0]

    return (
        f"--- Today's Forecast Trends for {location} ---\n"
        f"Temperature Range: High of {max_temp}°C | Low of {min_temp}°C\n"
        f"Peak Rain Probability: {rain_prob}%\n"
        f"Total Expected Rain: {precip_sum} mm\n"
        f"Max UV Index: {uv_index}"
    )
  except Exception as e:
    return f"Error fetching forecast trends: {e}"


tools = [weather_tool, forecast_tool]

# =====================================================================
# 2. LangGraph Multi-Tool Agent Setup
# =====================================================================


class AgentState(TypedDict):
  messages: Annotated[List[BaseMessage], operator.add]


# Initialize LLM with tool binding (ensure OPENAI_API_KEY is set in environment)
llm = ChatOpenAI(
    model="gpt-4o-mini", 
    temperature=0,
    api_key="pubatch10",
    base_url="https://keygateway1.arshnivlabs.com/v1"
)
llm_with_tools = llm.bind_tools(tools)


def agent_node(state: AgentState) -> dict:
  """Executes the LLM to inspect messages and determine if tools are needed."""
  response = llm_with_tools.invoke(state["messages"])
  return {"messages": [response]}


def route_tools(state: AgentState) -> str:
  """Routes execution to tools node if tool calls exist, otherwise ends."""
  last_message = state["messages"][-1]
  if getattr(last_message, "tool_calls", None):
    return "tools"
  return END


# Build Graph
graph = StateGraph(AgentState)
graph.add_node("advisor", agent_node)
graph.add_node("tools", ToolNode(tools))

graph.set_entry_point("advisor")
graph.add_conditional_edges("advisor", route_tools, {"tools": "tools", END: END})
graph.add_edge("tools", "advisor")

app = graph.compile()

# =====================================================================
# 3. Interactive Terminal Loop
# =====================================================================

SYSTEM_PROMPT = """You are an expert Weather Advisor Agent.
When the user asks about a city:
1. Call both `weather_tool` (for real-time metrics) and `forecast_tool` (for daily probability/trends).
2. Synthesize the findings into clear, structured, and actionable gear and clothing advice:
   - ☔ **Rain Gear / Umbrella**: Advise if current rain > 0 mm OR max rain probability > 30%.
   - 🧥 **Clothing & Layers**: Heavy jacket (<10°C), Light jacket/cardigan (10–18°C), Breathable/standard (19–25°C), Cool/summer wear (>25°C).
   - 🕶️ **Extra Gear**: Sunglasses/sunscreen (UV > 5), Windbreaker (Wind > 25 km/h).
Keep your final output clean, concise, and structured with headings and bullet points.
"""


def main():
  print("=" * 60)
  print("  WEATHER ADVISOR AGENT (LangGraph + Open-Meteo)")
  print("=" * 60)
  print("Type your query below (e.g., 'What should I wear in Tokyo today?')")
  print("Type 'exit' or 'quit' to stop.\n")

  while True:
    try:
      user_query = input("User > ").strip()
      if not user_query:
        continue
      if user_query.lower() in ["exit", "quit", "q"]:
        print("Goodbye!")
        break

      print("\n[Thinking & Fetching Live Weather Data...]")

      # Execute Graph
      result = app.invoke({
          "messages": [
              SystemMessage(content=SYSTEM_PROMPT),
              HumanMessage(content=user_query),
          ]
      })

      final_answer = result["messages"][-1].content
      safe_answer = final_answer.encode('ascii', 'ignore').decode('ascii')
      print("\n" + "-" * 60)
      print(safe_answer)
      print("-" * 60 + "\n")

    except KeyboardInterrupt:
      print("\nExiting session. Goodbye!")
      break
    except Exception as e:
      print(f"\n[Error]: {e}\n")


if __name__ == "__main__":
  main()