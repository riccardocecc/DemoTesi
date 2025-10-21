import uuid
from backend.graph.builder import build_graph
import time

graph = build_graph()


def run_demo(question: str, max_iterations: int = 10):
    """
    Esegue la demo e restituisce lo state finale completo.
    """
    thread_id = str(uuid.uuid4())
    config = {
        "configurable": {
            "passenger_id": "3442 587242",
            "thread_id": thread_id,
        }
    }
    result = graph.invoke(
        {"messages": [("user", question)]},
        config=config
    )
    return result


def run_demo_2():
    """Interactive chatbot loop for Swiss Airlines Assistant."""
    thread_id = str(uuid.uuid4())
    config = {
        "configurable": {

            "thread_id": thread_id,

        }
    }

    print("Swiss Airlines Assistant avviato! ✈️")
    print("Digita 'exit', 'quit', 'bye' o 'q' per uscire.\n")

    while True:
        user_input = input("Tu: ").strip()

        if user_input.lower() in ['exit', 'quit', 'bye', 'q']:
            print("Grazie per aver usato Swiss Airlines Assistant. Buon viaggio! ✈️")
            break

        if not user_input:
            continue

        try:
            # ✅ Usa stream() correttamente
            print("\nAssistant: ", end="", flush=True)

            final_message = None
            for event in graph.stream(
                    {"messages": [("user", user_input)]},
                    config=config,
                    stream_mode="values"  # Importante!
            ):
                # Ogni event è lo stato completo
                if "messages" in event and event["messages"]:
                    # Prendi l'ultimo messaggio
                    last_msg = event["messages"][-1]
                    if hasattr(last_msg, 'content') and last_msg.type == "ai":
                        final_message = last_msg.content

            # Mostra la risposta finale
            if final_message:
                print(final_message)
            print()

        except Exception as e:
            print(f"\n❌ Errore: {e}\n")

if __name__ == "__main__":
    start_time = time.time()
    run_demo_2()
    end_time = time.time()

    print(f"\n{'=' * 60}")
    print(f"Tempo totale: {end_time - start_time:.2f}s")
    print(f"{'=' * 60}")