import os
import json
import re
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from agent.state import AgentState
from agent.prompts import PLANNER_PROMPT, SYNTHESIZER_PROMPT
from tools.api_tools import get_weather, search_products, get_country_and_holidays, get_fx_and_crypto, get_hn_news
from tools.file_tools import list_files, read_file, write_file, delete_file
from tools.doc_tools import generate_pdf_report, generate_excel_report, generate_word_doc

llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    temperature=0,
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL")
)

def planner_node(state: AgentState):
    """Parses user input into a JSON list of tasks."""
    user_input = state["user_input"]
    print(f"\n[Planner] Analyzing request: '{user_input}'")
    
    response = llm.invoke([
        SystemMessage(content=PLANNER_PROMPT),
        HumanMessage(content=user_input)
    ])
    
    # Parse the JSON array from the response
    tasks = []
    content = response.content
    match = re.search(r'\[.*\]', content, re.DOTALL)
    if match:
        try:
            tasks = json.loads(match.group(0))
        except Exception:
            pass
            
    if not tasks:
        print("[Planner] Failed to parse tasks or no tasks needed.")
        return {"planned_tasks": []}
        
    print(f"[Planner] Tasks generated: {[t.get('action') for t in tasks]}")
    return {"planned_tasks": tasks, "messages": [AIMessage(content=f"Planned tasks: {json.dumps(tasks)}")]}

def route_hitl(state: AgentState):
    """Interrupts execution if a delete_file task is planned."""
    tasks = state.get("planned_tasks", [])
    if any(t.get("action") == "delete_file" for t in tasks):
        return "hitl_interrupt"
    return "executor"

def hitl_node(state: AgentState):
    """Dummy node that serves as the interrupt breakpoint."""
    return {}

def executor_node(state: AgentState):
    """Executes the planned tasks by directly invoking Python functions."""
    tasks = state.get("planned_tasks", [])
    gathered_data = {}
    
    print("\n[Executor] Running tasks...")
    for t in tasks:
        action = t.get("action")
        try:
            if action == "get_weather":
                gathered_data["weather"] = get_weather.invoke({"city": t.get("city", "")})
            elif action == "search_products":
                gathered_data["products"] = search_products.invoke({"query": t.get("query", "")})
            elif action == "get_country_and_holidays":
                gathered_data["country"] = get_country_and_holidays.invoke({"country_code": t.get("country_code", ""), "year": t.get("year", 2024)})
            elif action == "get_fx_and_crypto":
                gathered_data["fx_crypto"] = get_fx_and_crypto.invoke({"currency_from": t.get("currency_from", ""), "currency_to": t.get("currency_to", ""), "crypto_id": t.get("crypto_id", "")})
            elif action == "get_hn_news":
                gathered_data["news"] = get_hn_news.invoke({"query_keyword": t.get("query_keyword", "")})
            elif action == "list_files":
                gathered_data["files"] = list_files.invoke({})
            elif action == "read_file":
                gathered_data[f"file_{t.get('filename')}"] = read_file.invoke({"filename": t.get("filename")})
            elif action == "delete_file":
                gathered_data["delete_result"] = delete_file.invoke({"filename": t.get("filename")})
        except Exception as e:
            gathered_data[action] = f"Error executing {action}: {e}"
            
    print("[Executor] Data gathering complete.")
    return {"gathered_data": gathered_data}

def synthesizer_node(state: AgentState):
    """Writes a cohesive summary using the gathered data."""
    data = state.get("gathered_data", {})
    if not data:
        return {"synthesized_report": "No data gathered.", "messages": [AIMessage(content="No actions were performed.")]}
        
    print("\n[Synthesizer] Writing report...")
    prompt = f"Here is the raw data gathered from the operational tools:\n\n```json\n{json.dumps(data, indent=2)}\n```\n\nPlease write the final structured report."
    
    response = llm.invoke([
        SystemMessage(content=SYNTHESIZER_PROMPT),
        HumanMessage(content=prompt)
    ])
    
    return {"synthesized_report": response.content, "messages": [response]}

def documenter_node(state: AgentState):
    """Generates the requested document using the synthesized report."""
    tasks = state.get("planned_tasks", [])
    report = state.get("synthesized_report", "")
    
    print("\n[Documenter] Checking for document generation tasks...")
    for t in tasks:
        action = t.get("action")
        filename = t.get("filename", "report")
        try:
            if action == "generate_pdf_report":
                print(f"  -> Generating {filename}")
                generate_pdf_report.invoke({"filename": filename, "title": "AI Operations Report", "content": report})
            elif action == "generate_excel_report":
                print(f"  -> Generating {filename}")
                # For deterministic excel, we just split the report into lines for simplicity
                rows = [[line] for line in report.split('\n') if line.strip()]
                generate_excel_report.invoke({"filename": filename, "sheet_title": "Report", "headers": ["Content"], "rows": rows})
            elif action == "generate_word_doc":
                print(f"  -> Generating {filename}")
                generate_word_doc.invoke({"filename": filename, "title": "AI Operations Report", "content": report})
        except Exception as e:
            print(f"  -> Failed to generate {filename}: {e}")
            
    return {}

workflow = StateGraph(AgentState)

workflow.add_node("planner", planner_node)
workflow.add_node("hitl_interrupt", hitl_node)
workflow.add_node("executor", executor_node)
workflow.add_node("synthesizer", synthesizer_node)
workflow.add_node("documenter", documenter_node)

workflow.add_edge(START, "planner")
workflow.add_conditional_edges("planner", route_hitl, {"hitl_interrupt": "hitl_interrupt", "executor": "executor"})
workflow.add_edge("hitl_interrupt", "executor")
workflow.add_edge("executor", "synthesizer")
workflow.add_edge("synthesizer", "documenter")
workflow.add_edge("documenter", END)
