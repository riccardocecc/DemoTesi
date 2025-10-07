from langgraph.constants import START
from langgraph.graph import StateGraph

from backend.models.state import State
from backend.nodes.mobility_teams.analyze_mobility_node import (
    create_analyze_mobility_agent,
    create_analyze_mobility_node
)
from backend.nodes.mobility_teams.mobility_supervisor import make_supervisor_mobility


def build_mobility_graph(llm_agents, llm_supervisor):

    analyze_mobility_agent = create_analyze_mobility_agent(llm_agents)


    analyze_mobility_node = create_analyze_mobility_node(analyze_mobility_agent)


    mobility_team_supervisor = make_supervisor_mobility(
        llm_supervisor,
        ["analyze_mobility_node"]
    )


    builder = StateGraph(State)


    builder.add_node("mobility_team_supervisor", mobility_team_supervisor)
    builder.add_node("analyze_mobility_node", analyze_mobility_node)


    builder.add_edge(START, "mobility_team_supervisor")


    return builder.compile()