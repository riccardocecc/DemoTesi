"""
Nodo di visualizzazione per il team Kitchen - VERSIONE SEMPLICE
Un solo agente ReAct che decide quali grafici generare e li crea.
"""

from typing import Literal
import json

from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_core.messages import HumanMessage, ToolMessage

from backend.models.state import State, GraphData
from backend.tools.visualization_kitchen_tool import generate_kitchen_timeslot_chart, generate_kitchen_metrics_dashboard


def create_kitchen_visualization_node(llm):
    """
    Crea un nodo di visualizzazione semplice con un agente ReAct.
    """
    tools = [
        generate_kitchen_timeslot_chart,
        generate_kitchen_metrics_dashboard
    ]


    system_prompt = (
        "You generate Plotly graphs for kitchen usage analysis.\n\n"
        "AVAILABLE TOOLS:\n"
        "- generate_kitchen_timeslot_chart: bar chart of usage by time slot (breakfast/lunch/dinner)\n"
        "- generate_kitchen_metrics_dashboard: dashboard with key metrics (frequency, duration, total time)\n\n"
        "RULES:\n"
        "- If query mentions specific aspects (meal times, frequency, etc), generate ONLY those graphs\n"
        "- If query is generic ('kitchen usage?'), generate both graphs\n"
        "- Use kitchen_data for all tools\n"
        "- Generate graphs that answer the user's question\n"
    )


    agent = create_react_agent(llm, tools=tools, prompt=system_prompt)

    def kitchen_visualization_node(state: State) -> Command[Literal["kitchen_team_supervisor"]]:
        """
        Genera grafici usando un agente ReAct.
        """
        print(f"\n{'=' * 60}")
        print("KITCHEN VISUALIZATION - Generating graphs")
        print(f"{'=' * 60}\n")

        original_question = state.get("original_question", "")
        team_responses = state.get("structured_responses", [])


        kitchen_data = None

        for team_resp in team_responses:
            if team_resp["team_name"] == "kitchen_team":
                for resp in team_resp["structured_responses"]:
                    if "error" not in resp["data"]:
                        if resp["agent_name"] == "kitchen_agent":
                            kitchen_data = resp["data"]
                break

        if not kitchen_data:
            print("No data available, skipping visualization")
            return Command(
                goto="kitchen_team_supervisor",
                update={
                    "messages": [HumanMessage(
                        content="Visualization skipped: no data",
                        name="kitchen_visualization"
                    )]
                }
            )


        data_dict = {"kitchen_data": kitchen_data}


        prompt = f"""Query: "{original_question}"

Data: {json.dumps(data_dict, default=str)}"""


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
                        print(f"✓ Generated: {content['id']}")

            print(f"\nGenerated {len(graphs)} graphs\n")


            existing_graphs = state.get("graphs", [])

            return Command(
                goto="kitchen_team_supervisor",
                update={
                    "graphs": existing_graphs + graphs,
                    "messages": [HumanMessage(
                        content=f"Visualization completed: {len(graphs)} graphs",
                        name="kitchen_visualization"
                    )]
                }
            )

        except Exception as e:
            print(f"Visualization failed: {e}")
            return Command(
                goto="kitchen_team_supervisor",
                update={
                    "messages": [HumanMessage(
                        content=f"Visualization failed: {str(e)}",
                        name="kitchen_visualization"
                    )]
                }
            )

    return kitchen_visualization_node