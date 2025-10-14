"""
Tool per la generazione di grafici del dominio Mobility.
Ogni tool corrisponde a un template Plotly.
"""

from langchain_core.tools import tool
from typing import Any

from backend.models.results import MobilityAnalysisResult
from backend.models.state import GraphData
from backend.utils.graph_templates import (
    create_mobility_room_bars,
    create_mobility_timeslot_bar
)


@tool
def generate_mobility_room_distribution_chart(mobility_data: dict) -> dict:
    """
    Genera un grafico a barre che mostra la distribuzione della presenza nelle varie stanze.

    Usa questo tool quando l'utente chiede informazioni su:
    - In quali stanze passa più tempo
    - Distribuzione nelle stanze
    - Stanze più frequentate
    - Dove si sposta di più
    - Presenza per ambiente
    - Utilizzo degli spazi

    Mostra le stanze ordinate per frequenza con percentuali.

    Args:
        mobility_data: Dizionario con i dati di mobility_agent contenente:
            - room_distribution (dict con nome_stanza: count)
            - room_percentages (dict con nome_stanza: percentuale)
            - subject_id

    Returns:
        GraphData con il grafico Plotly
    """
    try:
        if "error" in mobility_data:
            return {"error": "Dati di mobilità non disponibili"}

        graph = create_mobility_room_bars(mobility_data)
        return graph
    except Exception as e:
        return {"error": f"Errore nella generazione del grafico: {str(e)}"}


@tool
def generate_mobility_timeslot_chart(mobility_data: dict) -> dict:
    """
    Genera un grafico a barre che mostra l'attività di mobilità per fascia oraria.

    Usa questo tool quando l'utente chiede informazioni su:
    - Quando si muove di più
    - Attività per fascia oraria
    - Orari di maggiore movimento
    - Distribuzione temporale degli spostamenti
    - Mobilità durante la giornata
    - Pattern di movimento giornaliero

    Mostra le fasce: notte, mattina, pomeriggio, sera.

    Args:
        mobility_data: Dizionario con i dati di mobility_agent contenente:
            - time_slot_activity (dict con fascia_oraria: count)
            - subject_id

    Returns:
        GraphData con il grafico Plotly
    """
    try:
        if "error" in mobility_data:
            return {"error": "Dati di mobilità non disponibili"}

        graph = create_mobility_timeslot_bar(mobility_data)
        return graph
    except Exception as e:
        return {"error": f"Errore nella generazione del grafico: {str(e)}"}