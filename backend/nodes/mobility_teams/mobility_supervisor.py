from typing import Literal, TypedDict
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.types import Command
from langgraph.graph import END

from backend.models.state import State


def make_supervisor_mobility(llm: BaseChatModel, members: list[str]):
    options = ["FINISH"] + members
    system_prompt = (
        "Sei un supervisore che coordina i task di analisi della mobilità domestica.\n"
        f"Workers disponibili: {members}\n\n"
        "Workers e le loro capacità:\n"
        "- analyze_mobility_node: Analizza i pattern di movimento del soggetto all'interno della casa utilizzando sensori ambientali.\n"
        "REGOLE IMPORTANTI:\n"
        "1. Chiama analyze_mobility_node per mobility metrics\n"
        "2. Only respond with FINISH after ALL relevant workers have completed their tasks\n\n"
        "Analyze the user request and route to the appropriate worker(s)."
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