import time
from typing import Annotated

from langchain_core.tools import tool
from langchain_experimental.utilities import PythonREPL
from langgraph.constants import START
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Literal

from langchain_core.messages import BaseMessage, HumanMessage
from langgraph.prebuilt import create_react_agent
from langgraph.graph import MessagesState, END, StateGraph
from langgraph.types import Command

# Configura il modello
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-pro",
    google_api_key="AIzaSyDhex9hSQKtuj7he4aMLJtLiKzV__cajSg",
    temperature=0.7,
    max_retries=0
)

structured_responses = [
    # Team 1: Sleep Team
    {
        "team_name": "sleep_team",
        "original_query": "correlazione fasi del sonno e utilizzo in cucina del soggetto 2 negli ultimi 5 giorni",
        "structured_responses": [
            {
                "task": "Analyze sleep patterns for subject 2 over last 5 days",
                "agent_name": "sleep_agent",
                "data": {
                    "subject_id": 2,
                    "period": "2024-06-24 to 2024-06-28",
                    "num_nights": 5,
                    "rem_sleep": {
                        "avg_minutes": 98.4,
                        "percentage": 23.9
                    },
                    "deep_sleep": {
                        "avg_minutes": 82.3,
                        "percentage": 20.0
                    },
                    "light_sleep": {
                        "avg_minutes": 231.05,
                        "percentage": 56.1
                    },
                    "total_sleep_minutes": 411.75,
                    "sleep_efficiency": 92.48
                }
            }
        ]
    },
    # Team 2: Kitchen Team
    {
        "team_name": "kitchen_team",
        "structured_responses": [
            {
                "task": "Analyze kitchen usage for subject 2 over last 5 days",
                "agent_name": "kitchen_agent",
                "data": {
                    "subject_id": 2,
                    "period": "2024-06-23 to 2024-06-27",
                    "total_activities": 18,
                    "num_days": 5,
                    "duration_minutes": {
                        "average": 12.5,
                        "median": 11.0,
                        "std_dev": 4.2,
                        "min": 5.0,
                        "max": 25.0
                    },
                    "temperature_max": {
                        "average": 85.3,
                        "median": 83.0,
                        "std_dev": 15.8,
                        "min": 60.0,
                        "max": 120.0
                    },
                    "activities_per_day": {
                        "average": 3.6,
                        "median": 4.0,
                        "std_dev": 1.14,
                        "min": 2.0,
                        "max": 5.0
                    }
                }
            }
        ]
    }
]

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

chart_agent = create_react_agent(
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


def chart_node(state: MessagesState) -> Command[Literal[END]]:
    global toDict
    original_query = None
    for team in structured_responses:
        if "original_query" in team:
            original_query = team["original_query"]
            break

    sleep_data = None
    kitchen_data = None

    for team in structured_responses:
        for response in team["structured_responses"]:
            if team["team_name"] == "sleep_team":
                sleep_data = response["data"]
            elif team["team_name"] == "kitchen_team":
                kitchen_data = response["data"]

    # Crea un prompt dettagliato con i dati strutturati
    data_summary = f"""
    
    Original Query: {original_query} 
    SLEEP Data: {sleep_data} 
    KITCHEN Data: {kitchen_data} 
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

    # Aggiungi il messaggio con i dati allo stato
    messages = state["messages"] + [HumanMessage(content=data_summary)]

    # Invoca l'agente
    result = chart_agent.invoke({"messages": messages})
    # Recupera la figura dal REPL
    try:
        # Accedi alla figura creata nel namespace del REPL
        fig = repl.locals.get('fig')
        if fig is not None:
            # Converti la figura in dizionario
            fig_dict = fig.to_dict()
            # Salva in una variabile globale o restituiscila
            global toDict
            toDict = fig_dict
        else:
            toDict = {"error": "Figure not found in REPL namespace"}
    except Exception as e:
        toDict = {"error": f"Failed to convert figure: {str(e)}"}
    # Converti l'ultimo messaggio in HumanMessage
    result["messages"][-1] = HumanMessage(
        content=result["messages"][-1].content, name="chart_generator"
    )

    return Command(
        update={
            "messages": result["messages"],
        },
        goto=END,
    )


workflow = StateGraph(MessagesState)
workflow.add_node("chart_generator", chart_node)

workflow.add_edge(START, "chart_generator")
graph = workflow.compile()

# Esempio di esecuzione
if __name__ == "__main__":
    initial_state = {
        "messages": [HumanMessage(content="Generate a correlation chart for sleep and kitchen data")]
    }
    print("Generating correlation chart...")
    start = time.time()
    result = graph.invoke(initial_state)
    print("Tempo di esecuzione:", time.time() - start, "secondi")

    print("\n\nFigure dictionary keys:", list(toDict.keys()) if toDict else "Empty")
    print("\n\nCheck if 'correlation_chart.html' has been created in the current directory.")