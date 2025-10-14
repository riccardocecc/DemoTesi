"""
Tool per la generazione di grafici del dominio Sleep.
Ogni tool corrisponde a un template Plotly.
"""

from langchain_core.tools import tool
from typing import Any

from backend.models.results import SleepAnalysisResult, DailyHeartRateResult
from backend.models.state import GraphData
from backend.utils.graph_templates import (
    create_sleep_phases_pie,
    create_sleep_efficiency_gauge,
    create_sleep_quality_bars,
    create_heart_rate_line
)


@tool
def generate_sleep_phases_chart(sleep_data: dict) -> dict:
    """
    Genera un grafico a torta che mostra la distribuzione delle fasi del sonno.

    Usa questo tool quando l'utente chiede informazioni su:
    - Fasi del sonno (REM, profondo, leggero)
    - Distribuzione del tempo di sonno
    - Quanto tempo ha passato in ogni fase

    Args:
        sleep_data: Dizionario con i dati di sleep_agent contenente:
            - avg_rem_sleep_minutes
            - avg_deep_sleep_minutes
            - avg_light_sleep_minutes
            - avg_total_sleep_hours
            - subject_id

    Returns:
        GraphData con il grafico Plotly
    """
    try:
        # Valida che i dati siano del tipo corretto
        if "error" in sleep_data:
            return {"error": "Dati del sonno non disponibili"}

        graph = create_sleep_phases_pie(sleep_data)
        return graph
    except Exception as e:
        return {"error": f"Errore nella generazione del grafico: {str(e)}"}


@tool
def generate_sleep_efficiency_gauge(sleep_data: dict) -> dict:
    """
    Genera un indicatore gauge per l'efficienza del sonno.

    Usa questo tool quando l'utente chiede informazioni su:
    - Efficienza del sonno
    - Qualità generale del sonno
    - Quanto bene ha dormito
    - Performance del sonno

    L'efficienza è mostrata come percentuale con fasce colorate:
    - Rosso: <70% (scarso)
    - Arancione: 70-85% (buono)
    - Verde: >85% (eccellente)

    Args:
        sleep_data: Dizionario con i dati di sleep_agent contenente:
            - sleep_efficiency (0-100)
            - subject_id

    Returns:
        GraphData con il grafico Plotly
    """
    try:
        if "error" in sleep_data:
            return {"error": "Dati del sonno non disponibili"}

        graph = create_sleep_efficiency_gauge(sleep_data)
        return graph
    except Exception as e:
        return {"error": f"Errore nella generazione del grafico: {str(e)}"}


@tool
def generate_sleep_disturbances_chart(sleep_data: dict) -> dict:
    """
    Genera un grafico a barre per i disturbi del sonno.

    Usa questo tool quando l'utente chiede informazioni su:
    - Risvegli notturni
    - Interruzioni del sonno
    - Uscite dal letto
    - Disturbi o problemi durante la notte
    - Continuità del sonno

    Args:
        sleep_data: Dizionario con i dati di sleep_agent contenente:
            - avg_wakeup_count
            - avg_out_of_bed_count
            - subject_id

    Returns:
        GraphData con il grafico Plotly
    """
    try:
        if "error" in sleep_data:
            return {"error": "Dati del sonno non disponibili"}

        graph = create_sleep_quality_bars(sleep_data)
        return graph
    except Exception as e:
        return {"error": f"Errore nella generazione del grafico: {str(e)}"}


@tool
def generate_heart_rate_timeline(heart_data: dict) -> dict:
    """
    Genera un grafico a linee per la frequenza cardiaca notturna nel tempo.

    Usa questo tool quando l'utente chiede informazioni su:
    - Frequenza cardiaca durante il sonno
    - Battiti cardiaci notturni
    - Andamento del cuore
    - Trend della frequenza cardiaca
    - Heart rate

    Mostra l'andamento giornaliero con media del periodo.

    Args:
        heart_data: Dizionario con i dati di heart_freq_agent contenente:
            - daily_avg_hr (dict con date e valori)
            - subject_id

    Returns:
        GraphData con il grafico Plotly
    """
    try:
        if "error" in heart_data:
            return {"error": "Dati della frequenza cardiaca non disponibili"}

        graph = create_heart_rate_line(heart_data)
        return graph
    except Exception as e:
        return {"error": f"Errore nella generazione del grafico: {str(e)}"}