from langgraph.constants import START
from langgraph.graph import StateGraph

from backend.models.state import State
from backend.nodes.mobility_teams.analyze_mobility_node import (
    create_analyze_mobility_agent,
    create_analyze_mobility_node
)
from backend.nodes.mobility_teams.mobility_visualization_node import (
    create_mobility_visualization_node
)
from backend.nodes.mobility_teams.mobility_supervisor import make_supervisor_mobility


def build_mobility_graph(llm_agents, llm_supervisor):
    """
    Costruisce il grafo del team Mobility con workflow:
    supervisor → analyze_mobility_node → [mobility_visualization_node] → FINISH
    """

    # Crea agente di analisi
    analyze_mobility_agent = create_analyze_mobility_agent(llm_agents)
    analyze_mobility_node = create_analyze_mobility_node(analyze_mobility_agent)

    # Crea nodo di visualizzazione
    mobility_visualization_node = create_mobility_visualization_node(llm_agents)

    # Crea supervisor (solo data workers in members, visualization gestita separatamente)
    mobility_team_supervisor = make_supervisor_mobility(
        llm_supervisor,
        members=["analyze_mobility_node"]  # Solo data workers
    )

    # Costruisci il grafo
    builder = StateGraph(State)

    # Aggiungi tutti i nodi
    builder.add_node("mobility_team_supervisor", mobility_team_supervisor)
    builder.add_node("analyze_mobility_node", analyze_mobility_node)
    builder.add_node("mobility_visualization_node", mobility_visualization_node)

    # Entry point
    builder.add_edge(START, "mobility_team_supervisor")

    return builder.compile()