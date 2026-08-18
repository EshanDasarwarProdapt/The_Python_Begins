"""
main.py - Entry point for the Solar Site Evaluator

Usage:
    python main.py

The script prompts for a location and plant capacity, then runs the
LangGraph pipeline and prints the final AI-generated evaluation report.
"""

import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from graph import graph


def main():
    load_dotenv()

    # Validate API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found. Please set it in .env")
        return

    print("=" * 60)
    print("   Autonomous Multi-Agent Solar Site Evaluator")
    print("=" * 60)

    # ── User Input ──
    location = input("\n  Enter candidate location (e.g., 'Mojave Desert, USA'): ").strip()
    if not location:
        location = "Mojave Desert, USA"

    try:
        capacity_str = input("  Enter desired plant capacity in MW (e.g., 50): ").strip()
        capacity = float(capacity_str) if capacity_str else 50.0
    except ValueError:
        print("  Invalid capacity. Defaulting to 50.0 MW")
        capacity = 50.0

    print(f"\n{'-' * 60}")
    print(f"  Evaluating '{location}' for a {capacity} MW Solar Plant")
    print(f"{'-' * 60}\n")

    # ── Initialize State ──
    initial_state = {
        "messages": [HumanMessage(content=f"Evaluate solar feasibility for {location} with {capacity} MW capacity.")],
        "location_query": location,
        "plant_capacity_mw": capacity,
        "coordinates": {},
        "country_info": {},
        "climate_metrics": {},
        "terrain_summary": "",
        "pv_yield": {},
    }

    # ── Run Graph ──
    final_state = graph.invoke(initial_state)

    # ── Print Final Report ──
    print(f"\n{'=' * 60}")
    print("   SOLAR FEASIBILITY EVALUATION REPORT")
    print(f"{'=' * 60}\n")
    print(final_state["messages"][-1].content)

    # ── Print Extracted State ──
    print(f"\n{'-' * 60}")
    print("  EXTRACTED STATE SUMMARY")
    print(f"{'-' * 60}")
    print(f"  Coordinates    : {final_state.get('coordinates', {})}")
    print(f"  Country Info   : {final_state.get('country_info', {})}")
    print(f"  Climate Metrics: {final_state.get('climate_metrics', {})}")
    print(f"  PV Yield       : {final_state.get('pv_yield', {})}")
    print(f"  Terrain Summary: {final_state.get('terrain_summary', '')[:150]}...")
    print(f"{'-' * 60}\n")


if __name__ == "__main__":
    main()
