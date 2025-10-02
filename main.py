# This is a sample Python script.
from backend.config.settings import llm
from backend.graph.builder import build_graph



serenade_graph =  build_graph(llm)
def run_demo(question: str, max_iterations: int = 10):
    """
    Esegue la demo del sistema con la domanda fornita.
    """
    print(f"DOMANDA: {question}")
    print("="*60)

    step = 1
    for s in serenade_graph.stream(
        {"messages": [("user", question)]},
        {"recursion_limit": max_iterations},
    ):
        print(f"\nSTEP {step}:")
        for node_name, node_output in s.items():
            if node_output is None:
                print(f"DEBUG: node {node_name} returned None")
                continue

            if node_name == "supervisor":
                next_agent = node_output.get("next", "Unknown")
                print(f"COORDINATORE -> Instradamento verso: {next_agent}")

                if next_agent == "FINISH" and "messages" in node_output:
                    print(f"\nRISPOSTA FINALE DEL SUPERVISOR:")
                    print("-" * 60)
                    for msg in node_output["messages"]:
                        if hasattr(msg, 'name') and msg.name == "supervisor":
                            print(msg.content)
                    print("-" * 60)
            else:
                print(f"AGENTE {node_name.upper()}:")
                # node_output è lo state (dict), non un Command
                structured_responses = node_output.get("structured_responses", [])

                if not structured_responses:
                    print(f"DEBUG: nessuna risposta strutturata per {node_name}")
                else:
                    # structured_responses è una lista di dict TypedDict
                    for response in structured_responses:
                        if isinstance(response, dict):
                            agent_name = response.get("agent_name", "Unknown")
                            data = response.get("data", {})
                            print(f"  Agent: {agent_name}")
                            print(f"  Data: {data}")

        print("-" * 50)
        step += 1


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    run_demo("Come ha dormito e come ha cucinato il soggetto 2 nell'ultima settimana? ")


