import json
from typing import Literal

from langgraph.prebuilt import create_react_agent


from backend.models.results  import(
SleepStatisticsResult,
    SleepDistributionResult,
    SleepQualityCorrelationResult,
    ErrorResult
)
from backend.models.state import State, AgentResponse, TeamResponse
from langgraph.types import Command
from langchain_core.messages import HumanMessage, ToolMessage
from backend.tools.sleep_tools import (
    analyze_sleep_statistics,
    analyze_sleep_distribution,
    analyze_sleep_quality_correlation
)


def create_analyze_sleep_agent(llm):
    """
        Crea l'agente ReAct per l'analisi del sonno con i nuovi tool.

        L'agente ha accesso a tre tool specializzati:
        1. analyze_sleep_statistics: statistiche descrittive complete
        2. analyze_sleep_distribution: distribuzione fasi del sonno
        3. analyze_sleep_quality_correlation: correlazioni interruzioni-qualità
        """
    tools = [
        analyze_sleep_statistics,
        analyze_sleep_distribution,
        analyze_sleep_quality_correlation
    ]

    system_message = (
        "You are a specialized agent for analyzing sleep patterns and quality.\n\n"
        "AVAILABLE TOOLS:\n"
        "1. analyze_sleep_statistics: Use this for statistical analysis (mean, median, std dev, range) "
        "of all sleep metrics. Call this when the user asks for:\n"
        "   - Statistical overview\n"
        "   - Average values with variability\n"
        "   - Range of values (min/max)\n"
        "   - Data consistency analysis\n\n"
        "2. analyze_sleep_distribution: Use this to understand how sleep time is distributed "
        "across phases (REM, deep, light). Call this when the user asks for:\n"
        "   - Sleep phase distribution\n"
        "   - Percentage of time in each phase\n"
        "   - Sleep composition\n"
        "   - Sleep efficiency\n\n"
        "3. analyze_sleep_quality_correlation: Use this to analyze relationships between "
        "sleep interruptions and sleep quality. Call this when the user asks for:\n"
        "   - Impact of wake-ups on sleep\n"
        "   - Correlation between interruptions and quality\n"
        "   - How disturbances affect sleep duration/efficiency\n"
        "   - Relationship between getting out of bed and deep sleep\n\n"
        "IMPORTANT RULES:\n"
        "- Always extract subject_id and period from the user's request\n"
        "- If the query is general about sleep (e.g., 'how did they sleep?'), call ONLY analyze_sleep_statistics tool\n"
        "- If the query is specific, call only the relevant tool(s)\n"
        "- Use the same subject_id and period for all tool calls\n"
        "- NEVER analyze heart rate or respiratory rate - those are handled by other agents\n\n"
        "EXAMPLES:\n"
        "Query: 'Analyze sleep of subject 2 in last 7 days'\n"
        "→ Call analyze_sleep_statistics tools with subject_id=2, period='last_7_days'\n\n"
        "Query: 'What's the distribution of sleep phases for subject 1?'\n"
        "→ Call only analyze_sleep_distribution with subject_id=1\n\n"
        "Query: 'Do wake-ups affect sleep quality for subject 3?'\n"
        "→ Call only analyze_sleep_quality_correlation with subject_id=3\n"
    )

    return create_react_agent(llm, tools=tools, prompt=system_message)


def create_analyze_sleep_node(analyze_sleep_agent):
    """
    Nodo che coordina l'agente di analisi del sonno.
    Raccoglie TUTTI i risultati dei tool chiamati dall'agente.
    """

    def _node(state: State) -> Command[Literal["sleep_team_supervisor"]]:
        # Estrai task dal supervisor
        task = None
        for msg in reversed(state["messages"]):
            if hasattr(msg, 'name') and msg.name == "supervisor_instruction":
                task = msg.content.replace("[TASK]: ", "")
                break

        print(f"DEBUG - Sleep agent received task: '{task}'")
        message = task or "Analizza il sonno del soggetto richiesto."

        # Invoca agent
        focused_state = {"messages": [HumanMessage(content=message)]}
        result = analyze_sleep_agent.invoke(focused_state)
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
            agent_data = {"error": "Nessuna risposta dall'agente sleep"}
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
            "agent_name": "sleep_agent",
            "data": agent_data
        }

        print(f"DEBUG - Sleep agent response: {len(all_results)} result(s) collected")

        # Aggiorna state
        current_responses = state.get("structured_responses", [])

        sleep_team_response = None
        for team_resp in current_responses:
            if team_resp["team_name"] == "sleep_team":
                sleep_team_response = team_resp
                break

        if sleep_team_response:
            sleep_team_response["structured_responses"].append(agent_response)
            updated_responses = current_responses
        else:
            new_team_response: TeamResponse = {
                "structured_responses": [agent_response],
                "team_name": "sleep_team"
            }
            updated_responses = current_responses + [new_team_response]

        completed_tasks = state.get("completed_tasks", set())
        completed_tasks.add(task)

        return Command(
            update={
                "structured_responses": updated_responses,
                "completed_tasks": completed_tasks,
                "messages": [HumanMessage(content=f"SleepNode completed: {task}", name="sleep_node_response")],
            },
            goto="sleep_team_supervisor"
        )

    return _node