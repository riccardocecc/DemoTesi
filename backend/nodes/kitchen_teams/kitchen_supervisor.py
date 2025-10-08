from typing import Literal, TypedDict
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.types import Command
from langgraph.graph import END

from backend.models.state import State


def make_supervisor_kitchen(llm: BaseChatModel, members: list[str]):
    options = ["FINISH"] + members
    system_prompt = (
        "Sei un supervisore che coordina i task di analisi della cucina.\n"
        f"Workers disponibili: {members}\n\n"
        "Workers e le loro capacità:\n"
        "- kitchen_agent: Analizza l'attività in cucina (presenza, durata, frequenza, orari di utilizzo)\n\n"
        "REGOLE IMPORTANTI:\n"
        "1. Assegna il task al kitchen_agent quando l'utente chiede informazioni sull'uso della cucina\n"
        "2. Se il task richiede analisi su più aspetti (es. durata E orari), il kitchen_agent può gestirli in una singola chiamata\n"
        "3. Rispondi con FINISH solo quando tutti i task richiesti sono stati completati\n"
        "4. Se un worker risponde con errore, puoi riassegnare il task con istruzioni più chiare (max 2 retry)\n\n"
        "Analizza la richiesta dell'utente e instrada al worker appropriato."
    )

    class Router(TypedDict):
        """Worker to route to next. If no workers needed, route to FINISH."""
        next: Literal[*options]

    def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:
        """An LLM-based router."""
        messages = [
            {"role": "system", "content": system_prompt},
        ] + state["messages"]
        response = llm.with_structured_output(Router).invoke(messages)
        goto = response["next"]
        if goto == "FINISH":
            goto = END

        return Command(goto=goto, update={"next": goto})

    return supervisor_node