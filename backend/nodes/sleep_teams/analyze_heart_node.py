import json
from typing import Literal

from langgraph.prebuilt import create_react_agent

from backend.models.results import DailyHeartRateResult, ErrorResult
from backend.models.state import State, AgentResponse, TeamResponse
from langgraph.types import Command
from langchain_core.messages import HumanMessage, ToolMessage

from backend.tools.sleep_tools import analyze_daily_heart_rate


def create_analyze_heart_agent(llm):
    tools = [analyze_daily_heart_rate]
    return create_react_agent(llm, tools=tools)


def create_analyze_heart_node(analyze_heart_agent):
    def _node(state: State) -> Command[Literal["sleep_team_supervisor"]]:
        # Estrai task
        task = None
        for msg in reversed(state["messages"]):
            if hasattr(msg, 'name') and msg.name == "supervisor_instruction":
                task = msg.content.replace("[TASK]: ", "")
                break

        print(f"DEBUG - Heart rate agent received task: '{task}'")
        message = task or "Analizza la frequenza cardiaca del soggetto richiesto."

        # Invoca agent con focused_state
        focused_state = {"messages": [HumanMessage(content=message)]}
        result = analyze_heart_agent.invoke(focused_state)
        print("result " + str(result))

        # Estrai dati strutturati
        agent_data: DailyHeartRateResult | ErrorResult | None = None
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
            agent_data = {"error": "Nessuna risposta dall'agente heart rate"}

        # Crea AgentResponse
        agent_response: AgentResponse = {
            "task": message,
            "agent_name": "heart_freq_agent",
            "data": agent_data
        }

        print(f"DEBUG - Heart rate agent response type: {type(agent_response['data'])}")

        # Recupera structured_responses esistenti
        current_responses = state.get("structured_responses", [])

        # Cerca se esiste già un TeamResponse per sleep_team
        sleep_team_response = None
        for team_resp in current_responses:
            if team_resp["team_name"] == "sleep_team":
                sleep_team_response = team_resp
                break

        # Aggiorna o crea TeamResponse
        if sleep_team_response:
            # Aggiungi la nuova risposta all'array esistente
            sleep_team_response["structured_responses"].append(agent_response)
            updated_responses = current_responses
        else:
            # Crea un nuovo TeamResponse
            new_team_response: TeamResponse = {
                "structured_responses": [agent_response],
                "team_name": "sleep_team"
            }
            updated_responses = current_responses + [new_team_response]

        # Aggiorna completed_tasks
        completed_tasks = state.get("completed_tasks", set())
        completed_tasks.add(task)

        return Command(
            update={
                "structured_responses": updated_responses,
                "completed_tasks": completed_tasks,
                "messages": [HumanMessage(content=f"HeartRateNode completed: {task}", name="heart_node_response")]
            },
            goto="sleep_team_supervisor"
        )

    return _node