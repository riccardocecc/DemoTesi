from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from uuid import uuid4
from backend.graph.builder import build_graph

app = FastAPI()
serenade_graph = build_graph()


class ChatMessage(BaseModel):
    """Singolo messaggio nella conversazione"""
    role: str
    content: str


class QueryRequest(BaseModel):
    """Richiesta per il chatbot"""
    message: str
    thread_id: Optional[str] = None
    max_iterations: int = 15


class GraphResponse(BaseModel):
    """Rappresenta un singolo grafico"""
    id: str
    title: str
    type: str
    plotly_json: Dict[str, Any]


class QueryResponse(BaseModel):
    """Risposta del chatbot"""
    thread_id: str
    message: str
    structured_responses: List[Dict[str, Any]]
    graphs: Optional[List[GraphResponse]] = None


def run_chat(message: str, thread_id: str, max_iterations: int = 15):
    """
    Esegue il chatbot con gestione dello stato conversazionale.
    """
    assistant_message = None
    structured_responses = []
    graphs = None

    # Configura con thread_id per mantenere la conversazione
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": max_iterations
    }

    # Stream degli aggiornamenti
    for event in serenade_graph.stream(
            {"messages": [("user", message)]},
            config,
            stream_mode="updates"
    ):
        # Ogni event è un dict: {node_name: node_output}
        for node_name, node_output in event.items():


            if node_output is None:
                continue

            # Cattura messaggi AI aggiunti
            if "messages" in node_output:
                for msg in node_output["messages"]:
                    if hasattr(msg, 'type') and msg.type == "ai":
                        assistant_message = msg.content

            # Cattura structured_responses
            if "structured_responses" in node_output:
                team_responses = node_output["structured_responses"]
                print("Team response ", team_responses)
                all_agent_responses = []
                for team_resp in team_responses:
                    if isinstance(team_resp, dict) and "structured_responses" in team_resp:
                        all_agent_responses.extend(team_resp["structured_responses"])
                structured_responses = all_agent_responses


            # Cattura i grafici
            if "graphs" in node_output:
                graphs = node_output["graphs"]

    if assistant_message is None:
        final_state = serenade_graph.get_state(config)

        if final_state and final_state.values and "messages" in final_state.values:
            # Trova l'ultimo messaggio AI
            for msg in reversed(final_state.values["messages"]):
                if hasattr(msg, 'type') and msg.type == "ai":
                    assistant_message = msg.content
                    break

        # Cattura graphs dallo state finale se non catturati prima
        if graphs is None and final_state and final_state.values and "graphs" in final_state.values:
            graphs = final_state.values["graphs"]

        # Se ancora non abbiamo risposta
        if assistant_message is None:
            assistant_message = "I'm sorry, I couldn't generate a response."

    return assistant_message, structured_responses, graphs


@app.post("/chat", response_model=QueryResponse)
async def chat_endpoint(request: QueryRequest):
    """
    Endpoint per il chatbot conversazionale.
    """
    try:
        # Genera un nuovo thread_id se non fornito
        thread_id = request.thread_id or str(uuid4())


        # Esegui il chatbot
        assistant_message, structured_responses, graphs = run_chat(
            request.message,
            thread_id,
            request.max_iterations
        )



        return QueryResponse(
            thread_id=thread_id,
            message=assistant_message,
            structured_responses=structured_responses,
            graphs=graphs or []
        )

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante l'elaborazione: {str(e)}"
        )


@app.post("/chat/new")
async def new_conversation():
    """
    Crea una nuova conversazione e restituisce il thread_id.
    """
    thread_id = str(uuid4())
    return {
        "thread_id": thread_id,
        "message": "Nuova conversazione creata"
    }


@app.get("/chat/{thread_id}/history")
async def get_conversation_history(thread_id: str):
    """
    Recupera la cronologia di una conversazione.
    """
    try:
        config = {"configurable": {"thread_id": thread_id}}
        state = serenade_graph.get_state(config)

        if state is None or not state.values or "messages" not in state.values:
            return {"messages": [], "thread_id": thread_id}

        # Converti i messaggi in un formato serializzabile
        messages = []
        for msg in state.values["messages"]:
            messages.append({
                "role": "user" if msg.type == "human" else "assistant",
                "content": msg.content
            })

        return {
            "thread_id": thread_id,
            "messages": messages
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Errore nel recupero della cronologia: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Endpoint di health check."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", timeout_keep_alive=300,port=8000)