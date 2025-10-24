"""
Nodo di visualizzazione per il team Sleep - VERSIONE AGGIORNATA
Agente ReAct che usa i nuovi tool basati sui 3 tool di analisi del sonno.
"""

from typing import Literal
import json
from google.api_core import exceptions
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_core.messages import HumanMessage, ToolMessage

from backend.config.settings import invoke_with_retry
from backend.models.state import State, GraphData
from backend.tools.visualization_sleep_tools import (
    visualize_sleep_statistics,
    visualize_sleep_distribution,
    visualize_sleep_quality_correlation
)


def create_sleep_visualization_node(llm):
    """
    Crea un nodo di visualizzazione con agente ReAct.
    Ora supporta tutti i nuovi grafici basati sui 3 tool di analisi.
    """

    # Tool disponibili (7 grafici)
    tools = [
        visualize_sleep_statistics,
        visualize_sleep_distribution,
        visualize_sleep_quality_correlation
    ]

    # System prompt aggiornato
    system_prompt = (
        "You generate Plotly graphs for sleep analysis based on 3 types of data:\n\n"
        "AVAILABLE TOOLS:\n"
        "- visualize_sleep_statistics: statistiche generali sul sonno \n"
        "- visualize_sleep_distribution: visualizzazione per la distribuzione delle fasi del sonno (REM, DEEP, LEGGER)\n"
        "- visualize_sleep_quality_correlation: visualizzazione per le correlazioni tra interruzioni e qualità del sonno Risvegli vs Tempo di sonno"
        "- Uscite dal letto vs Tempo di sonno\n"
        "RULES\n"
        "for generic query about sleep use ONLY visualize_sleep_statistics\n"
        "IMPORTANT choose ONLY THE MOST RELEVANT. MAX 1 graph for each query"
    )

    # Crea agente ReAct
    agent = create_react_agent(llm, tools=tools, prompt=system_prompt)

    def sleep_visualization_node(state: State) -> Command[Literal["sleep_team_supervisor"]]:
        """
        Genera grafici usando un agente ReAct che interpreta i nuovi dati strutturati.
        """
        print(f"\n{'=' * 60}")
        print("SLEEP VISUALIZATION - Generating graphs")
        print(f"{'=' * 60}\n")

        original_question = state.get("original_question", "")
        team_responses = state.get("structured_responses", [])

        # Estrai dati del team Sleep
        sleep_data = None
        heart_data = None

        for team_resp in team_responses:
            if team_resp["team_name"] == "sleep_team":
                for resp in team_resp["structured_responses"]:
                    if "error" not in resp["data"]:
                        if resp["agent_name"] == "sleep_agent":
                            sleep_data = resp["data"]
                        elif resp["agent_name"] == "heart_freq_agent":
                            heart_data = resp["data"]
                break

        if not sleep_data and not heart_data:
            print("No data available, skipping visualization")
            return Command(
                goto="sleep_team_supervisor",
                update={
                    "messages": [HumanMessage(
                        content="Visualization skipped: no data",
                        name="sleep_visualization"
                    )]
                }
            )

        # Log dei dati disponibili
        print("Available data:")
        if sleep_data:
            if "results" in sleep_data:
                print(f"   - sleep_data with {sleep_data['num_analyses']} analyses")
                for i, result in enumerate(sleep_data["results"]):
                    keys = list(result.keys())[:5]  # Prime 5 chiavi
                    print(f"     Result {i+1}: {keys}...")
            else:
                keys = list(sleep_data.keys())[:5]
                print(f"   - sleep_data: {keys}...")
        if heart_data:
            print(f"   - heart_data available")

        # Costruisci prompt per l'agente
        data_dict = {"sleep_data": sleep_data, "heart_data": heart_data}

        prompt = f"""Query: "{original_question}"

Available data: {json.dumps(data_dict, default=str, indent=2)}

Generate appropriate graphs based on the query and available data."""

        try:
            try:
                result = invoke_with_retry(agent, [HumanMessage(content=prompt)], 3)
            except exceptions.ResourceExhausted as e:
                print(f"Generazione garfico fallito dopo {e} tenativi")

            print("CHIAMTA LLM")

            graphs: list[GraphData] = []

            for msg in result["messages"]:
                if isinstance(msg, ToolMessage):
                    content = msg.content

                    if isinstance(content, str):
                        try:
                            content = json.loads(content)
                        except:
                            continue

                    if isinstance(content, dict) and "id" in content and "plotly_json" in content:
                        graphs.append(content)
                        print(f"✓ Generated: {content['id']} - {content['title']}")
                    elif isinstance(content, dict) and "error" in content:
                        print(f"✗ Tool error: {content['error']}")

            print(f"\nGenerated {len(graphs)} graphs total\n")

            return Command(
                goto="sleep_team_supervisor",
                update={
                    "graphs": graphs,
                    "messages": [HumanMessage(
                        content=f"Visualization completed: {len(graphs)} graphs",
                        name="sleep_visualization"
                    )]
                }
            )

        except Exception as e:
            print(f"❌ Visualization failed: {e}")
            import traceback
            traceback.print_exc()

            return Command(
                goto="sleep_team_supervisor",
                update={
                    "messages": [HumanMessage(
                        content=f"Visualization failed: {str(e)}",
                        name="sleep_visualization"
                    )]
                }
            )

    return sleep_visualization_node