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
        "Come ha dormito il soggetto e come ha cucinato 2 nell'ultima settimana?")
    end_time = time.time()



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