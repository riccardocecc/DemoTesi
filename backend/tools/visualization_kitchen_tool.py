"""
Tool per la generazione di grafici del dominio Kitchen.
Ogni tool corrisponde a un template Plotly.
"""

from langchain_core.tools import tool
from typing import Any

from backend.models.results import KitchenAnalysisResult
from backend.models.state import GraphData
from backend.utils.graph_templates import (
    create_kitchen_timeslot_bar,
    create_kitchen_metrics_cards
)


@tool
def generate_kitchen_timeslot_chart(kitchen_data: dict) -> dict:
    """
    Genera un grafico a barre che mostra l'utilizzo della cucina per fascia oraria.

    Usa questo tool quando l'utente chiede informazioni su:
    - Quando usa la cucina
    - Distribuzione delle attività in cucina
    - Orari dei pasti (colazione, pranzo, cena)
    - Fasce orarie di utilizzo cucina
    - Quando cucina di più

    Args:
        kitchen_data: Dizionario con i dati di kitchen_agent contenente:
            - time_slot_distribution (dict con chiavi: mattina, pranzo, cena)
            - subject_id

    Returns:
        GraphData con il grafico Plotly
    """
    try:
        if "error" in kitchen_data:
            return {"error": "Dati della cucina non disponibili"}

        graph = create_kitchen_timeslot_bar(kitchen_data)
        return graph
    except Exception as e:
        return {"error": f"Errore nella generazione del grafico: {str(e)}"}


@tool
def generate_kitchen_metrics_dashboard(kitchen_data: dict) -> dict:
    """
    Genera un dashboard con le metriche chiave dell'utilizzo della cucina.

    Usa questo tool quando l'utente chiede informazioni su:
    - Frequenza di utilizzo cucina
    - Quante volte usa la cucina
    - Durata media delle attività in cucina
    - Tempo totale passato in cucina
    - Statistiche generali sulla cucina
    - Metriche complessive cucina

    Mostra tre indicatori: frequenza giornaliera, durata media, tempo totale.

    Args:
        kitchen_data: Dizionario con i dati di kitchen_agent contenente:
            - activities_per_day
            - avg_duration_minutes
            - total_cooking_time_hours
            - subject_id

    Returns:
        GraphData con il grafico Plotly
    """
    try:
        if "error" in kitchen_data:
            return {"error": "Dati della cucina non disponibili"}

        graph = create_kitchen_metrics_cards(kitchen_data)
        return graph
    except Exception as e:
        return {"error": f"Errore nella generazione del grafico: {str(e)}"}