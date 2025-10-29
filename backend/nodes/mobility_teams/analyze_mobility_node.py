import json
from typing import Literal
from google.api_core import exceptions
from langgraph.prebuilt import create_react_agent

from backend.config.settings import invoke_with_retry
from backend.models.results import MobilityAnalysisResult, ErrorResult
from backend.models.state import State, AgentResponse, TeamResponse
from langgraph.types import Command
from langchain_core.messages import HumanMessage, ToolMessage

from backend.tools.mobility_tools import analyze_mobility_patterns


def create_analyze_mobility_agent(llm):
    """
    Crea l'agente ReAct per l'analisi della mobilità.

    L'agente ha accesso a tool specializzato:
    1. analyze_mobility_patterns: analisi dei pattern di movimento in casa
    """
    tools = [analyze_mobility_patterns]

    system_message = (
        "You are a specialized agent for analyzing home mobility patterns.\n\n"
        "AVAILABLE TOOLS:\n"
        "1. analyze_mobility_patterns: Use this to analyze movement patterns within the home. "
        "Call this when the user asks for:\n"
        "   - Room usage and distribution\n"
        "   - Movement frequency and patterns\n"
        "   - Time spent in different areas\n"
        "   - Activity levels throughout the day\n"
        "   - Mobility trends over time\n\n"
        "IMPORTANT RULES:\n"
        "- Always extract subject_id and period from the user's request\n"
        "- Use the same subject_id and period for all tool calls\n"
        "- Focus only on environmental sensor data (PIR sensors)\n\n"
        "EXAMPLES:\n"
        "Query: 'Analyze mobility of subject 2 in last 4 days'\n"
        "→ Call analyze_mobility_patterns with subject_id=2, period='last_4_days'\n\n"
        "Query: 'What rooms does subject 1 use most?'\n"
        "→ Call analyze_mobility_patterns with subject_id=1\n"
    )

    return create_react_agent(llm, tools=tools, prompt=system_message)


def create_analyze_mobility_node(analyze_mobility_agent):
    """
    Nodo che coordina l'agente di analisi della mobilità.
    Raccoglie TUTTI i risultati dei tool chiamati dall'agente.
    """

    def _node(state: State) -> Command[Literal["mobility_team_supervisor"]]:
        # Estrai task dal supervisor
        task = None
        for msg in reversed(state["messages"]):
            if hasattr(msg, 'name') and msg.name == "supervisor_instruction":
                task = msg.content.replace("[TASK]: ", "")
                break

        print(f"DEBUG - Mobility agent received task: '{task}'")
        message = task or "Analizza la mobilità del soggetto richiesto."

        # Invoca l'agente
        try:
            result = invoke_with_retry(analyze_mobility_agent, [HumanMessage(content=message)])
        except exceptions.ResourceExhausted as e:
            print(f"Failed after all retries: {e}")

        print("CHIAMATA LLM")
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
            agent_data = {"error": "Nessuna risposta dall'agente mobility"}
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
            "agent_name": "mobility_agent",
            "data": agent_data
        }

        print(f"DEBUG - Mobility agent response: {len(all_results)} result(s) collected")

        # Aggiorna state
        current_responses = state.get("structured_responses", [])

        mobility_team_response = None
        for team_resp in current_responses:
            if team_resp["team_name"] == "mobility_team":
                mobility_team_response = team_resp
                break

        if mobility_team_response:
            mobility_team_response["structured_responses"].append(agent_response)
            updated_responses = current_responses
        else:
            new_team_response: TeamResponse = {
                "structured_responses": [agent_response],
                "team_name": "mobility_team"
            }
            updated_responses = current_responses + [new_team_response]

        completed_tasks = state.get("completed_tasks", set())
        completed_tasks.add(task)

        return Command(
            update={
                "structured_responses": updated_responses,
                "completed_tasks": completed_tasks,
                "messages": [HumanMessage(content=f"MobilityNode completed: {task}", name="mobility_node_response")],
            },
            goto="mobility_team_supervisor"
        )

    return _node