from __future__ import annotations

from langgraph.graph import MessagesState
from typing_extensions import TypedDict, Literal
from typing import Any
from backend.models.results import SleepAnalysisResult, KitchenAnalysisResult,MobilityAnalysisResult,ErrorResult




class AgentResponse(TypedDict):
    """Risposta strutturata di un agente specializzato"""
    task: str
    agent_name: Literal["sleep_agent", "kitchen_agent", "mobility_agent"]
    data: SleepAnalysisResult | KitchenAnalysisResult | MobilityAnalysisResult | ErrorResult


class SupervisorRouter(TypedDict):
    """Worker to route to next. If no workers needed route to FINISH."""
    next: Literal["sleep_node", "kitchen_node", "mobility_node", "FINISH"]
    task: str


class State(MessagesState):
    """State globale del grafo con risposte strutturate"""
    next: str
    original_question: str
    structured_responses: list[AgentResponse]
    execution_plan: Any # ← AGGIUNGI
    completed_tasks: set[str]  # ← AGGIUNGI (opzionale ma utile)