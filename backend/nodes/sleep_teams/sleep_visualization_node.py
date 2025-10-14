"""
Nodo di visualizzazione per il team Sleep - VERSIONE SEMPLICE
Un solo agente ReAct che decide quali grafici generare e li crea.
"""

from typing import Literal
import json

from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_core.messages import HumanMessage, ToolMessage

from backend.models.state import State, GraphData, AgentResponse
from backend.tools.visualization_sleep_tools import (
    generate_sleep_phases_chart,
    generate_sleep_efficiency_gauge,
    generate_sleep_disturbances_chart,
    generate_heart_rate_timeline
)


def create_sleep_visualization_node(llm):
    """
    Crea un nodo di visualizzazione semplice con un agente ReAct.
    """

    # Tool disponibili
    tools = [
        generate_sleep_phases_chart,
        generate_sleep_efficiency_gauge,
        generate_sleep_disturbances_chart,
        generate_heart_rate_timeline
    ]

    # System prompt conciso
    system_prompt = (
        "You generate Plotly graphs for sleep analysis.\n\n"
        "AVAILABLE TOOLS:\n"
        "- generate_sleep_phases_chart: pie chart of REM/deep/light sleep\n"
        "- generate_sleep_efficiency_gauge: gauge showing efficiency 0-100%\n"
        "- generate_sleep_disturbances_chart: bar chart of wake-ups\n"
        "- generate_heart_rate_timeline: line chart of heart rate\n\n"
        "RULES:\n"
        "- If query mentions specific aspects (REM, efficiency, etc), generate ONLY those graphs\n"
        "- If query is generic ('how did they sleep?'), generate efficiency + phases (max 2 graphs)\n"
        "- Use sleep_data for sleep tools, heart_data for heart tool\n"
        "- Generate graphs that answer the user's question\n"
    )

    # Crea agente ReAct
    agent = create_react_agent(llm, tools=tools, prompt=system_prompt)

    def sleep_visualization_node(state: State) -> Command[Literal["sleep_team_supervisor"]]:
        """
        Genera grafici usando un agente ReAct.
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

        # Costruisci prompt MINIMO per l'agente
        data_dict = {"sleep_data": sleep_data, "heart_data": heart_data}



        # Prompt semplice: solo query + dati
        prompt = f"""Query: "{original_question}"

Data: {json.dumps(data_dict, default=str)}"""

        # Invoca agente
        try:
            result = agent.invoke({"messages": [HumanMessage(content=prompt)]})

            # Estrai grafici dai ToolMessage
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
                        print(f"✓ Generated: {content['id']}")

            print(f"\n✅ Generated {len(graphs)} graphs\n")

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
            print(f"✗ Visualization failed: {e}")
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