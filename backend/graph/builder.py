from langgraph.graph import StateGraph, START

from backend.config.settings import llm_query, llm_agents, llm_supervisor
from backend.models.state import State
from backend.nodes.kitchen_node import kitchen_node, create_kitchen_agent
from backend.nodes.mobility_node import mobility_node, create_mobility_agent
from backend.nodes.sleep_node import sleep_node, create_sleep_agent
from backend.nodes.supervisor import make_supervisor_node
from backend.nodes.planner_node import create_planner_node
from backend.nodes.correlation_analyzer_node import create_correlation_analyzer_node  # ← AGGIUNGI


def build_graph():
    """
    Costruisce il grafo completo del sistema multi-agente.

    Returns:
        CompiledGraph: Grafo compilato pronto per l'esecuzione
    """
    # Crea gli agenti
    sleep_agent = create_sleep_agent(llm_agents)
    kitchen_agent = create_kitchen_agent(llm_agents)
    mobility_agent = create_mobility_agent(llm_agents)

    # Crea i nodi
    planner = create_planner_node(llm_query)
    supervisor = make_supervisor_node(llm_supervisor, ["sleep_node", "kitchen_node", "mobility_node"])
    correlation_analyzer = create_correlation_analyzer_node(llm_supervisor)

    # Costruisce il grafo
    builder = StateGraph(State)
    builder.add_node("planner", planner)
    builder.add_node("supervisor", supervisor)
    builder.add_node("sleep_node", sleep_node(sleep_agent))
    builder.add_node("kitchen_node", kitchen_node(kitchen_agent))
    builder.add_node("mobility_node", mobility_node(mobility_agent))
    builder.add_node("correlation_analyzer", correlation_analyzer)  # ← AGGIUNGI

    # Flusso: START → planner → supervisor → [agents] → supervisor → correlation_analyzer → END
    builder.add_edge(START, "planner")

    return builder.compile()