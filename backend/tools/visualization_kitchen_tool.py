from __future__ import annotations

from typing import Annotated
from langchain_core.tools import tool
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from backend.models.results import (
    KitchenStatisticsResult,
    KitchenUsagePatternResult,
    KitchenTemperatureAnalysisResult,
    ErrorResult,
)
from backend.models.state import GraphData


@tool
def visualize_kitchen_statistics(
        result: Annotated[KitchenStatisticsResult, "Result from analyze_kitchen_statistics tool"]
) -> GraphData | ErrorResult:
    """
    Crea una visualizzazione per le statistiche delle attività in cucina.

    Genera un grafico combinato che mostra:
    - Numero totale di attività nel periodo
    - Numero di giorni analizzati
    - Statistiche delle attività giornaliere (media, mediana, min, max)

    Args:
        result: Risultato del tool analyze_kitchen_statistics

    Returns:
        GraphData con il grafico Plotly in formato JSON, oppure ErrorResult
    """
    try:
        # Crea subplot con 2 righe e 3 colonne per gli indicator cards
        fig = make_subplots(
            rows=2, cols=3,
            specs=[
                [{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}],
                [{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]
            ],
            vertical_spacing=0.2,
            horizontal_spacing=0.12
        )

        # Card 1: Totale attività
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=result["total_activities"],
                title={
                    "text": "Totale Attività",
                    "font": {"size": 18}
                },
                number={
                    "font": {"size": 50, "color": "#3b82f6"}
                },
                domain={"x": [0, 1], "y": [0, 1]}
            ),
            row=1, col=1
        )


        # Card 3: Media attività per giorno
        activities_stats = result["activities_per_day"]
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=activities_stats["average"],
                title={
                    "text": "Media Attività/Giorno",
                    "font": {"size": 18}
                },
                number={
                    "font": {"size": 50, "color": "#10b981"},
                    "valueformat": ".1f"
                },
                domain={"x": [0, 1], "y": [0, 1]}
            ),
            row=1, col=3
        )

        # Card 5: Min attività per giorno
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=activities_stats["min"],
                title={
                    "text": f"Min Attività/Giorno",
                    "font": {"size": 18}
                },
                number={
                    "font": {"size": 50, "color": "#f59e0b"}
                },
                domain={"x": [0, 1], "y": [0, 1]}
            ),
            row=2, col=2
        )

        # Card 6: Max attività per giorno
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=activities_stats["max"],
                title={
                    "text": f"Max Attività/Giorno",
                    "font": {"size": 18}
                },
                number={
                    "font": {"size": 50, "color": "#ef4444"}
                },
                domain={"x": [0, 1], "y": [0, 1]}
            ),
            row=2, col=3
        )

        # Layout
        fig.update_layout(
            title_font_size=20,
            height=600,
            template="plotly_white",
            margin=dict(t=100, b=50, l=50, r=50)
        )

        graph_data: GraphData = {
            "id": f"kitchen_stats_{result['subject_id']}",
            "title": f"Statistiche Attività Cucina - Soggetto {result['subject_id']}",
            "type": "kitchen_statistics",
            "plotly_json": fig.to_dict()
        }

        return graph_data

    except Exception as e:
        return ErrorResult(error=f"Errore nella visualizzazione statistiche cucina: {str(e)}")

@tool
def visualize_kitchen_usage_pattern(
    result: Annotated[KitchenUsagePatternResult, "Result from analyze_kitchen_usage_pattern tool"]
) -> GraphData | ErrorResult:
    """
    Crea una visualizzazione per i pattern di utilizzo della cucina.
    
    Genera grafici che mostrano:
    - Distribuzione delle attività per fascia oraria (mattina, pranzo, cena)
    - Metriche aggregate (attività totali, attività/giorno, ore di cucina)
    
    Args:
        result: Risultato del tool analyze_kitchen_usage_pattern
        
    Returns:
        GraphData con il grafico Plotly in formato JSON, oppure ErrorResult
    """
    try:
        # Crea subplot con 2 colonne
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(
                "Distribuzione per Fascia Oraria",
                "Metriche Aggregate"
            ),
            specs=[[{"type": "bar"}, {"type": "bar"}]],
            horizontal_spacing=0.15
        )
        
        # Prima colonna: Distribuzione per fascia oraria
        timeslots = ["Mattina", "Pranzo", "Cena"]
        timeslot_keys = ["mattina", "pranzo", "cena"]
        counts = [result["timeslot_distribution"][key]["count"] for key in timeslot_keys]
        percentages = [result["timeslot_distribution"][key]["percentage"] for key in timeslot_keys]
        
        fig.add_trace(
            go.Bar(
                x=timeslots,
                y=counts,
                marker_color=["#fbbf24", "#f97316", "#8b5cf6"],
                text=[f"{count}<br>({pct:.1f}%)" for count, pct in zip(counts, percentages)],
                textposition="auto",
                name="Attività per Fascia"
            ),
            row=1, col=1
        )
        
        # Seconda colonna: Metriche aggregate
        metrics = ["Totale<br>Attività", "Attività<br>al Giorno", "Ore Totali<br>Cucina"]
        values = [
            result["total_activities"],
            result["activities_per_day"],
            result["total_cooking_time_hours"]
        ]
        
        fig.add_trace(
            go.Bar(
                x=metrics,
                y=values,
                marker_color=["#3b82f6", "#10b981", "#ec4899"],
                text=[f"{val:.1f}" for val in values],
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
        
        fig.update_xaxes(title_text="Fascia Oraria", row=1, col=1)
        fig.update_yaxes(title_text="Numero Attività", row=1, col=1)
        
        fig.update_xaxes(title_text="Metrica", row=1, col=2)
        fig.update_yaxes(title_text="Valore", row=1, col=2)
        
        graph_data: GraphData = {
            "id": f"kitchen_pattern_{result['subject_id']}",
            "title": f"Pattern Utilizzo Cucina - Soggetto {result['subject_id']}",
            "type": "kitchen_usage_pattern",
            "plotly_json": fig.to_dict()
        }
        
        return graph_data
        
    except Exception as e:
        return ErrorResult(error=f"Errore nella visualizzazione pattern cucina: {str(e)}")


@tool
def visualize_kitchen_temperature(
    result: Annotated[KitchenTemperatureAnalysisResult, "Result from analyze_kitchen_temperature tool"]
) -> GraphData | ErrorResult:
    """
    Crea una visualizzazione per l'analisi delle temperature in cucina.
    
    Genera un grafico a barre che mostra:
    - Temperatura media
    - Temperatura massima
    - Temperatura minima
    
    Args:
        result: Risultato del tool analyze_kitchen_temperature
        
    Returns:
        GraphData con il grafico Plotly in formato JSON, oppure ErrorResult
    """
    try:
        # Crea grafico a barre semplice
        fig = go.Figure()
        
        temperatures = ["Media", "Massima", "Minima"]
        values = [
            result["avg_temperature"],
            result["max_temperature"],
            result["min_temperature"]
        ]
        colors = ["#3b82f6", "#ef4444", "#10b981"]
        
        fig.add_trace(
            go.Bar(
                x=temperatures,
                y=values,
                marker_color=colors,
                text=[f"{val:.1f}°C" for val in values],
                textposition="auto",
                textfont=dict(size=14, color="white"),
                name="Temperature"
            )
        )
        
        # Layout
        fig.update_layout(
            xaxis_title="Tipo Temperatura",
            yaxis_title="Temperatura (°C)",
            showlegend=False,
            height=500,
            template="plotly_white"
        )
        
        graph_data: GraphData = {
            "id": f"kitchen_temp_{result['subject_id']}",
            "title": f"Analisi Temperature Cucina - Soggetto {result['subject_id']}",
            "type": "kitchen_temperature",
            "plotly_json": fig.to_dict()
        }
        
        return graph_data
        
    except Exception as e:
        return ErrorResult(error=f"Errore nella visualizzazione temperature cucina: {str(e)}")