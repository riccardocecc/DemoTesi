from pydantic import BaseModel, Field
from typing import Literal


class GraphIntent(BaseModel):
    """Intent per generare un grafico specifico"""
    template_id: str = Field(
        description="ID del template da utilizzare (es. 'sleep_phases_distribution', 'kitchen_timeslot_distribution')"
    )
    reason: str = Field(
        description="Motivazione per cui questo grafico è rilevante per la query"
    )


class VisualizationPlan(BaseModel):
    """Piano di visualizzazione generato dall'LLM"""
    generate_graphs: bool = Field(
        description="Se True, genera grafici; se False, solo risposta testuale"
    )
    graph_intents: list[GraphIntent] = Field(
        default_factory=list,
        description="Lista degli intent per i grafici da generare (max 4)"
    )
    explanation: str = Field(
        description="Spiegazione breve del piano di visualizzazione"
    )