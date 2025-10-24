import json
from typing import Literal
from google.api_core import exceptions
from langgraph.prebuilt import create_react_agent

from backend.config.settings import invoke_with_retry
from backend.models.results import KitchenAnalysisResult, ErrorResult
from backend.models.state import State, AgentResponse, TeamResponse
from langgraph.types import Command
from langchain_core.messages import HumanMessage, ToolMessage

from backend.tools.kitchen_tools import (
    analyze_kitchen_statistics,
    analyze_kitchen_usage_pattern,
    analyze_kitchen_temperature
)


def create_analyze_kitchen_agent(llm):
    tools = [
        analyze_kitchen_statistics,
        analyze_kitchen_usage_pattern,
        analyze_kitchen_temperature
    ]
    system_message = (
        "You are a specialized agent for analyzing kitchen usage patterns.\n\n"
        "AVAILABLE TOOLS:\n"
        "1. analyze_kitchen_statistics: Statistical analysis (mean, median, std dev, range)\n"
        "2. analyze_kitchen_usage_pattern: When and how kitchen is used (time slots, patterns)\n"
        "3. analyze_kitchen_temperature: Temperature analysis (cooking intensity, types)\n\n"
        "CRITICAL RULE: For GENERAL kitchen queries, call ONLY analyze_kitchen_statistics.\n"
        "Only call additional tools if the user explicitly asks for:\n"
        "- 'when' or 'time slots' or 'meal times' or 'pattern' → add analyze_kitchen_usage_pattern\n"
        "- 'temperature' or 'cooking intensity' or 'how hot' → add analyze_kitchen_temperature\n\n"
        "Always extract subject_id and period from the user's request.\n"
    )

    return create_react_agent(llm, tools=tools, prompt=system_message)


def create_analyze_kitchen_node(analyze_kitchen_agent):
    """
    Nodo che coordina l'agente di analisi cucina.
    Raccoglie TUTTI i risultati dei tool chiamati dall'agente.
    """

    def _node(state: State) -> Command[Literal["kitchen_team_supervisor"]]:
        # Estrai task dal supervisor
        task = None
        for msg in reversed(state["messages"]):
            if hasattr(msg, 'name') and msg.name == "supervisor_instruction":
                task = msg.content.replace("[TASK]: ", "")
                break

        print(f"DEBUG - Kitchen agent received task: '{task}'")
        message = task or "Analizza l'attività di cucina del soggetto richiesto."

        try:
            result = invoke_with_retry(analyze_kitchen_agent, [HumanMessage(content=message)], 3)
        except exceptions.ResourceExhausted as e:
            print(f"Failed after all retries: {e}")



        print("result " + str(result))

        # Raccoglie TUTTI i risultati dai ToolMessage
        all_results = []

        for msg in result["messages"]:
            if isinstance(msg, ToolMessage):
                # Parse del contenuto
                if isinstance(msg.content, dict):
                    raw_data = msg.content
                elif isinstance(msg.content, str):
                    try:
                        raw_data = json.loads(msg.content)
                    except json.JSONDecodeError:
                        raw_data = {"error": "JSON parsing failed"}
                else:
                    raw_data = {"error": f"Formato risposta non valido: {type(msg.content)}"}

                # Aggiungi il risultato alla lista
                all_results.append(raw_data)

        # Se non ci sono risultati, genera errore
        if not all_results:
            agent_data = {"error": "Nessuna risposta dall'agente kitchen"}
        elif len(all_results) == 1:
            # Un solo tool chiamato - usa direttamente il risultato
            agent_data = all_results[0]
        else:
            # Multipli tool chiamati - crea un dizionario aggregato
            agent_data = {
                "results": all_results,
                "num_analyses": len(all_results)
            }

        # Crea AgentResponse
        agent_response: AgentResponse = {
            "task": message,
            "agent_name": "kitchen_agent",
            "data": agent_data
        }

        print(f"DEBUG - Kitchen agent response: {len(all_results)} result(s) collected")

        # Aggiorna state
        current_responses = state.get("structured_responses", [])

        kitchen_team_response = None
        for team_resp in current_responses:
            if team_resp["team_name"] == "kitchen_team":
                kitchen_team_response = team_resp
                break

        if kitchen_team_response:
            kitchen_team_response["structured_responses"].append(agent_response)
            updated_responses = current_responses
        else:
            new_team_response: TeamResponse = {
                "structured_responses": [agent_response],
                "team_name": "kitchen_team"
            }
            updated_responses = current_responses + [new_team_response]

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