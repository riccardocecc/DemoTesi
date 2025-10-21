"""
Nodo di visualizzazione per il team Sleep - VERSIONE AGGIORNATA
Agente ReAct che usa i nuovi tool basati sui 3 tool di analisi del sonno.
"""

from typing import Literal
import json

from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_core.messages import HumanMessage, ToolMessage

from backend.models.state import State, GraphData
from backend.tools.visualization_sleep_tools import (
    generate_sleep_phases_chart,
    generate_sleep_efficiency_gauge,
    generate_sleep_statistics_dashboard,
    generate_sleep_disturbances_chart,
    generate_sleep_correlation_heatmap,
    generate_sleep_variability_box,
    generate_heart_rate_timeline
)


def create_sleep_visualization_node(llm):
    """
    Crea un nodo di visualizzazione con agente ReAct.
    Ora supporta tutti i nuovi grafici basati sui 3 tool di analisi.
    """

    # Tool disponibili (7 grafici)
    tools = [
        generate_sleep_phases_chart,
        generate_sleep_efficiency_gauge,
        generate_sleep_statistics_dashboard,
        generate_sleep_disturbances_chart,
        generate_sleep_correlation_heatmap,
        generate_sleep_variability_box,
        generate_heart_rate_timeline
    ]

    # System prompt aggiornato
    system_prompt = (
        "You generate Plotly graphs for sleep analysis based on 3 types of data:\n\n"
        "DATA TYPES:\n"
        "1. analyze_sleep_statistics → statistics dashboard, variability box plot\n"
        "2. analyze_sleep_distribution → phases pie chart, efficiency gauge\n"
        "3. analyze_sleep_quality_correlation → disturbances bar, correlation heatmap\n"
        "4. analyze_daily_heart_rate → heart rate timeline\n\n"
        "AVAILABLE TOOLS:\n"
        "- generate_sleep_phases_chart: pie chart of REM/deep/light sleep (needs distribution data)\n"
        "- generate_sleep_efficiency_gauge: gauge 0-100% (needs distribution data)\n"
        "- generate_sleep_statistics_dashboard: 4 metrics with mean±std (needs statistics data)\n"
        "- generate_sleep_disturbances_chart: bar chart wake-ups (needs quality_correlation data)\n"
        "- generate_sleep_correlation_heatmap: correlations heatmap (needs quality_correlation data)\n"
        "- generate_sleep_variability_box: box plots showing variability (needs statistics data)\n"
        "- generate_heart_rate_timeline: line chart heart rate over time (needs heart_data)\n\n"
        "RULES\n"
        "for generic query about sleep use ONLY generate_sleep_statistics_dashboard"
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
            print("⚠️  No data available, skipping visualization")
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
        print("📊 Available data:")
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
            result = agent.invoke({"messages": [HumanMessage(content=prompt)]})
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

            print(f"\n✅ Generated {len(graphs)} graphs total\n")

            # Update state
            existing_graphs = state.get("graphs", [])

            return Command(
                goto="sleep_team_supervisor",
                update={
                    "graphs": existing_graphs + graphs,
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