import json
from typing import Literal

from langgraph.prebuilt import create_react_agent

from backend.models.results import SleepAnalysisResult, ErrorResult
from backend.models.state import State, AgentResponse
from langgraph.types import Command
from langchain_core.messages import HumanMessage, ToolMessage

from backend.tools.sleep_tools import analyze_sleep_changes, analyze_daily_heart_rate


def create_sleep_agent(llm):
    tools = [analyze_sleep_changes, analyze_daily_heart_rate]
    return create_react_agent(llm, tools=tools)


def sleep_node(sleep_agent):
    def _node(state: State) -> Command[Literal["supervisor"]]:
        # Estrai task
        task = None
        for msg in reversed(state["messages"]):
            if hasattr(msg, 'name') and msg.name == "supervisor_instruction":
                task = msg.content.replace("[TASK]: ", "")
                break

        # Invoca agent
        result = sleep_agent.invoke({"messages": [HumanMessage(content=task)]})

        # Estrai dati strutturati
        agent_data = None
        for msg in result["messages"]:
            if isinstance(msg, ToolMessage):
                agent_data = msg.content if isinstance(msg.content, dict) else json.loads(msg.content)
                break

        structured_response: AgentResponse = {
            "task": task,
            "agent_name": "sleep_agent",
            "data": agent_data
        }

        return Command(
            update={
                "structured_responses": state.get("structured_responses", []) + [structured_response],
                "messages": [HumanMessage(content=f"{task}, completed")]
            },
            goto="supervisor"
        )

    return _node