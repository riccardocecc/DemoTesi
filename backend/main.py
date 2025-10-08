
from backend.graph.builder import build_graph

graph = build_graph()

def run_demo(question: str, max_iterations: int = 10):
    """
    Esegue la demo del sistema con la domanda fornita e restituisce la risposta finale.
    """
    final_response = None

    for s in graph.stream(
            {"messages": [("user", question)]},
            {"recursion_limit": max_iterations},
    ):
        for node_name, node_output in s.items():
            if node_output is None:
                continue

            # Cattura la risposta finale dal correlation_analyzer
            if node_name == "correlation_analyzer" and "messages" in node_output:
                for msg in node_output["messages"]:
                    if hasattr(msg, 'name') and msg.name == "correlation_analyzer":
                        final_response = msg.content
                        break

    return final_response

if __name__ == "__main__":
    # Salva il grafo come immagine PNG
    #png_data = graph.get_graph().draw_mermaid_png()

    #with open("total_graph.png", "wb") as f:
     #   f.write(png_data)

    #print("Grafo salvato come 'grafo_langgraph.png'")
    run_demo("Come ha dormito il soggetto 2 nell'ultima settimana e come si è mosso?")