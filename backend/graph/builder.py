
from langgraph.graph import StateGraph, START


from backend.models.state import State
from backend.nodes.kitchen_node import kitchen_node, create_kitchen_agent
from backend.nodes.mobility_node import mobility_node, create_mobility_agent
from backend.nodes.sleep_node import sleep_node, create_sleep_agent
from backend.nodes.supervisor import make_supervisor_node


def build_graph(llm):
    """
    Costruisce il grafo completo del sistema multi-agente.

    Returns:
        CompiledGraph: Grafo compilato pronto per l'esecuzione
    """
    sleep_agent = create_sleep_agent(llm)
    kitchen_agent = create_kitchen_agent(llm)
    mobility_agent = create_mobility_agent(llm)

    supervisor = make_supervisor_node(llm, ["sleep_node", "kitchen_node", "mobility_node"])

    # Crea il supervisore

    # Costruisce il grafo
    builder = StateGraph(State)
    builder.add_node("supervisor", supervisor)
    builder.add_node("sleep_node", sleep_node(sleep_agent))
    builder.add_node("kitchen_node", kitchen_node(kitchen_agent))
    builder.add_node("mobility_node", mobility_node(mobility_agent))

    # Edge iniziale
    builder.add_edge(START, "supervisor")

    return builder.compile()