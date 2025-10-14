from langgraph.constants import START
from langgraph.graph import StateGraph

from backend.models.state import State
from backend.nodes.kitchen_teams.analyze_kitchen_node import (
    create_analyze_kitchen_agent,
    create_analyze_kitchen_node
)
from backend.nodes.kitchen_teams.kitchen_visualization_node import (
    create_kitchen_visualization_node
)
from backend.nodes.kitchen_teams.kitchen_supervisor import make_supervisor_kitchen


def build_kitchen_graph(llm_agents, llm_supervisor):
    """
    Costruisce il grafo del team Kitchen con workflow:
    supervisor → analyze_kitchen_node → [kitchen_visualization_node] → FINISH
    """

    # Crea agente di analisi
    analyze_kitchen_agent = create_analyze_kitchen_agent(llm_agents)
    analyze_kitchen_node = create_analyze_kitchen_node(analyze_kitchen_agent)

    # Crea nodo di visualizzazione
    kitchen_visualization_node = create_kitchen_visualization_node(llm_agents)

    # Crea supervisor (solo data workers in members, visualization gestita separatamente)
    kitchen_team_supervisor = make_supervisor_kitchen(
        llm_supervisor,
        members=["analyze_kitchen_node"]  # Solo data workers
    )

    # Costruisci il grafo
    builder = StateGraph(State)

    # Aggiungi tutti i nodi
    builder.add_node("kitchen_team_supervisor", kitchen_team_supervisor)
    builder.add_node("analyze_kitchen_node", analyze_kitchen_node)
    builder.add_node("kitchen_visualization_node", kitchen_visualization_node)

    # Entry point
    builder.add_edge(START, "kitchen_team_supervisor")

    return builder.compile()