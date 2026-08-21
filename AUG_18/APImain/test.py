from graph import graph
import os
from dotenv import load_dotenv

load_dotenv()

print("Testing OmniCrisis Graph Execution...")
state = graph.invoke({})
print("Done!")
print("DEFCON:", state.get("defcon_level"))
print("POKEMON:", state.get("recommended_pokemon"))
print("SUMMARY:", state.get("threat_summary")[:100] + "...")
