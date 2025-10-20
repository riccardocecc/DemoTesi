"""
backend/nodes/correlation_graph_node.py

Nodo per la generazione di grafici cross-domain in UN SINGOLO PANNELLO.
Gestisce correttamente i TypedDict strutturati dai vari agenti.
"""
import json
from typing import Literal, Optional
import plotly.graph_objects as go
from pydantic import BaseModel, Field
from langgraph.types import Command
from langchain_core.messages import HumanMessage

from backend.models.state import State, GraphData


# =============================================================================
# SINGLE PANEL MODELS
# =============================================================================

class MetricMapping(BaseModel):
    """Mappatura di una metrica dai dati raw"""
    label: str = Field(description="Label da mostrare nel grafico")
    domain: Literal["sleep", "kitchen", "mobility"] = Field(description="Dominio della metrica")
    path: str = Field(description="Path nei dati (es: 'rem_sleep.avg_minutes', 'total_sleep_time.average')")
    unit: str = Field(description="Unità di misura (es: 'min', 'h', '%')")
    color: Optional[str] = Field(default=None, description="Colore esadecimale (opzionale)")


class SinglePanelGraphIntent(BaseModel):
    """Intent per un grafico a pannello singolo cross-domain"""
    chart_type: Literal["bar", "grouped_bar", "line"] = Field(
        description="Tipo di visualizzazione nel pannello unico"
    )
    title: str = Field(description="Titolo del grafico")
    metrics: list[MetricMapping] = Field(
        description="Lista delle metriche cross-domain da confrontare (max 8)"
    )
    insight: str = Field(description="Insight del grafico")
    y_axis_title: Optional[str] = Field(default="Valore", description="Titolo asse Y")


class VisualizationPlan(BaseModel):
    """Piano per generare UN GRAFICO A PANNELLO SINGOLO"""
    generate_visualization: bool = Field(
        description="Se True, genera il grafico"
    )
    graph: Optional[SinglePanelGraphIntent] = Field(
        default=None,
        description="Configurazione del grafico a pannello singolo"
    )
    explanation: str = Field(description="Spiegazione del piano")


# =============================================================================
# DATA HELPERS
# =============================================================================

def extract_value_from_path(data: dict, path: str) -> float:
    """
    Estrae un valore da un path nei TypedDict.
    Supporta sia path semplici ('total_activities') che nested ('rem_sleep.avg_minutes').
    """
    try:
        keys = path.split('.')
        value = data

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return 0.0
            else:
                return 0.0

        # Converti a float
        if isinstance(value, (int, float)):
            return float(value)
        return 0.0

    except (KeyError, ValueError, TypeError, AttributeError) as e:
        print(f"   ⚠️  Failed to extract '{path}': {e}")
        return 0.0


def get_all_domains_data(sleep_data: dict, kitchen_data: dict, mobility_data: dict) -> dict:
    """Restituisce tutti i dati organizzati per dominio"""
    return {
        "sleep": sleep_data or {},
        "kitchen": kitchen_data or {},
        "mobility": mobility_data or {}
    }


# =============================================================================
# SINGLE PANEL GRAPH BUILDER
# =============================================================================

def create_single_panel_graph(
        intent: SinglePanelGraphIntent,
        sleep_data: dict,
        kitchen_data: dict,
        mobility_data: dict,
        subject_id: int
) -> GraphData:
    """
    Costruisce UN GRAFICO CON UN SOLO PANNELLO che confronta metriche cross-domain.
    """
    fig = go.Figure()
    all_data = get_all_domains_data(sleep_data, kitchen_data, mobility_data)

    # Colori di default per dominio
    domain_colors = {
        "sleep": "#9B59B6",
        "kitchen": "#E67E22",
        "mobility": "#3498DB"
    }

    if intent.chart_type == "bar":
        # Bar chart: tutte le metriche nello stesso pannello
        labels = []
        values = []
        colors = []
        hover_texts = []

        for metric in intent.metrics:
            domain_data = all_data.get(metric.domain, {})
            value = extract_value_from_path(domain_data, metric.path)

            labels.append(metric.label)
            values.append(value)
            colors.append(metric.color or domain_colors.get(metric.domain, '#95a5a6'))
            hover_texts.append(
                f"<b>{metric.label}</b><br>"
                f"Dominio: {metric.domain.upper()}<br>"
                f"Valore: {value:.1f} {metric.unit}"
            )

        fig.add_trace(go.Bar(
            x=labels,
            y=values,
            marker=dict(color=colors),
            text=[f"{v:.1f}" for v in values],
            textposition='outside',
            hovertemplate='%{hovertext}<extra></extra>',
            hovertext=hover_texts,
            showlegend=False
        ))

        fig.update_layout(
            xaxis_title="Metriche",
            yaxis_title=intent.y_axis_title
        )

    elif intent.chart_type == "grouped_bar":
        # Grouped bar: raggruppa per dominio
        domains_metrics = {}
        for metric in intent.metrics:
            if metric.domain not in domains_metrics:
                domains_metrics[metric.domain] = []
            domains_metrics[metric.domain].append(metric)

        for domain, metrics in domains_metrics.items():
            domain_data = all_data.get(domain, {})
            labels = [m.label for m in metrics]
            values = [extract_value_from_path(domain_data, m.path) for m in metrics]

            fig.add_trace(go.Bar(
                name=domain.title(),
                x=labels,
                y=values,
                marker=dict(color=domain_colors.get(domain, '#95a5a6')),
                text=[f"{v:.1f}" for v in values],
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Dominio: ' + domain.upper() + '<br>Valore: %{y:.1f}<extra></extra>'
            ))

        fig.update_layout(
            barmode='group',
            xaxis_title="Metriche",
            yaxis_title=intent.y_axis_title,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

    elif intent.chart_type == "line":
        # Line chart: una linea per dominio
        domains_metrics = {}
        for metric in intent.metrics:
            if metric.domain not in domains_metrics:
                domains_metrics[metric.domain] = []
            domains_metrics[metric.domain].append(metric)

        for domain, metrics in domains_metrics.items():
            domain_data = all_data.get(domain, {})
            labels = [m.label for m in metrics]
            values = [extract_value_from_path(domain_data, m.path) for m in metrics]

            fig.add_trace(go.Scatter(
                name=domain.title(),
                x=labels,
                y=values,
                mode='lines+markers',
                marker=dict(size=10, color=domain_colors.get(domain, '#95a5a6')),
                line=dict(width=3, color=domain_colors.get(domain, '#95a5a6')),
                hovertemplate='<b>%{x}</b><br>Dominio: ' + domain.upper() + '<br>Valore: %{y:.1f}<extra></extra>'
            ))

        fig.update_layout(
            xaxis_title="Metriche",
            yaxis_title=intent.y_axis_title,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

    # Layout comune
    fig.update_layout(
        title=f"{intent.title} - Soggetto {subject_id}",
        height=500,
        template="plotly_white",
        font=dict(size=12),
        margin=dict(t=100, b=80, l=80, r=40)
    )

    return {
        "id": f"single_panel_{subject_id}",
        "title": intent.title,
        "type": "single_panel_comparison",
        "plotly_json": fig.to_dict()
    }


# =============================================================================
# FALLBACK PLAN
# =============================================================================

def _create_fallback_plan(
        query: str,
        sleep_data: dict,
        kitchen_data: dict,
        mobility_data: dict
) -> VisualizationPlan:
    """
    Crea un piano di fallback quando l'LLM fallisce.
    Genera un grafico a barre con le metriche principali disponibili.
    """
    query_lower = query.lower()
    metrics = []

    # SLEEP DOMAIN
    if sleep_data:
        # SleepDistributionResult
        if "rem_sleep" in sleep_data and isinstance(sleep_data["rem_sleep"], dict):
            metrics.append(MetricMapping(
                label="REM",
                domain="sleep",
                path="rem_sleep.avg_minutes",
                unit="min",
                color="#9B59B6"
            ))
        if "deep_sleep" in sleep_data and isinstance(sleep_data["deep_sleep"], dict):
            metrics.append(MetricMapping(
                label="Sonno Profondo",
                domain="sleep",
                path="deep_sleep.avg_minutes",
                unit="min",
                color="#8E44AD"
            ))
        if "light_sleep" in sleep_data and isinstance(sleep_data["light_sleep"], dict):
            metrics.append(MetricMapping(
                label="Sonno Leggero",
                domain="sleep",
                path="light_sleep.avg_minutes",
                unit="min",
                color="#BB8FCE"
            ))

        # SleepStatisticsResult
        if "total_sleep_time" in sleep_data and isinstance(sleep_data["total_sleep_time"], dict):
            metrics.append(MetricMapping(
                label="Durata Sonno",
                domain="sleep",
                path="total_sleep_time.average",
                unit="min",
                color="#9B59B6"
            ))

        # Sleep efficiency (direct value)
        if "sleep_efficiency" in sleep_data and not isinstance(sleep_data["sleep_efficiency"], dict):
            metrics.append(MetricMapping(
                label="Efficienza",
                domain="sleep",
                path="sleep_efficiency",
                unit="%",
                color="#8E44AD"
            ))

    # KITCHEN DOMAIN
    if kitchen_data:
        # KitchenAnalysisResult
        if "activities_per_day" in kitchen_data:
            metrics.append(MetricMapping(
                label="Attività/giorno",
                domain="kitchen",
                path="activities_per_day",
                unit="volte",
                color="#E67E22"
            ))
        if "avg_duration_minutes" in kitchen_data:
            metrics.append(MetricMapping(
                label="Durata Media",
                domain="kitchen",
                path="avg_duration_minutes",
                unit="min",
                color="#D35400"
            ))
        if "avg_temperature_max" in kitchen_data:
            metrics.append(MetricMapping(
                label="Temp. Max",
                domain="kitchen",
                path="avg_temperature_max",
                unit="°C",
                color="#C0392B"
            ))

    # MOBILITY DOMAIN
    if mobility_data:
        # MobilityAnalysisResult
        if "detections_per_day" in mobility_data:
            metrics.append(MetricMapping(
                label="Rilevazioni/giorno",
                domain="mobility",
                path="detections_per_day",
                unit="volte",
                color="#3498DB"
            ))
        if "avg_duration_minutes" in mobility_data:
            metrics.append(MetricMapping(
                label="Durata Media",
                domain="mobility",
                path="avg_duration_minutes",
                unit="min",
                color="#2E86C1"
            ))

    if not metrics:
        return VisualizationPlan(
            generate_visualization=False,
            graph=None,
            explanation="Fallback: nessuna metrica disponibile nei dati"
        )

    # Limita a max 8 metriche per non sovraffollare
    metrics = metrics[:8]

    return VisualizationPlan(
        generate_visualization=True,
        graph=SinglePanelGraphIntent(
            chart_type="bar",
            title="Confronto Metriche Multi-Dominio",
            metrics=metrics,
            insight="Visualizzazione unificata delle metriche principali disponibili",
            y_axis_title="Valore"
        ),
        explanation=f"Fallback: grafico a barre con {len(metrics)} metriche da {len(set(m.domain for m in metrics))} domini"
    )


def _create_data_summary(sleep_data: dict, kitchen_data: dict, mobility_data: dict) -> str:
    """
    Crea un sommario dettagliato con SEMANTICA dei dati disponibili.
    Legge i path REALI dai dati invece di inventarli.
    """
    summary = []

    # =========================================================================
    # SLEEP DATA
    # =========================================================================
    if sleep_data:
        summary.append("🌙 SLEEP DATA:")

        # Sleep distribution
        if "rem_sleep" in sleep_data and isinstance(sleep_data["rem_sleep"], dict):
            summary.append("  - rem_sleep.avg_minutes (durata media fase REM in minuti)")
            summary.append("  - rem_sleep.percentage (% fase REM sul totale)")
        if "deep_sleep" in sleep_data and isinstance(sleep_data["deep_sleep"], dict):
            summary.append("  - deep_sleep.avg_minutes (durata media sonno profondo in minuti)")
            summary.append("  - deep_sleep.percentage (% sonno profondo)")
        if "light_sleep" in sleep_data and isinstance(sleep_data["light_sleep"], dict):
            summary.append("  - light_sleep.avg_minutes (durata media sonno leggero in minuti)")
            summary.append("  - light_sleep.percentage (% sonno leggero)")

        # Direct values
        if "total_sleep_minutes" in sleep_data and not isinstance(sleep_data["total_sleep_minutes"], dict):
            summary.append("  - total_sleep_minutes (durata totale sonno in minuti)")
        if "sleep_efficiency" in sleep_data and not isinstance(sleep_data["sleep_efficiency"], dict):
            summary.append("  - sleep_efficiency (efficienza del sonno in %)")

        # SleepStatisticsResult
        if "total_sleep_time" in sleep_data and isinstance(sleep_data["total_sleep_time"], dict):
            summary.append("  - total_sleep_time.average (durata media sonno)")
            summary.append("  - total_sleep_time.median (mediana durata sonno)")
        if "rem_sleep_duration" in sleep_data and isinstance(sleep_data["rem_sleep_duration"], dict):
            summary.append("  - rem_sleep_duration.average (durata media REM)")
        if "wakeup_count" in sleep_data and isinstance(sleep_data["wakeup_count"], dict):
            summary.append("  - wakeup_count.average (numero medio risvegli)")

    # =========================================================================
    # KITCHEN DATA
    # =========================================================================
    if kitchen_data:
        summary.append("\n🍳 KITCHEN DATA:")

        # Metriche aggregate comuni
        if "activities_per_day" in kitchen_data:
            summary.append("  - activities_per_day (numero medio attività/giorno)")
        if "avg_duration_minutes" in kitchen_data:
            summary.append("  - avg_duration_minutes (durata media singola attività in minuti)")
        if "total_cooking_time_hours" in kitchen_data:
            summary.append("  - total_cooking_time_hours (tempo totale cucina in ore - AGGREGATO)")
        if "avg_temperature_max" in kitchen_data:
            summary.append("  - avg_temperature_max (temperatura massima media)")

        # ⚡ DISTRIBUZIONE TEMPORALE - Gestisci entrambe le strutture
        # Variante 1: timeslot_distribution (KitchenUsagePatternResult)
        if "timeslot_distribution" in kitchen_data and isinstance(kitchen_data["timeslot_distribution"], dict):
            summary.append("\n  📍 DISTRIBUZIONE FASCE ORARIE (timeslot_distribution):")
            for timeslot, values in kitchen_data["timeslot_distribution"].items():
                if isinstance(values, dict):
                    # Mostra tutti i sottocampi disponibili
                    if "percentage" in values:
                        summary.append(
                            f"    - timeslot_distribution.{timeslot}.percentage (% attività in questa fascia)")
                    if "count" in values:
                        summary.append(f"    - timeslot_distribution.{timeslot}.count (numero attività)")
                    if "avg_duration" in values:
                        summary.append(f"    - timeslot_distribution.{timeslot}.avg_duration (durata media in minuti)")
            summary.append(
                "    ⚠️ USA QUESTI per query su 'quando', 'fasce orarie', 'orari', 'distribuzione temporale'")

        # Variante 2: time_slot_distribution (KitchenAnalysisResult)
        elif "time_slot_distribution" in kitchen_data and isinstance(kitchen_data["time_slot_distribution"], dict):
            summary.append("\n  📍 DISTRIBUZIONE FASCE ORARIE (time_slot_distribution):")
            for timeslot, count in kitchen_data["time_slot_distribution"].items():
                summary.append(f"    - time_slot_distribution.{timeslot} (conteggio attività)")
            summary.append("    ⚠️ USA QUESTI per query su 'quando', 'fasce orarie', 'orari'")

        if "most_active_slot" in kitchen_data:
            summary.append(f"  - most_active_slot (fascia più attiva: '{kitchen_data['most_active_slot']}')")

        # Temperature analysis
        if "avg_temp_by_timeslot" in kitchen_data and isinstance(kitchen_data["avg_temp_by_timeslot"], dict):
            summary.append("\n  🌡️ TEMPERATURA PER FASCIA:")
            for timeslot in kitchen_data["avg_temp_by_timeslot"].keys():
                summary.append(f"    - avg_temp_by_timeslot.{timeslot}")

    # =========================================================================
    # MOBILITY DATA
    # =========================================================================
    if mobility_data:
        summary.append("\n🚶 MOBILITY DATA:")

        if "detections_per_day" in mobility_data:
            summary.append("  - detections_per_day (rilevazioni medie/giorno)")
        if "avg_duration_minutes" in mobility_data:
            summary.append("  - avg_duration_minutes (durata media movimento in minuti)")
        if "total_active_time_hours" in mobility_data:
            summary.append("  - total_active_time_hours (tempo attivo totale in ore - AGGREGATO)")

        # Room distribution
        if "room_distribution" in mobility_data and isinstance(mobility_data["room_distribution"], dict):
            summary.append("\n  📍 DISTRIBUZIONE STANZE (room_distribution):")
            for room in mobility_data["room_distribution"].keys():
                summary.append(f"    - room_distribution.{room} (conteggio rilevazioni)")

        # Room percentages
        if "room_percentages" in mobility_data and isinstance(mobility_data["room_percentages"], dict):
            summary.append("\n  📍 PERCENTUALI STANZE (room_percentages):")
            for room in mobility_data["room_percentages"].keys():
                summary.append(f"    - room_percentages.{room} (% tempo trascorso)")

        # Time slot activity
        if "time_slot_activity" in mobility_data and isinstance(mobility_data["time_slot_activity"], dict):
            summary.append("\n  ⏰ ATTIVITÀ PER FASCIA ORARIA (time_slot_activity):")
            for timeslot in mobility_data["time_slot_activity"].keys():
                summary.append(f"    - time_slot_activity.{timeslot} (conteggio rilevazioni)")

    return "\n".join(summary) if summary else "Nessun dato disponibile"
# =============================================================================
# NODE IMPLEMENTATION
# =============================================================================

def create_correlation_graph_node(llm):
    """Crea il nodo per generare UN GRAFICO A PANNELLO SINGOLO cross-domain"""

    def correlation_graph_node(state: State) -> Command[Literal["correlation_analyzer"]]:
        """Genera un grafico a pannello singolo cross-domain"""
        print(f"\n{'=' * 60}")
        print("CORRELATION GRAPH NODE - Single Panel Approach")
        print(f"{'=' * 60}\n")

        original_question = state.get("original_question", "")
        team_responses = state.get("structured_responses", [])
        # =====================================================================
        # DEBUG: Visualizza la struttura completa delle risposte
        # =====================================================================
        print("🔍 DEBUG: STRUCTURED RESPONSES")
        print(f"{'─' * 60}")
        print(f"Total teams: {len(team_responses)}")

        for idx, team_resp in enumerate(team_responses):
            team_name = team_resp.get("team_name", "unknown")
            print(f"\n[Team {idx + 1}] {team_name}")
            print(f"  Keys: {list(team_resp.keys())}")

            structured_resps = team_resp.get("structured_responses", [])
            print(f"  Agents: {len(structured_resps)}")

            for agent_idx, agent_resp in enumerate(structured_resps):
                agent_name = agent_resp.get("agent_name", "unknown")
                data = agent_resp.get("data", {})

                print(f"\n  [{agent_idx + 1}] Agent: {agent_name}")
                print(f"      Keys in data: {list(data.keys())}")

                # Mostra la struttura dettagliata dei dati
                if "error" not in data:
                    for key, value in data.items():
                        if isinstance(value, dict):
                            print(f"      • {key}: dict with keys {list(value.keys())}")
                            # Mostra anche i valori se è una distribuzione
                            if "distribution" in key.lower():
                                for subkey, subval in value.items():
                                    print(f"          - {subkey}: {subval}")
                        elif isinstance(value, list):
                            print(f"      • {key}: list[{len(value)}]")
                        else:
                            print(f"      • {key}: {type(value).__name__} = {value}")
                else:
                    print(f"      ⚠️ Error: {data.get('error')}")

        print(f"\n{'─' * 60}\n")
        # =====================================================================

        # Estrai dati dai team
        sleep_data = None
        kitchen_data = None
        mobility_data = None

        for team_resp in team_responses:
            team_name = team_resp["team_name"]
            for agent_resp in team_resp["structured_responses"]:
                if "error" not in agent_resp["data"]:
                    if team_name == "sleep_team" and agent_resp["agent_name"] == "sleep_agent":
                        sleep_data = agent_resp["data"]
                    elif team_name == "kitchen_team" and agent_resp["agent_name"] == "kitchen_agent":
                        kitchen_data = agent_resp["data"]
                    elif team_name == "mobility_team" and agent_resp["agent_name"] == "mobility_agent":
                        mobility_data = agent_resp["data"]

        if not any([sleep_data, kitchen_data, mobility_data]):
            print("⚠️  No data available")
            return Command(goto="correlation_analyzer", update={
                "messages": [HumanMessage(content="No data", name="correlation_graph")]
            })

        print("📊 Available data:")
        if sleep_data:
            print(f"   ✓ Sleep: {list(sleep_data.keys())[:6]}")
        if kitchen_data:
            print(f"   ✓ Kitchen: {list(kitchen_data.keys())[:6]}")
        if mobility_data:
            print(f"   ✓ Mobility: {list(mobility_data.keys())[:6]}")

        # Prompt per LLM con struttura dati dettagliata
        data_summary = _create_data_summary(sleep_data, kitchen_data, mobility_data)

        intent_prompt = f"""Crea UN GRAFICO A PANNELLO SINGOLO per confrontare metriche cross-domain.

        QUERY UTENTE: "{original_question}"

        STRUTTURE DATI DISPONIBILI:
        {data_summary}

        🎯 REGOLE PER LA SELEZIONE DELLE METRICHE:

        1. **Analisi della query**:
           - "quando", "fasce orarie", "orari", "distribuzione temporale"
             → USA *_distribution.*, time_slot_activity.*
           - "quanto", "durata", "totale"
             → USA avg_*, total_*
           - "qualità", "efficienza", "percentuale", "proporzione"
             → USA *_percentage, *_efficiency
           - "correlazione", "relazione"
             → Scegli metriche con UNITÀ COMPATIBILI (vedi sotto)

        2. **Path corretti**: Usa SOLO i path esatti elencati sopra

        3. **Numero di metriche**: 3-4 metriche rilevanti

        4. **Tipo di chart**:
           - "bar": confronto metriche diverse (default)
           - "grouped_bar": raggruppa per dominio
           - "line": solo per progressioni logiche

        5. **⚠️ UNITÀ COMPATIBILI - REGOLA CRITICA**:
           Per query su "correlazione" o "relazione", le metriche DEVONO avere unità simili.

           ✅ COMBINAZIONI VALIDE:
           - Tutte percentuali: sleep_efficiency (%), rem_sleep.percentage (%), room_percentages.cucina (%)
           - Tutte durate: total_sleep_minutes (min), avg_duration_minutes (min)
           - Tutte frequenze: activities_per_day (count), detections_per_day (count)
           - Tutte ore: total_cooking_time_hours (h), total_active_time_hours (h)

           ❌ COMBINAZIONI INVALIDE (NON FARE MAI):
           - Mescolare % con conteggi: sleep_efficiency (%) + detections_per_day (count) ❌
           - Mescolare minuti con conteggi: avg_duration_minutes (min) + activities_per_day (count) ❌
           - Mescolare ore con %: total_active_time_hours (h) + sleep_efficiency (%) ❌

           Se non ci sono abbastanza metriche con unità compatibili, scegli UNA categoria principale
           e prendi tutte le metriche di quella categoria (es: solo percentuali, solo durate).

        📌 ESEMPIO per "{original_question}":
           Query: "correlazione efficienza sonno e mobilità"

           Opzione A (solo percentuali):
           - sleep_efficiency (%)
           - rem_sleep.percentage (%)
           - deep_sleep.percentage (%)
           - room_percentages.cucina (%)
           - room_percentages.soggiorno (%)

           Opzione B (solo durate):
           - total_sleep_minutes (min)
           - avg_duration_minutes (min)

           Opzione C (solo frequenze/conteggi):
           - detections_per_day (count)

           ❌ NON FARE:
           - sleep_efficiency (%) + detections_per_day (count) → unità incompatibili!

        Genera un piano con metriche OMOGENEE per unità di misura."""

        try:
            messages = [HumanMessage(content=intent_prompt)]
            structured_llm = llm.with_structured_output(VisualizationPlan, method="function_calling")
            plan = structured_llm.invoke(messages)

            if plan is None:
                print("⚠️  LLM returned None, using fallback")
                plan = _create_fallback_plan(original_question, sleep_data, kitchen_data, mobility_data)

            print(f"\n📋 Plan: {plan.explanation}")

            if not plan.generate_visualization or plan.graph is None:
                print("   → No visualization needed")
                return Command(goto="correlation_analyzer", update={
                    "messages": [HumanMessage(content=f"No viz: {plan.explanation}", name="correlation_graph")]
                })

            # Genera il grafico a pannello singolo
            subject_id = state.get("execution_plan").subject_id if state.get("execution_plan") else 0

            print(f"\n   → Generating single panel graph: {plan.graph.title}")
            print(f"      Chart type: {plan.graph.chart_type}")
            print(f"      Metrics: {len(plan.graph.metrics)}")
            for m in plan.graph.metrics:
                print(f"         • {m.label} ({m.domain}.{m.path})")

            graph = create_single_panel_graph(
                plan.graph,
                sleep_data or {},
                kitchen_data or {},
                mobility_data or {},
                subject_id
            )

            print(f"      ✓ Single panel graph created\n")

            existing_graphs = state.get("graphs", [])

            return Command(
                goto="correlation_analyzer",
                update={
                    "graphs": existing_graphs + [graph],
                    "messages": [HumanMessage(
                        content=f"Generated single panel graph: {plan.explanation}",
                        name="correlation_graph"
                    )]
                }
            )

        except Exception as e:
            print(f"❌ Failed: {e}")
            import traceback
            traceback.print_exc()

            # Prova fallback in caso di errore
            print("\n🔄 Attempting fallback plan...")
            try:
                fallback_plan = _create_fallback_plan(original_question, sleep_data, kitchen_data, mobility_data)
                if fallback_plan.generate_visualization and fallback_plan.graph:
                    subject_id = state.get("execution_plan").subject_id if state.get("execution_plan") else 0
                    graph = create_single_panel_graph(
                        fallback_plan.graph,
                        sleep_data or {},
                        kitchen_data or {},
                        mobility_data or {},
                        subject_id
                    )
                    existing_graphs = state.get("graphs", [])
                    return Command(
                        goto="correlation_analyzer",
                        update={
                            "graphs": existing_graphs + [graph],
                            "messages": [HumanMessage(
                                content=f"Generated fallback graph: {fallback_plan.explanation}",
                                name="correlation_graph"
                            )]
                        }
                    )
            except Exception as fallback_error:
                print(f"❌ Fallback also failed: {fallback_error}")

            return Command(goto="correlation_analyzer", update={
                "messages": [HumanMessage(content=f"Failed: {str(e)}", name="correlation_graph")]
            })

    return correlation_graph_node