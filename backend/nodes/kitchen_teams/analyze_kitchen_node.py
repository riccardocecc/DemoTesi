import json
from typing import Literal

from langgraph.prebuilt import create_react_agent

from backend.models.results import KitchenAnalysisResult, ErrorResult
from backend.models.state import State, AgentResponse, TeamResponse
from langgraph.types import Command
from langchain_core.messages import HumanMessage, ToolMessage

from backend.tools.kitchen_tools import analyze_kitchen_activity


def create_analyze_kitchen_agent(llm):
    tools = [analyze_kitchen_activity]
    return create_react_agent(llm, tools=tools)


def create_analyze_kitchen_node(analyze_kitchen_agent):
    def _node(state: State) -> Command[Literal["kitchen_team_supervisor"]]:

        task = None
        for msg in reversed(state["messages"]):
            if hasattr(msg, 'name') and msg.name == "supervisor_instruction":
                task = msg.content.replace("[TASK]: ", "")
                break

        print(f"DEBUG - Kitchen agent received task: '{task}'")
        message = task or "Analizza l'attività di cucina del soggetto richiesto."

        # Invoca agent con focused_state
        focused_state = {"messages": [HumanMessage(content=message)]}
        result = analyze_kitchen_agent.invoke(focused_state)
        print("result " + str(result))

        # Estrai dati strutturati
        agent_data: KitchenAnalysisResult | ErrorResult | None = None
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
            agent_data = {"error": "Nessuna risposta dall'agente kitchen"}


        agent_response: AgentResponse = {
            "task": message,
            "agent_name": "kitchen_agent",
            "data": agent_data
        }

        print(f"DEBUG - Kitchen agent response type: {type(agent_response['data'])}")


        current_responses = state.get("structured_responses", [])

        # Cerca se esiste già un TeamResponse per kitchen_team
        kitchen_team_response = None
        for team_resp in current_responses:
            if team_resp["team_name"] == "kitchen_team":
                kitchen_team_response = team_resp
                break

        # Aggiorna o crea TeamResponse
        if kitchen_team_response:
            # Aggiungi la nuova risposta all'array esistente
            kitchen_team_response["structured_responses"].append(agent_response)
            updated_responses = current_responses
        else:
            # Crea un nuovo TeamResponse
            new_team_response: TeamResponse = {
                "structured_responses": [agent_response],
                "team_name": "kitchen_team"
            }
            updated_responses = current_responses + [new_team_response]

        # Aggiorna completed_tasks
        completed_tasks = state.get("completed_tasks", set())
        completed_tasks.add(task)

        return Command(
            update={
                "structured_responses": updated_responses,
                "completed_tasks": completed_tasks,
                "messages": [HumanMessage(content=f"KitchenNode completed: {task}", name="kitchen_node_response")]
            },
            goto="kitchen_team_supervisor"
        )

    return _node