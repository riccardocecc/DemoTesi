from __future__ import annotations

from typing import Annotated
from langchain_core.tools import tool
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from backend.models.results import (
    SleepStatisticsResult,
    SleepDistributionResult,
    SleepQualityCorrelationResult,
    DailyHeartRateResult,
    ErrorResult,
)
from backend.models.state import GraphData


@tool
def visualize_sleep_statistics(
    result: Annotated[SleepStatisticsResult, "Result from analyze_sleep_statistics tool"]
) -> GraphData | ErrorResult:
    """
    Crea una visualizzazione per le statistiche del sonno.
    
    Genera un grafico combinato che mostra:
    - Numero totale di notti analizzate
    - Statistiche tempo totale di sonno (media, mediana, min, max)
    - Statistiche risvegli notturni
    - Statistiche uscite dal letto
    
    Args:
        result: Risultato del tool analyze_sleep_statistics
        
    Returns:
        GraphData con il grafico Plotly in formato JSON, oppure ErrorResult
    """
    try:
        # Crea subplot con 2 righe e 2 colonne
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Tempo Totale di Sonno (minuti)",
                "Risvegli Notturni",
                "Uscite dal Letto",
                f"Notti Analizzate: {result['num_nights']}"
            ),
            specs=[
                [{"type": "bar"}, {"type": "bar"}],
                [{"type": "bar"}, {"type": "indicator"}]
            ],
            vertical_spacing=0.15,
            horizontal_spacing=0.12
        )
        
        # Subplot 1: Tempo totale di sonno
        sleep_time_stats = result["total_sleep_time"]
        fig.add_trace(
            go.Bar(
                x=["Media", "Mediana", "Min", "Max"],
                y=[
                    sleep_time_stats["average"],
                    sleep_time_stats["median"],
                    sleep_time_stats["min"],
                    sleep_time_stats["max"]
                ],
                marker_color=["#3b82f6", "#06b6d4", "#f59e0b", "#ef4444"],
                text=[
                    f"{sleep_time_stats['average']:.0f}",
                    f"{sleep_time_stats['median']:.0f}",
                    f"{sleep_time_stats['min']:.0f}",
                    f"{sleep_time_stats['max']:.0f}"
                ],
                textposition="auto",
                name="Tempo Sonno"
            ),
            row=1, col=1
        )
        
        # Subplot 2: Risvegli notturni
        wakeup_stats = result["wakeup_count"]
        fig.add_trace(
            go.Bar(
                x=["Media", "Mediana", "Min", "Max"],
                y=[
                    wakeup_stats["average"],
                    wakeup_stats["median"],
                    wakeup_stats["min"],
                    wakeup_stats["max"]
                ],
                marker_color=["#8b5cf6", "#a78bfa", "#c4b5fd", "#ddd6fe"],
                text=[
                    f"{wakeup_stats['average']:.1f}",
                    f"{wakeup_stats['median']:.1f}",
                    f"{wakeup_stats['min']:.0f}",
                    f"{wakeup_stats['max']:.0f}"
                ],
                textposition="auto",
                name="Risvegli"
            ),
            row=1, col=2
        )
        
        # Subplot 3: Uscite dal letto
        out_of_bed_stats = result["out_of_bed_count"]
        fig.add_trace(
            go.Bar(
                x=["Media", "Mediana", "Min", "Max"],
                y=[
                    out_of_bed_stats["average"],
                    out_of_bed_stats["median"],
                    out_of_bed_stats["min"],
                    out_of_bed_stats["max"]
                ],
                marker_color=["#10b981", "#34d399", "#6ee7b7", "#a7f3d0"],
                text=[
                    f"{out_of_bed_stats['average']:.1f}",
                    f"{out_of_bed_stats['median']:.1f}",
                    f"{out_of_bed_stats['min']:.0f}",
                    f"{out_of_bed_stats['max']:.0f}"
                ],
                textposition="auto",
                name="Uscite"
            ),
            row=2, col=1
        )
        
        # Subplot 4: Indicatore numero notti
        fig.add_trace(
            go.Indicator(
                mode="number",
                value=result["num_nights"],
                title={"text": "Notti Totali"},
                number={"font": {"size": 60, "color": "#3b82f6"}},
                domain={"x": [0, 1], "y": [0, 1]}
            ),
            row=2, col=2
        )
        
        # Layout
        fig.update_layout(
            title_text=f"Statistiche Sonno - Soggetto {result['subject_id']}<br><sub>Periodo: {result['period']}</sub>",
            title_font_size=18,
            showlegend=False,
            height=700,
            template="plotly_white"
        )
        
        # Aggiorna assi
        fig.update_xaxes(title_text="Statistiche", row=1, col=1)
        fig.update_yaxes(title_text="Minuti", row=1, col=1)
        
        fig.update_xaxes(title_text="Statistiche", row=1, col=2)
        fig.update_yaxes(title_text="Numero", row=1, col=2)
        
        fig.update_xaxes(title_text="Statistiche", row=2, col=1)
        fig.update_yaxes(title_text="Numero", row=2, col=1)
        
        graph_data: GraphData = {
            "id": f"sleep_stats_{result['subject_id']}",
            "title": f"Statistiche Sonno - Soggetto {result['subject_id']}",
            "type": "sleep_statistics",
            "plotly_json": fig.to_dict()
        }
        
        return graph_data
        
    except Exception as e:
        return ErrorResult(error=f"Errore nella visualizzazione statistiche sonno: {str(e)}")


@tool
def visualize_sleep_distribution(
    result: Annotated[SleepDistributionResult, "Result from analyze_sleep_distribution tool"]
) -> GraphData | ErrorResult:
    """
    Crea una visualizzazione per la distribuzione delle fasi del sonno.
    
    Genera grafici che mostrano:
    - Distribuzione percentuale delle fasi (REM, profondo, leggero) tramite pie chart
    - Durata media in minuti per ogni fase tramite bar chart
    - Tempo totale di sonno
    
    Args:
        result: Risultato del tool analyze_sleep_distribution
        
    Returns:
        GraphData con il grafico Plotly in formato JSON, oppure ErrorResult
    """
    try:
        # Crea subplot con 1 riga e 2 colonne
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=(
                "Distribuzione Percentuale Fasi",
                "Durata Media per Fase (minuti)"
            ),
            specs=[[{"type": "pie"}, {"type": "bar"}]],
            horizontal_spacing=0.15
        )
        
        # Dati delle fasi
        phases = ["REM", "Profondo", "Leggero"]
        percentages = [
            result["rem_sleep"]["percentage"],
            result["deep_sleep"]["percentage"],
            result["light_sleep"]["percentage"]
        ]
        minutes = [
            result["rem_sleep"]["avg_minutes"],
            result["deep_sleep"]["avg_minutes"],
            result["light_sleep"]["avg_minutes"]
        ]
        colors = ["#3b82f6", "#8b5cf6", "#06b6d4"]
        
        # Subplot 1: Pie chart percentuali
        fig.add_trace(
            go.Pie(
                labels=phases,
                values=percentages,
                marker_colors=colors,
                textinfo="label+percent",
                textposition="auto",
                hovertemplate="<b>%{label}</b><br>%{percent}<br>%{value:.1f}%<extra></extra>"
            ),
            row=1, col=1
        )
        
        # Subplot 2: Bar chart minuti
        fig.add_trace(
            go.Bar(
                x=phases,
                y=minutes,
                marker_color=colors,
                text=[f"{min:.0f}" for min in minutes],
                textposition="auto",
                name="Durata"
            ),
            row=1, col=2
        )
        
        # Layout
        fig.update_layout(
            title_text=f"Distribuzione Fasi del Sonno - Soggetto {result['subject_id']}<br><sub>Periodo: {result['period']} | Notti: {result['num_nights']} | Tempo Totale Medio: {result['total_sleep_minutes']:.0f} min</sub>",
            title_font_size=18,
            showlegend=False,
            height=500,
            template="plotly_white"
        )
        
        fig.update_xaxes(title_text="Fase del Sonno", row=1, col=2)
        fig.update_yaxes(title_text="Minuti", row=1, col=2)
        
        graph_data: GraphData = {
            "id": f"sleep_distribution_{result['subject_id']}",
            "title": f"Distribuzione Fasi Sonno - Soggetto {result['subject_id']}",
            "type": "sleep_distribution",
            "plotly_json": fig.to_dict()
        }
        
        return graph_data
        
    except Exception as e:
        return ErrorResult(error=f"Errore nella visualizzazione distribuzione sonno: {str(e)}")


@tool
def visualize_sleep_quality_correlation(
    result: Annotated[SleepQualityCorrelationResult, "Result from analyze_sleep_quality_correlation tool"]
) -> GraphData | ErrorResult:
    """
    Crea una visualizzazione per le correlazioni tra interruzioni e qualità del sonno.
    
    Genera un grafico a barre che mostra le correlazioni:
    - Risvegli vs Tempo di sonno
    - Uscite dal letto vs Tempo di sonno
    
    Coefficienti di correlazione variano da -1 a +1:
    - Negativo: relazione inversa (più interruzioni, meno qualità)
    - Positivo: relazione diretta
    - Vicino a 0: nessuna relazione
    
    Args:
        result: Risultato del tool analyze_sleep_quality_correlation
        
    Returns:
        GraphData con il grafico Plotly in formato JSON, oppure ErrorResult
    """
    try:
        # Crea grafico a barre
        fig = go.Figure()
        
        correlations_data = [
            {
                "label": "Risvegli vs<br>Tempo Sonno",
                "value": result["correlations"]["wakeup_vs_sleep_time"],
                "color": "#3b82f6"
            },
            {
                "label": "Uscite Letto vs<br>Tempo Sonno",
                "value": result["correlations"]["out_of_bed_vs_sleep_time"],
                "color": "#8b5cf6"
            }
        ]
        
        labels = [item["label"] for item in correlations_data]
        values = [item["value"] for item in correlations_data]
        colors = [item["color"] for item in correlations_data]
        
        fig.add_trace(
            go.Bar(
                x=labels,
                y=values,
                marker_color=colors,
                text=[f"{val:.3f}" for val in values],
                textposition="auto",
                name="Correlazione"
            )
        )
        
        # Aggiungi linea di riferimento a y=0
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        
        # Layout
        fig.update_layout(
            title_text=f"Correlazione Interruzioni - Qualità Sonno - Soggetto {result['subject_id']}<br><sub>Periodo: {result['period']} | Notti: {result['num_nights']}</sub>",
            title_font_size=18,
            xaxis_title="Tipo di Correlazione",
            yaxis_title="Coefficiente di Correlazione",
            yaxis_range=[-1.1, 1.1],
            showlegend=False,
            height=500,
            template="plotly_white"
        )
        
        # Aggiungi annotazioni per interpretazione
        fig.add_annotation(
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            text="<b>Interpretazione:</b><br>Negativo = più interruzioni → meno sonno<br>Positivo = più interruzioni → più sonno<br>~0 = nessuna relazione",
            showarrow=False,
            align="left",
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="gray",
            borderwidth=1,
            font=dict(size=10)
        )
        
        graph_data: GraphData = {
            "id": f"sleep_correlation_{result['subject_id']}",
            "title": f"Correlazione Interruzioni-Qualità - Soggetto {result['subject_id']}",
            "type": "sleep_quality_correlation",
            "plotly_json": fig.to_dict()
        }
        
        return graph_data
        
    except Exception as e:
        return ErrorResult(error=f"Errore nella visualizzazione correlazioni sonno: {str(e)}")


@tool
def visualize_daily_heart_rate(
    result: Annotated[DailyHeartRateResult, "Result from analyze_daily_heart_rate tool"]
) -> GraphData | ErrorResult:
    """
    Crea una visualizzazione per la frequenza cardiaca giornaliera durante il sonno.
    
    Genera un line chart che mostra l'andamento della FC media notturna nel tempo:
    - Asse X: Date
    - Asse Y: Frequenza cardiaca (bpm)
    - Linea con marker per ogni notte
    
    Args:
        result: Risultato del tool analyze_daily_heart_rate
        
    Returns:
        GraphData con il grafico Plotly in formato JSON, oppure ErrorResult
    """
    try:
        # Estrai date e valori
        dates = list(result["daily_avg_hr"].keys())
        hr_values = list(result["daily_avg_hr"].values())
        
        # Crea line chart
        fig = go.Figure()
        
        fig.add_trace(
            go.Scatter(
                x=dates,
                y=hr_values,
                mode="lines+markers",
                line=dict(color="#ef4444", width=2),
                marker=dict(size=8, color="#dc2626"),
                name="FC Media",
                hovertemplate="<b>%{x}</b><br>FC: %{y:.1f} bpm<extra></extra>"
            )
        )
        
        # Calcola media complessiva per linea di riferimento
        avg_hr = sum(hr_values) / len(hr_values) if hr_values else 0
        
        fig.add_hline(
            y=avg_hr,
            line_dash="dash",
            line_color="gray",
            opacity=0.5,
            annotation_text=f"Media: {avg_hr:.1f} bpm",
            annotation_position="right"
        )
        
        # Layout
        fig.update_layout(
            title_text=f"Frequenza Cardiaca Notturna - Soggetto {result['subject_id']}<br><sub>Periodo: {result['period']}</sub>",
            title_font_size=18,
            xaxis_title="Data",
            yaxis_title="Frequenza Cardiaca (bpm)",
            showlegend=False,
            height=500,
            template="plotly_white",
            hovermode="x unified"
        )
        
        # Formatta asse X per date
        fig.update_xaxes(
            tickangle=-45,
            tickformat="%d/%m/%Y"
        )
        
        graph_data: GraphData = {
            "id": f"daily_hr_{result['subject_id']}",
            "title": f"Frequenza Cardiaca Notturna - Soggetto {result['subject_id']}",
            "type": "daily_heart_rate",
            "plotly_json": fig.to_dict()
        }
        
        return graph_data
        
    except Exception as e:
        return ErrorResult(error=f"Errore nella visualizzazione frequenza cardiaca: {str(e)}")