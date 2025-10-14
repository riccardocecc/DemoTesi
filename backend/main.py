
from backend.graph.builder import build_graph
import time
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
import json

if __name__ == "__main__":
    start_time = time.time()
    final_state = run_demo("Fase REM del soggetto 2 nelle ultime due settimane?")
    end_time = time.time()

    graphs = final_state.get("graphs")

    print(f"\n{'=' * 60}")
    print("GRAPHS")
    print(f"{'=' * 60}\n")

    print(json.dumps(graphs, indent=2, ensure_ascii=False, default=str))

    print(f"\n{'=' * 60}")
    print(f"Tempo: {end_time - start_time:.3f}s")
    print(f"{'=' * 60}")






