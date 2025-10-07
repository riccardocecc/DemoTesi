from __future__ import annotations

from langgraph.graph import MessagesState
from typing_extensions import TypedDict, Literal
from typing import Any
from backend.models.results import SleepAnalysisResult, KitchenAnalysisResult,MobilityAnalysisResult,ErrorResult


class AgentResponse(TypedDict):
    """Risposta strutturata di un agente specializzato"""
    task: str
    agent_name: Literal["sleep_agent", "kitchen_agent", "mobility_agent","heart_freq_agent"]
    data: SleepAnalysisResult | KitchenAnalysisResult | MobilityAnalysisResult | ErrorResult

class TeamResponse(TypedDict):
    structured_responses: list[AgentResponse]
    team_name: str

class State(MessagesState):
    """State globale del grafo con risposte strutturate"""
    next: str
    original_question: str
    structured_responses: list[TeamResponse]
    execution_plan: Any
    completed_tasks: set[str]

