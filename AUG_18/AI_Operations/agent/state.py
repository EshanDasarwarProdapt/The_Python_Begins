import operator
from typing import Annotated, List, TypedDict, Any
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    user_input: str
    planned_tasks: List[dict]
    gathered_data: dict
    synthesized_report: str
