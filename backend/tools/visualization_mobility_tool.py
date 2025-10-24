from __future__ import annotations

from typing import Annotated
from langchain_core.tools import tool
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from backend.models.results import (
    MobilityAnalysisResult,
    ErrorResult,

)
from backend.models.state import GraphData


@tool
def visualize_mobility_patterns(
    result: Annotated[MobilityAnalysisResult, "Result from analyze_mobility_patterns tool"]
) -> GraphData | ErrorResult:
    """
    Crea una visualizzazione per i pattern di mobilità indoor.
    
    Genera un grafico combinato che mostra:
    - Distribuzione percentuale per stanza (pie chart)
    - Metriche aggregate di mobilità (bar chart)
    
    Args:
        result: Risultato del tool analyze_mobility_patterns
        
    Returns:
        GraphData con il grafico Plotly in formato JSON, oppure ErrorResult
    """
    print("RESULT TO GRAPH", result)
    try:
        # Crea subplot con 1 riga e 2 colonne
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(
                "Distribuzione per Stanza (%)",
                "Metriche di Mobilità"
            ),
            specs=[[{"type": "pie"}, {"type": "bar"}]],
            horizontal_spacing=0.15
        )
        
        # Subplot 1: Pie chart distribuzione stanze
        rooms = list(result["room_percentages"].keys())
        percentages = list(result["room_percentages"].values())
        
        # Colori personalizzati per ogni stanza
        room_colors = {
            "cucina": "#f59e0b",
            "soggiorno": "#3b82f6",
            "camera_letto": "#8b5cf6",
            "bagno": "#06b6d4",
            "ingresso": "#10b981"
        }
        colors = [room_colors.get(room, "#6b7280") for room in rooms]
        
        # Capitalizza i nomi delle stanze per visualizzazione
        display_rooms = [room.replace("_", " ").title() for room in rooms]
        
        fig.add_trace(
            go.Pie(
                labels=display_rooms,
                values=percentages,
                marker_colors=colors,
                textinfo="label+percent",
                textposition="auto",
                hovertemplate="<b>%{label}</b><br>%{percent}<br>%{value:.1f}%<extra></extra>"
            ),
            row=1, col=1
        )
        
        # Subplot 2: Bar chart metriche aggregate
        metrics = [
            "Rilevazioni<br>Totali",
            "Rilevazioni<br>al Giorno",
            "Durata Media<br>(minuti)"
        ]
        values = [
            result["total_detections"],
            result["detections_per_day"],
            result["avg_duration_minutes"]
        ]
        metric_colors = ["#3b82f6", "#10b981", "#f59e0b"]
        
        fig.add_trace(
            go.Bar(
                x=metrics,
                y=values,
                marker_color=metric_colors,
                text=[f"{val:.1f}" if isinstance(val, float) else str(val) for val in values],
                textposition="auto",
                name="Metriche"
            ),
            row=1, col=2
        )
        
        # Layout
        fig.update_layout(
            showlegend=False,
            height=500,
            template="plotly_white"
        )
        
        fig.update_xaxes(title_text="Metrica", row=1, col=2)
        fig.update_yaxes(title_text="Valore", row=1, col=2)
        
        graph_data: GraphData = {
            "id": f"mobility_patterns_{result['subject_id']}",
            "title": f"Pattern Mobilità Indoor - Soggetto {result['subject_id']}",
            "type": "mobility_patterns",
            "plotly_json": fig.to_dict()
        }
        
        return graph_data
        
    except Exception as e:
        return ErrorResult(error=f"Errore nella visualizzazione pattern mobilità: {str(e)}")