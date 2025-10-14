"""
Nodo di visualizzazione specifico per il team Sleep.
Usa un agente ReAct con tool per generare grafici Plotly.
"""

from typing import Literal
import json

from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langgraph.graph import END
from langchain_core.messages import HumanMessage, ToolMessage

from backend.models.state import State, GraphData, AgentResponse
from backend.tools.visulizzation_sleep_tools import (
    generate_sleep_phases_chart,
    generate_sleep_efficiency_gauge,
    generate_sleep_disturbances_chart,
    generate_heart_rate_timeline
)


def create_visualize_sleep_agent(llm):
    """
    Crea un agente ReAct specializzato nella generazione di grafici del sonno.
    """
    tools = [
        generate_sleep_phases_chart,
        generate_sleep_efficiency_gauge,
        generate_sleep_disturbances_chart,
        generate_heart_rate_timeline
    ]

    system_message = (
        "You are a sleep data visualization specialist. "
        "Your job is to generate the most relevant Plotly charts based on the user's query.\n\n"
        
        "AVAILABLE TOOLS:\n"
        "- generate_sleep_phases_chart: Shows REM, deep, and light sleep distribution (pie chart)\n"
        "- generate_sleep_efficiency_gauge: Shows sleep efficiency percentage 0-100% (gauge indicator)\n"
        "- generate_sleep_disturbances_chart: Shows wake-ups and out-of-bed counts (bar chart)\n"
        "- generate_heart_rate_timeline: Shows heart rate trends during sleep (line chart)\n\n"
        
        "GUIDELINES:\n"
        "1. SPECIFICITY FIRST: If the query mentions specific aspects, generate ONLY related charts\n"
        "   - 'sleep phases'/'REM'/'deep sleep'/'light sleep' → ONLY generate_sleep_phases_chart\n"
        "   - 'efficiency'/'quality'/'performance' → ONLY generate_sleep_efficiency_gauge\n"
        "   - 'wake-ups'/'disturbances'/'interruptions'/'risvegli' → ONLY generate_sleep_disturbances_chart\n"
        "   - 'heart rate'/'cardiac'/'battiti'/'frequenza cardiaca' → ONLY generate_heart_rate_timeline\n\n"
        
        "2. GENERIC QUERIES ('how did they sleep?', 'analyze sleep', 'come ha dormito'):\n"
        "   - Generate overview: efficiency gauge + sleep phases\n"
        "   - Optionally add disturbances chart for complete picture\n\n"
        
        "3. MAXIMUM 3 CHARTS (preferably 1-2 for specific queries)\n\n"
        
        "4. AVOID REDUNDANCY: Don't generate overlapping charts\n\n"
        
        "5. Each tool requires the appropriate data dictionary:\n"
        "   - Sleep tools need sleep_data (from sleep_agent)\n"
        "   - Heart rate tool needs heart_data (from heart_freq_agent)\n\n"
        
        "IMPORTANT: Call each tool with the correct data parameter as a dict/JSON object.\n\n"
        
        "After generating charts, provide a brief summary of what you created and why."
    )

    return create_react_agent(llm, tools=tools, prompt=system_message)


def create_sleep_visualization_node(llm):
    """
    Crea il nodo di visualizzazione che usa l'agente ReAct con tool.
    """

    visualize_sleep_agent = create_visualize_sleep_agent(llm)

    def sleep_visualization_node(state: State) -> Command[Literal["__end__"]]:
        """
        Genera grafici usando un agente ReAct con tool.
        """
        print(f"\n{'=' * 60}")
        print("SLEEP VISUALIZATION NODE - Generating graphs with ReAct agent")
        print(f"{'=' * 60}\n")

        original_question = state.get("original_question", "")
        team_responses = state.get("structured_responses", [])

        # Estrai solo le risposte del team Sleep
        sleep_team_data = None
        for team_resp in team_responses:
            if team_resp["team_name"] == "sleep_team":
                sleep_team_data = team_resp
                break

        if not sleep_team_data:
            print("No sleep team data found")
            return Command(
                goto=END,
                update={
                    "graphs": [],
                    "next": "FINISH"
                }
            )

        # Estrai AgentResponse dal team Sleep
        all_agent_responses: list[AgentResponse] = sleep_team_data["structured_responses"]

        # Identifica agenti con dati validi
        sleep_data = None
        heart_data = None

        for resp in all_agent_responses:
            agent_name = resp["agent_name"]
            data = resp["data"]

            # Salta errori
            if "error" in data:
                print(f"⚠️  Skipping {agent_name} - error in data")
                continue

            if agent_name == "sleep_agent":
                sleep_data = data
                print(f"✓ Sleep data available: {list(data.keys())[:5]}...")
            elif agent_name == "heart_freq_agent":
                heart_data = data
                print(f"✓ Heart rate data available: {list(data.keys())[:3]}...")

        if not sleep_data and not heart_data:
            print("No valid sleep data available for visualization")
            return Command(
                goto=END,
                update={
                    "graphs": [],
                    "next": "FINISH"
                }
            )

        # --- Prepara il prompt per l'agente ReAct ---
        print("\n[Phase 1] Preparing agent prompt...")

        data_info = []
        if sleep_data:
            data_info.append(
                f"sleep_data is available with keys: {list(sleep_data.keys())}"
            )
        else:
            data_info.append("sleep_data is NOT available")

        if heart_data:
            data_info.append(
                f"heart_data is available with keys: {list(heart_data.keys())}"
            )
        else:
            data_info.append("heart_data is NOT available")

        # Serializza i dati per passarli all'agente
        data_context = {
            "sleep_data": sleep_data,
            "heart_data": heart_data
        }

        agent_prompt = f"""USER QUERY: "{original_question}"

AVAILABLE DATA:
{chr(10).join(data_info)}

TASK: 
Analyze the user's query and generate the most relevant charts using the available tools.

DATA TO USE:
{json.dumps(data_context, indent=2, default=str)}

IMPORTANT INSTRUCTIONS:
1. Decide which charts are needed based on the user query
2. Call the appropriate tool(s) with the correct data
3. For sleep-related tools (phases, efficiency, disturbances), use the sleep_data object
4. For heart rate tool, use the heart_data object
5. Generate 1-3 charts that best answer the user's question
6. Provide a brief summary of what you generated

Remember: Be specific - if the query asks about a particular aspect, generate only that chart."""

        # --- Invoca l'agente ReAct ---
        print("\n[Phase 2] Invoking ReAct agent...")

        focused_state = {"messages": [HumanMessage(content=agent_prompt)]}

        try:
            result = visualize_sleep_agent.invoke(focused_state)

            print("\n" + "=" * 60)
            print("AGENT EXECUTION COMPLETED")
            print("=" * 60)

            # --- Estrai i grafici dai ToolMessage ---
            graphs: list[GraphData] = []

            for msg in result["messages"]:
                if isinstance(msg, ToolMessage):
                    # Il contenuto può essere dict o string JSON
                    content = msg.content

                    if isinstance(content, str):
                        try:
                            content = json.loads(content)
                        except json.JSONDecodeError:
                            print(f"⚠️  Could not parse tool message content")
                            continue

                    # Verifica se è un GraphData valido
                    if isinstance(content, dict):
                        if "id" in content and "plotly_json" in content:
                            graphs.append(content)
                            print(f"✓ Extracted graph: {content['id']} - {content['title']}")
                        elif "error" in content:
                            print(f"⚠️  Tool returned error: {content['error']}")

            print(f"\n{'=' * 60}")
            print(f"Generated {len(graphs)} sleep graphs successfully")
            print(f"Graph IDs: {[g['id'] for g in graphs]}")
            print(f"{'=' * 60}\n")

            return Command(
                goto=END,
                update={
                    "graphs": graphs,
                    "next": "FINISH"
                }
            )

        except Exception as e:
            print(f"✗ Error in visualization agent: {str(e)}")
            import traceback
            traceback.print_exc()

            return Command(
                goto=END,
                update={
                    "graphs": [],
                    "next": "FINISH"
                }
            )

    return sleep_visualization_node