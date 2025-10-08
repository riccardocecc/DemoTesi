from typing import List, Optional, Literal, TypedDict
from langchain_core.language_models.chat_models import BaseChatModel

from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import Command
from langchain_core.messages import HumanMessage, trim_messages

from backend.models.state import State

#al momento è basato su LLM. Si può creare un suprevisor deterministico come il top_supervisor?
#se la query comprende l'utilizzo di diversi agenti sotto la supervisione di questo supervisor forse è
#meglio scomporla piuttosto che inoltrarla ad agenti che non gestiscono domini presenti nella richiesta
def make_supervisor_sleep(llm: BaseChatModel, members: list[str]) -> str:
    options = ["FINISH"] + members
    system_prompt = (
        "You are a supervisor coordinating sleep analysis tasks.\n"
        f"Available workers: {members}\n\n"
        "Workers and their capabilities:\n"
        "- analyze_sleep_node: Analyzes sleep quality, duration, phases (REM, deep, light), awakenings\n"
        "- analyze_heart_node: Analyzes heart rate during sleep and its variations\n\n"
        "IMPORTANT RULES:\n"
        "1. If the task mentions BOTH sleep AND heart/cardiac aspects, you MUST call BOTH workers\n"
        "2. Call analyze_sleep_node first for sleep metrics\n"
        "3. Call analyze_heart_node for cardiac data\n"
        "4. Only respond with FINISH after ALL relevant workers have completed their tasks\n\n"
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

        print("Sleep supervisor goto:", goto)
        print(f"{'=' * 60}")
        return Command(goto=goto, update={"next": goto})

    return supervisor_node