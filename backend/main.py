from backend.graph.builder import build_graph
import time
import json

graph = build_graph()


def run_demo(question: str, max_iterations: int = 10):
    """
    Esegue la demo e restituisce lo state finale completo.
    """
    result = graph.invoke(
        {"messages": [("user", question)]},
        {"recursion_limit": max_iterations}
    )

    return result


if __name__ == "__main__":
    start_time = time.time()
    final_state = run_demo(
        "Analizzai in quali stanze passa più tempo il soggetto 2 nell'ultima settimana e la fase rem ?")
    end_time = time.time()

    # Stampa tutti i messaggi
    print(f"\n{'=' * 60}")
    print("MESSAGGI DELLO STATE")
    print(f"{'=' * 60}\n")

    messages = final_state.get("messages", [])

    for i, msg in enumerate(messages, 1):
        print(f"\n--- Messaggio {i} ---")
        print(f"Tipo: {type(msg).__name__}")

        # Gestisci diversi tipi di messaggi
        if hasattr(msg, 'type'):
            print(f"Role: {msg.type}")

        if hasattr(msg, 'content'):
            print(f"Content: {msg.content}")

        if hasattr(msg, 'name'):
            print(f"Name: {msg.name}")

        if hasattr(msg, 'tool_calls'):
            print(f"Tool calls: {msg.tool_calls}")

        if hasattr(msg, 'additional_kwargs'):
            print(f"Additional kwargs: {msg.additional_kwargs}")

        # Stampa la rappresentazione completa del messaggio
        print(f"\nOggetto completo:")
        print(json.dumps(msg.dict() if hasattr(msg, 'dict') else str(msg),
                         indent=2, ensure_ascii=False, default=str))

    # Stampa anche i graphs
    graphs = final_state.get("graphs")
    print(f"\n{'=' * 60}")
    print("GRAPHS")
    print(f"{'=' * 60}\n")
    print(json.dumps(graphs, indent=2, ensure_ascii=False, default=str))

    # Stampa altri campi dello state
    print(f"\n{'=' * 60}")
    print("ALTRI CAMPI DELLO STATE")
    print(f"{'=' * 60}\n")

    print(f"Original question: {final_state.get('original_question')}")
    print(f"Next: {final_state.get('next')}")
    print(f"Completed tasks: {final_state.get('completed_tasks')}")
    print(f"\nStructured responses:")
    print(json.dumps(final_state.get('structured_responses'),
                     indent=2, ensure_ascii=False, default=str))

    print(f"\n{'=' * 60}")
    print(f"Tempo totale: {end_time - start_time:.3f}s")
    print(f"{'=' * 60}")