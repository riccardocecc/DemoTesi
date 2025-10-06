
from backend.graph.builder import build_graph

graph = build_graph()

def run_demo(question: str, max_iterations: int = 10):
    """
    Esegue la demo del sistema con la domanda fornita e restituisce la risposta finale.
    """
    print(f"DOMANDA: {question}")
    print("=" * 60)

    final_response = None

    for s in graph.stream(
            {"messages": [("user", question)]},
            {"recursion_limit": max_iterations},
    ):
        for node_name, node_output in s.items():
            if node_output is None:
                continue

            if node_name == "supervisor":
                next_agent = node_output.get("next", "Unknown")

                if next_agent == "FINISH" and "messages" in node_output:
                    for msg in node_output["messages"]:
                        if hasattr(msg, 'name') and msg.name == "supervisor":
                            final_response = msg.content
                            break

    if final_response:
        print(f"\nRISPOSTA FINALE:")
        print("-" * 60)
        print(final_response)
        print("-" * 60)
    else:
        print("\nNessuna risposta finale trovata.")

    return final_response


if __name__ == "__main__":
    # Salva l'immagine su file
    #png_data = graph.get_graph().draw_mermaid_png()
    #with open("graph.png", "wb") as f:
     #   f.write(png_data)s

    #print("Grafo salvato come 'graph.png'")

    # Opzionalmente, apri l'immagine automaticamente
    #import os
    #import platform

    #if platform.system() == 'Darwin':  # macOS
     #   os.system('open grafo_serenade.png')
    #elif platform.system() == 'Windows':
     ##   os.system('start grafo_serenade.png')
    #else:  # Linux
       # os.system('xdg-open grafo_serenade.png')
    run_demo("Come ha dormito e come ha cucinato il soggetto 2 nell'ultima settimana?")