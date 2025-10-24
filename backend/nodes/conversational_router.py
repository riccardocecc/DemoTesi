from typing import Literal
from langgraph.types import Command
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage

from backend.models.state import State

def create_conversational_router(llm):
    """
    Router che delega all'LLM la decisione di routing.
    Se FINISH, risponde direttamente. Altrimenti va al planner.
    """

    system_message = """
        You are a helpful assistant for a health data analysis system.
        Based on the conversation, decide what to do:
        - planner: Route here for data analysis requests (sleep, kitchen, mobility, correlations)
        - FINISH: Route here for greetings, help requests, thanks, or general questions - you will respond directly
        When you choose FINISH, be conversational, helpful, and friendly in your response.
        SE NON SEI A CONOSCENZA dell'id del soggetto, il periodo o il dominio (SONNO, CUCINA, MOBILITA') non andare avanti e chiedi all'utente
        id del soggetto = OBBLIGATORIO
        dominio di analisi = OBBLIGATORIO
        periodo = OPZIONALE 
        Se l'utente chiede altre analisi non contestare mai esegui verso PLANNER
    """

    class RouteSchema(BaseModel):
        """Route to next node"""
        response: str = Field(description="Route response") #per evitare di chiamare due volte LLM
        next: Literal["planner", "FINISH"] = Field(
            description="Next node: 'planner' for analysis, 'FINISH' to respond directly"
        )

    def route(state: State) -> Command[Literal["planner", "__end__"]]:
        """Route based on LLM decision."""
        messages = [{"role": "system", "content": system_message}]

        for msg in state["messages"]:
            messages.append({
                "role": "user" if msg.type == "human" else "assistant",
                "content": msg.content
            })

        decision = llm.with_structured_output(RouteSchema).invoke(messages)
        ai_message = AIMessage(content=decision.response)

        if decision.next == "FINISH":
            return Command(
                goto="__end__",
                update={"messages":[ai_message]}
            )

        # Altrimenti vai al planner
        return Command(
            goto="planner"
        )

    return route