from typing import Annotated, Literal
import json

from langchain_experimental.utilities import PythonREPL
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.prebuilt import create_react_agent
from langgraph.types import Command

from backend.models.state import State, GraphData

repl = PythonREPL()


@tool
def python_repl_tool(
        code: Annotated[str, "The python code to execute to generate your chart."],
):
    """Use this to execute python code. If you want to see the output of a value,
    you should print it out with `print(...)`. This is visible to the user."""
    try:
        result = repl.run(code)
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"
    result_str = f"Successfully executed:\n```python\n{code}\n```\nStdout: {result}"
    return (
            result_str + "\n\nIf you have completed all tasks, respond with FINAL ANSWER."
    )

def create_graph_generator_agent(llm):
    return create_react_agent(
        llm,
        [python_repl_tool],
        prompt=(
            "You are a chart generation expert. You MUST use the python_repl_tool to create visualizations. "
            "Create professional and informative visualizations based on the data provided. "
            "\n\n"
            "CRITICAL REQUIREMENTS:\n"
            "- You MUST use ONLY Plotly for visualization (plotly.graph_objects or plotly.express)\n"
            "- DO NOT use matplotlib, seaborn, or any other plotting library\n"
            "- Save the output as an HTML file using fig.write_html('correlation_chart.html')\n"
            "- Your code MUST start with imports like:\n"
            "  from plotly.subplots import make_subplots\n"
            "  import plotly.graph_objects as go\n"
            "- DO NOT import matplotlib or plt\n"
            "IMPORTANT: you must use the best combination of chart (DONT USE GAUGE CHART) to best represent the user's query"
            "\n"
            "Make sure charts are clear, well-labeled, and visually appealing. "
            "IMPORTANT: You must call the python_repl_tool to execute the code that generates the chart. "
            "After generating the chart, respond with FINAL ANSWER."
        ),
    )


def create_graph_generator_node(graph_generator_agent):
    def _node_(state: State) -> Command[Literal["correlation_analyzer"]]:
        execution_plan = state.get("execution_plan")
        if execution_plan and execution_plan.cross_domain:
            structured_responses = state.get("structured_responses", [])

            # Costruisci original_query dai task
            original_query_parts = []
            for task in execution_plan.tasks:
                original_query_parts.append(f"{task.team}: {task.instruction}")

            original_query = " | ".join(original_query_parts)

            sleep_data = None
            kitchen_data = None
            mobility_data = None
            for team in structured_responses:
                for response in team["structured_responses"]:
                    if team["team_name"] == "sleep_team":
                        sleep_data = response["data"]
                    elif team["team_name"] == "kitchen_team":
                        kitchen_data = response["data"]
                    elif team["team_name"] == "mobility_team":
                        mobility_data = response["data"]


            data_summary = f"""
                Original Query: {original_query} 
                SLEEP Data: {sleep_data} 
                KITCHEN Data: {kitchen_data} 
                MOBILITY Data: {mobility_data} 
                
                Use plotly.graph_objects or plotly.express and create a comprehensive visualization. Make sure to:
                - Import plotly.graph_objects as go and/or import plotly.express as px
                - Import plotly.subplots (from plotly.subplots import make_subplots)
                - Create a figure with subplots (e.g., fig = make_subplots(rows=2, cols=2, ...))
                - Add proper titles and labels
                - Configure layout with fig.update_layout()
                - Save the figure as 'correlation_chart.html' using fig.write_html('correlation_chart.html')
                - Display with fig.show()
                
                IMPORTANT: you must use the best combination of chart (DONT USE GAUGE CHART) to best represent the Original Query
                
                Start by calling the python_repl_tool with the complete code to generate the interactive chart.
            """

            messages = state["messages"] + [HumanMessage(content=data_summary)]

            # Invoca l'agente
            result = graph_generator_agent.invoke({"messages": messages})

            toDict = {}
            try:
                # Accedi alla figura creata nel namespace del REPL
                fig = repl.locals.get('fig')
                if fig is not None:
                    toDict = fig.to_dict()
                else:
                    toDict = {"error": "Figure not found in REPL namespace"}
            except Exception as e:
                toDict = {"error": f"Failed to convert figure: {str(e)}"}

            output_messages = result["messages"]
            if output_messages:
                output_messages[-1] = AIMessage(
                    content=output_messages[-1].content,
                    name="graph_generator"
                )

            print("ToDictGraph", toDict)

            graph_data = GraphData(
                id="correlation_chart",
                title=f"Correlation Chart: {original_query}",
                type="plotly",
                plotly_json=toDict
            )

            existing_graphs = state.get("graphs", [])
            updated_graphs = existing_graphs + [graph_data]

            return Command(
                update={
                    "graphs": updated_graphs,
                    "messages": output_messages,
                },
                goto="correlation_analyzer"
            )

        return Command(
            goto="correlation_analyzer",
        )

    return _node_