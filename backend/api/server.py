from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from backend.graph.builder import build_graph

app = FastAPI()
serenade_graph = build_graph()


class QueryRequest(BaseModel):
    question: str
    max_iterations: int = 10


class GraphResponse(BaseModel):
    """Rappresenta un singolo grafico"""
    id: str
    title: str
    type: str
    plotly_json: Dict[str, Any]


class QueryResponse(BaseModel):
    question: str
    answer: str
    structured_responses: List[Dict[str, Any]]
    graphs: Optional[List[GraphResponse]] = None  # ← NUOVO CAMPO


def run_demo(question: str, max_iterations: int = 10):
    """
    Esegue la demo del sistema con la domanda fornita e restituisce la risposta finale,
    le risposte strutturate e i grafici generati.
    """
    final_response = None
    structured_responses = []
    graphs = []  # ← NUOVO

    for s in serenade_graph.stream(
            {"messages": [("user", question)]},
            {"recursion_limit": max_iterations},
    ):
        for node_name, node_output in s.items():

            if node_output is None:
                continue

            # Cattura structured_responses dallo state e "spacchetta" i TeamResponse
            if "structured_responses" in node_output:
                team_responses = node_output["structured_responses"]
                # Estrai tutti gli AgentResponse da tutti i TeamResponse
                all_agent_responses = []
                for team_resp in team_responses:
                    all_agent_responses.extend(team_resp["structured_responses"])
                structured_responses = all_agent_responses

            # Cattura la risposta finale
            if node_name == "correlation_analyzer" and "messages" in node_output:
                for msg in node_output["messages"]:
                    if hasattr(msg, 'name'):
                        if msg.name == "correlation_analyzer":
                            final_response = msg.content
                            break

            # ← NUOVO: Cattura i grafici
            if node_name == "visualization_node" and "graphs" in node_output:
                graphs = node_output["graphs"]

    return final_response, structured_responses, graphs  # ← MODIFICATO


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    Endpoint che riceve una domanda e restituisce la risposta finale,
    le risposte strutturate degli agenti e i grafici generati.
    """
    try:
        answer, structured_responses, graphs = run_demo(
            request.question,
            request.max_iterations
        )

        if answer is None:
            raise HTTPException(status_code=500, detail="Nessuna risposta finale generata")

        return QueryResponse(
            question=request.question,
            answer=answer,
            structured_responses=structured_responses,
            graphs=graphs  # ← NUOVO
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore durante l'elaborazione: {str(e)}")


@app.get("/health")
async def health_check():
    """
    Endpoint di health check.
    """
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)