from __future__ import annotations

from langchain_core.messages import AnyMessage
from langgraph.graph import MessagesState, add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict, Literal
from typing import Any, Optional, Dict, Annotated
from backend.models.results import (
    SleepStatisticsResult,
    SleepDistributionResult,
    SleepQualityCorrelationResult,
    DailyHeartRateResult,
    KitchenAnalysisResult,
    MobilityAnalysisResult,
    ErrorResult
)


class AgentResponse(TypedDict):
    """Risposta strutturata di un agente specializzato"""
    task: str
    agent_name: Literal["sleep_agent", "kitchen_agent", "mobility_agent", "heart_freq_agent"]
    data: (
        SleepStatisticsResult |
        SleepDistributionResult |
        SleepQualityCorrelationResult |
        DailyHeartRateResult |
        KitchenAnalysisResult |
        MobilityAnalysisResult |
        ErrorResult
    )


class TeamResponse(TypedDict):
    structured_responses: list[AgentResponse]
    team_name: str


class GraphData(TypedDict):
    """Rappresenta un singolo grafico generato"""
    id: str
    title: str
    type: str
    plotly_json: dict[str, Any]

class TeamTask(BaseModel):
    """Singolo task per un team specifico"""
    team: Literal["sleep_team", "kitchen_team", "mobility_team"] = Field(
        description="Nome del team che deve eseguire il task"
    )
    instruction: str = Field(
        description="Istruzione specifica e dettagliata per il team, che include tutti gli aspetti da analizzare nel dominio di competenza"
    )



class ExecutionPlan(BaseModel):
    """Piano di esecuzione completo"""
    subject_id: int | None = Field(
        description="ID del soggetto da analizzare (null se non specificato)"
    )
    period: str = Field(
        description="Periodo da analizzare: 'last_N_days' o 'YYYY-MM-DD,YYYY-MM-DD'",
        default="last_30_days"
    )
    cross_domain: bool = Field(
        default=False,
        description=(
            "True se la query richiede correlazioni/relazioni tra domini diversi. "
            "Quando True, i team di dominio (sleep/kitchen/mobility) non generano i grafici, "
            "e il visualizzation node genera i grafici di correlazione."
        )
    )
    tasks: list[TeamTask] = Field(
        description="Lista ordinata di task da eseguire, uno per ogni team coinvolto"
    )

    def get_next_task(self, completed: set[str]) -> TeamTask | None:
        """Restituisce il prossimo task non completato"""
        for task in self.tasks:
            if task.instruction not in completed:
                return task
        return None

class State(MessagesState):
    """State globale del grafo con risposte strutturate"""
    messages = Annotated[list[AnyMessage], add_messages]
    next: Optional[str] = None
    original_question: Optional[str]
    structured_responses: list[TeamResponse]
    execution_plan: ExecutionPlan
    completed_tasks: set[str]
    graphs: Optional[list[GraphData]]