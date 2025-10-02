
from typing import Literal

from langgraph.prebuilt import create_react_agent

from backend.models.results import MobilityAnalysisResult, ErrorResult
from backend.models.state import State, AgentResponse
from langgraph.types import Command
from langchain_core.messages import HumanMessage, ToolMessage

from backend.tools.mobility_tools import analyze_mobility_patterns


def create_mobility_agent(llm):
    tools = [analyze_mobility_patterns]
    return create_react_agent(llm, tools=tools)

def mobility_node(mobility_agent):
    def _node(state: State) -> Command[Literal["supervisor"]]:
        task = None
        for msg in reversed(state["messages"]):
            if hasattr(msg, 'name') and msg.name == "supervisor_instruction":
                task = msg.content.replace("[TASK]: ", "")
                break

        print(f"DEBUG - Kitchen agent received task: '{task}'")
        message = task or "Analizza la mobilità del soggetto richiesto."

        focused_state = {"messages": [HumanMessage(content=message)]}
        result = mobility_agent.invoke(focused_state)
        print("result " + str(result))

        agent_data: MobilityAnalysisResult | ErrorResult | None = None
        for msg in result["messages"]:
            if isinstance(msg, ToolMessage):
                import json


                if isinstance(msg.content, dict):
                    raw_data = msg.content
                elif isinstance(msg.content, str):
                    raw_data = json.loads(msg.content)
                else:
                    raw_data = {"error": f"Formato risposta non valido: {type(msg.content)}"}


                if "error" in raw_data:
                    agent_data = raw_data
                else:
                    agent_data = raw_data
                break

        if not agent_data:
            agent_data = {"error": "Nessuna risposta dall'agente mobility"}




        structured_response: AgentResponse = {
            "task": message,
            "agent_name": "mobility_agent",
            "data": agent_data
        }
        print(f"DEBUG - Mobility agent response type: {type(structured_response['data'])}")

        return Command(
            update={
                "structured_responses":  state.get("structured_responses", []) + [structured_response],
                "messages": [HumanMessage(content=task + ", completed")]
            },
            goto="supervisor",
        )
    return _node