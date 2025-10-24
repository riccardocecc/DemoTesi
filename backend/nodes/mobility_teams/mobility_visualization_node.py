"""
Nodo di visualizzazione per il team Mobility - VERSIONE SEMPLICE
Un solo agente ReAct che decide quali grafici generare e li crea.
"""

from typing import Literal
import json
from google.api_core import exceptions
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langchain_core.messages import HumanMessage, ToolMessage

from backend.config.settings import invoke_with_retry
from backend.models.state import State, GraphData
from backend.tools.visualization_mobility_tool import visualize_mobility_patterns


def create_mobility_visualization_node(llm):
    """
    Crea un nodo di visualizzazione semplice con un agente ReAct.
    """

    # Tool disponibili
    tools = [
        visualize_mobility_patterns
    ]

    # System prompt conciso
    system_prompt = (
        "You generate Plotly graphs for mobility analysis.\n\n"
        "AVAILABLE TOOLS:\n"
        "- visualize_mobility_patterns: visualizza come si muove o si comporta dentro casa il paziente\n"
    )

    # Crea agente ReAct
    agent = create_react_agent(llm, tools=tools, prompt=system_prompt)

    def mobility_visualization_node(state: State) -> Command[Literal["mobility_team_supervisor"]]:
        """
        Genera grafici usando un agente ReAct.
        """
        print(f"\n{'=' * 60}")
        print("MOBILITY VISUALIZATION - Generating graphs")
        print(f"{'=' * 60}\n")

        original_question = state.get("original_question", "")
        team_responses = state.get("structured_responses", [])

        # Estrai dati del team Mobility
        mobility_data = None

        for team_resp in team_responses:
            if team_resp["team_name"] == "mobility_team":
                for resp in team_resp["structured_responses"]:
                    if "error" not in resp["data"]:
                        if resp["agent_name"] == "mobility_agent":
                            mobility_data = resp["data"]
                break

        if not mobility_data:
            print("⚠No data available, skipping visualization")
            return Command(
                goto="mobility_team_supervisor",
                update={
                    "messages": [HumanMessage(
                        content="Visualization skipped: no data",
                        name="mobility_visualization"
                    )]
                }
            )

        # Costruisci prompt MINIMO per l'agente
        data_dict = {"mobility_data": mobility_data}

        # Prompt semplice: solo query + dati
        prompt = f"""Query: "{original_question}"

Data: {json.dumps(data_dict, default=str)}"""

        # Invoca agente
        try:
            try:
                result = invoke_with_retry(agent, [HumanMessage(content=prompt)], 3)
            except exceptions.ResourceExhausted as e:
                print(f"Generazione grafico fallito {e} tenatitivi")


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



            return Command(
                goto="mobility_team_supervisor",
                update={
                    "graphs":  graphs,
                    "messages": [HumanMessage(
                        content=f"Visualization completed: {len(graphs)} graphs",
                        name="mobility_visualization"
                    )]
                }
            )

        except Exception as e:
            print(f"✗ Visualization failed: {e}")
            return Command(
                goto="mobility_team_supervisor",
                update={
                    "messages": [HumanMessage(
                        content=f"Visualization failed: {str(e)}",
                        name="mobility_visualization"
                    )]
                }
            )

    return mobility_visualization_node