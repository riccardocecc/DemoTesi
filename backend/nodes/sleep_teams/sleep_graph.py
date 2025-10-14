from langgraph.constants import START
from langgraph.graph import StateGraph

from backend.models.state import State
from backend.nodes.sleep_teams.analyze_heart_node import create_analyze_heart_agent, create_analyze_heart_node
from backend.nodes.sleep_teams.analyze_sleep_node import create_analyze_sleep_agent, create_analyze_sleep_node
from backend.nodes.sleep_teams.sleep_supervisor import make_supervisor_sleep
from backend.nodes.sleep_teams.sleep_visualizzation_node import create_sleep_visualization_node


def build_sleep_graph(llm_agents, llm_supervisor):
    # Crea agenti
    analyze_sleep_agent = create_analyze_sleep_agent(llm_agents)
    analyze_heart_agent = create_analyze_heart_agent(llm_agents)

    # Crea nodi
    analyze_sleep_node = create_analyze_sleep_node(analyze_sleep_agent)
    analyze_heart_node = create_analyze_heart_node(analyze_heart_agent)
    sleep_visualization_node = create_sleep_visualization_node(llm_agents)


    sleep_team_supervisor = make_supervisor_sleep(
        llm_supervisor,
        ["analyze_sleep_node", "analyze_heart_node"]
    )

    builder = StateGraph(State)


    builder.add_node("sleep_team_supervisor", sleep_team_supervisor)
    builder.add_node("analyze_sleep_node", analyze_sleep_node)
    builder.add_node("analyze_heart_node", analyze_heart_node)
    builder.add_node("sleep_visualization", sleep_visualization_node)


    builder.add_edge(START, "sleep_team_supervisor")



    return builder.compile()


