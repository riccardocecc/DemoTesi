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

        print(f"DEBUG - Sleep agent received task: '{task}'")
        message = task or "Analizza il sonno del soggetto richiesto."

        # Invoca agent con focused_state
        focused_state = {"messages": [HumanMessage(content=message)]}
        result = sleep_agent.invoke(focused_state)
        print("result " + str(result))

        # Estrai dati strutturati
        agent_data: SleepAnalysisResult | ErrorResult | None = None
        for msg in result["messages"]:
            if isinstance(msg, ToolMessage):
                if isinstance(msg.content, dict):
                    raw_data = msg.content
                elif isinstance(msg.content, str):
                    try:
                        raw_data = json.loads(msg.content)
                    except json.JSONDecodeError:
                        raw_data = {"error": "JSON parsing failed"}
                else:
                    raw_data = {"error": f"Formato risposta non valido: {type(msg.content)}"}

                if "error" in raw_data:
                    agent_data = raw_data
                else:
                    agent_data = raw_data
                break

        if not agent_data:
            agent_data = {"error": "Nessuna risposta dall'agente sleep"}

        structured_response: AgentResponse = {
            "task": message,
            "agent_name": "sleep_agent",
            "data": agent_data
        }

        print(f"DEBUG - Sleep agent response type: {type(structured_response['data'])}")

        return Command(
            update={
                "structured_responses": state.get("structured_responses", []) + [structured_response],
                "messages": [HumanMessage(content=task)]  # ✅ CORRETTO
            },
            goto="supervisor"
        )

    return _node