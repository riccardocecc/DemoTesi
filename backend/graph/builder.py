from langgraph.graph import StateGraph, START

from backend.config.settings import llm_agents, llm_supervisor, llm_query
from backend.models.state import State
from backend.nodes.kitchen_teams.kitchen_graph import build_kitchen_graph
from backend.nodes.mobility_teams.mobility_graph import build_mobility_graph
from backend.nodes.sleep_teams.sleep_graph import build_sleep_graph
from backend.nodes.supervisor import make_supervisor_node
from backend.nodes.planner_node import create_planner_node
from backend.nodes.correlation_analyzer_node import create_correlation_analyzer_node
from backend.nodes.visualization_node import create_visualization_node  # ← NUOVO IMPORT


def build_graph():
    """
    Costruisce il grafo completo del sistema multi-agente con teams

    Architettura:
    - Planner: analizza la query e crea l'execution plan
    - Supervisor: coordina i team in base al piano
    - Teams (subgraphs): sleep_team, kitchen_team, mobility_team
    - Correlation Analyzer: sintetizza i risultati finali
    - Visualization Node: genera grafici Plotly dai dati strutturati  ← NUOVO
    """

    sleep_team_graph = build_sleep_graph(llm_agents, llm_supervisor)
    kitchen_team_graph = build_kitchen_graph(llm_agents, llm_supervisor)
    mobility_team_graph = build_mobility_graph(llm_agents, llm_supervisor)

    planner = create_planner_node(llm_query)
    supervisor = make_supervisor_node(
        llm_supervisor,
        teams=["sleep_team", "kitchen_team", "mobility_team"]
    )
    correlation_analyzer = create_correlation_analyzer_node(llm_supervisor)


    builder = StateGraph(State)

    # nodi di coordinamento
    builder.add_node("planner", planner)
    builder.add_node("supervisor", supervisor)
    builder.add_node("correlation_analyzer", correlation_analyzer)


    # subgraphs come nodi
    builder.add_node("sleep_team", sleep_team_graph)
    builder.add_node("kitchen_team", kitchen_team_graph)
    builder.add_node("mobility_team", mobility_team_graph)

    # edge da team a top supervisor
    builder.add_edge("sleep_team", "supervisor")
    builder.add_edge("kitchen_team", "supervisor")
    builder.add_edge("mobility_team", "supervisor")

    # estrae domini da query e assegna teams. Non va nel dettaglio
    builder.add_edge(START, "planner")

    return builder.compile()