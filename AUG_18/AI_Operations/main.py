import os
import uuid
import json
from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from agent.graph import workflow

# Compile graph with memory and interrupt
memory = MemorySaver()
app = workflow.compile(
    checkpointer=memory,
    interrupt_before=["hitl_interrupt"]
)

def print_agent_message(msg):
    safe_msg = msg.encode('ascii', 'ignore').decode('ascii')
    print("\n" + "=" * 60)
    print("[Agent Response]:")
    print(safe_msg)
    print("=" * 60 + "\n")

def main():
    print("=" * 60)
    print("  Meridian Retail Group - AI Operations Agent")
    print("=" * 60)
    print("Type your operational request below.")
    print("Type 'exit' or 'quit' to stop.\n")

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    while True:
        try:
            user_input = input("Operator > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("Logging out. Goodbye!")
                break

            print("\n[Processing...]")
            
            # Start streaming
            for event in app.stream({"user_input": user_input, "messages": [HumanMessage(content=user_input)]}, config):
                for k, v in event.items():
                    if k == "synthesizer":
                        msg = v.get("synthesized_report", "")
                        if msg:
                            print_agent_message(msg)

            # Check if interrupted
            state = app.get_state(config)
            if state.next and "hitl_interrupt" in state.next:
                print("\n[WARNING]: The agent is attempting to delete a file.")
                
                planned = state.values.get("planned_tasks", [])
                target_files = [t.get("filename") for t in planned if t.get("action") == "delete_file"]
                
                print(f"Target file(s): {', '.join(target_files)}")
                choice = input("Do you approve this deletion? [y/N]: ").strip().lower()
                
                if choice == 'y':
                    print("\n[Deletion Approved. Resuming...]")
                    # Resume graph
                    for event in app.stream(None, config):
                        for k, v in event.items():
                            if k == "synthesizer":
                                msg = v.get("synthesized_report", "")
                                if msg:
                                    print_agent_message(msg)
                else:
                    print("\n[Deletion Denied. Aborting Deletion...]")
                    # Modify the state to remove the delete_file task
                    safe_tasks = [t for t in planned if t.get("action") != "delete_file"]
                    app.update_state(config, {"planned_tasks": safe_tasks})
                    
                    # Resume graph (it will go to hitl_node then executor)
                    for event in app.stream(None, config):
                        for k, v in event.items():
                            if k == "synthesizer":
                                msg = v.get("synthesized_report", "")
                                if msg:
                                    print_agent_message(msg)

        except KeyboardInterrupt:
            print("\nExiting session.")
            break
        except Exception as e:
            print(f"\n[System Error]: {e}\n")

if __name__ == "__main__":
    main()
