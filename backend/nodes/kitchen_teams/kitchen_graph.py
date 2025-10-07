from langgraph.constants import START
from langgraph.graph import StateGraph

from backend.models.state import State
from backend.nodes.kitchen_teams.analyze_kitchen_node import (
    create_analyze_kitchen_agent,
    create_analyze_kitchen_node
)
from backend.nodes.kitchen_teams.kitchen_supervisor import make_supervisor_kitchen


def build_kitchen_graph(llm_agents, llm_supervisor):

    analyze_kitchen_agent = create_analyze_kitchen_agent(llm_agents)


    analyze_kitchen_node = create_analyze_kitchen_node(analyze_kitchen_agent)


    kitchen_team_supervisor = make_supervisor_kitchen(
        llm_supervisor,
        ["analyze_kitchen_node"]
    )


    builder = StateGraph(State)


    builder.add_node("kitchen_team_supervisor", kitchen_team_supervisor)
    builder.add_node("analyze_kitchen_node", analyze_kitchen_node)


    builder.add_edge(START, "kitchen_team_supervisor")

    return builder.compile()