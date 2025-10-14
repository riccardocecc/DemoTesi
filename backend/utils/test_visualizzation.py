"""
Script di test per il sistema di visualizzazione.
Esegue query di esempio e salva i grafici generati come HTML.
"""

from backend.graph.builder import build_graph
import json
from pathlib import Path

# Crea directory per output
OUTPUT_DIR = Path("visualization_output")
OUTPUT_DIR.mkdir(exist_ok=True)


def test_visualization(question: str, filename: str):
    """
    Testa il sistema con una domanda specifica e salva i risultati.
    """
    print(f"\n{'=' * 80}")
    print(f"Testing: {question}")
    print(f"{'=' * 80}\n")

    graph = build_graph()

    final_response = None
    structured_responses = []
    graphs = []

    for s in graph.stream(
            {"messages": [("user", question)]},
            {"recursion_limit": 15},
    ):
        for node_name, node_output in s.items():
            if node_output is None:
                continue

            # Cattura structured_responses
            if "structured_responses" in node_output:
                team_responses = node_output["structured_responses"]
                all_agent_responses = []
                for team_resp in team_responses:
                    all_agent_responses.extend(team_resp["structured_responses"])
                structured_responses = all_agent_responses

            # Cattura risposta finale
            if node_name == "correlation_analyzer" and "messages" in node_output:
                for msg in node_output["messages"]:
                    if hasattr(msg, 'name') and msg.name == "correlation_analyzer":
                        final_response = msg.content
                        break

            # Cattura grafici
            if node_name == "visualization_node" and "graphs" in node_output:
                graphs = node_output["graphs"]

    # Salva risultati
    output_file = OUTPUT_DIR / f"{filename}.json"

    result = {
        "question": question,
        "answer": final_response,
        "num_graphs": len(graphs),
        "graph_ids": [g["id"] for g in graphs]
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Results saved to: {output_file}")
    print(f"  Generated {len(graphs)} graphs")

    # Salva grafici come HTML
    for i, graph in enumerate(graphs):
        import plotly.graph_objects as go
        fig = go.Figure(graph["plotly_json"])

        html_file = OUTPUT_DIR / f"{filename}_graph_{i + 1}_{graph['id']}.html"
        fig.write_html(str(html_file))
        print(f"  Graph {i + 1}: {html_file}")

    return final_response, graphs


if __name__ == "__main__":
    # Test 1: Solo sonno
    test_visualization(
        "Come ha dormito il soggetto 2 negli ultimi 7 giorni?",
        "test_sleep_only"
    )

    # Test 2: Sonno + Cucina
    test_visualization(
        "Come ha dormito il soggetto 2 nell'ultima settimana e come ha cucinato?",
        "test_sleep_kitchen"
    )

    # Test 3: Tutti i domini
    test_visualization(
        "Analizza sonno, cucina e mobilità del soggetto 1 nell'ultimo mese",
        "test_all_domains"
    )

    print(f"\n{'=' * 80}")
    print("All tests completed!")
    print(f"Check {OUTPUT_DIR} for results")
    print(f"{'=' * 80}\n")