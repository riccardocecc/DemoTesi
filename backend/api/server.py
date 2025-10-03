from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.config.settings import llm
from backend.graph.builder import build_graph

app = FastAPI()
serenade_graph = build_graph(llm)


class QueryRequest(BaseModel):
    question: str
    max_iterations: int = 10


class QueryResponse(BaseModel):
    question: str
    answer: str


def run_demo(question: str, max_iterations: int = 10):
    """
    Esegue la demo del sistema con la domanda fornita e restituisce la risposta finale.
    """
    final_response = None

    for s in serenade_graph.stream(
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

    return final_response


@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    """
    Endpoint che riceve una domanda e restituisce la risposta finale.
    """
    try:
        answer = run_demo(request.question, request.max_iterations)

        if answer is None:
            raise HTTPException(status_code=500, detail="Nessuna risposta finale generata")

        return QueryResponse(question=request.question, answer=answer)

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