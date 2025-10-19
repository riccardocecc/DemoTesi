"""
Tool per la generazione di grafici del dominio Kitchen.
Ogni tool corrisponde a un template Plotly basato sui nuovi tool di analisi.
"""

from langchain_core.tools import tool
from typing import Any

from backend.models.results import (
    KitchenStatisticsResult,
    KitchenUsagePatternResult,
    KitchenTemperatureAnalysisResult
)
from backend.models.state import GraphData
from backend.utils.graph_templates import (
    create_kitchen_statistics_dashboard,
    create_kitchen_timeslot_bar,
    create_kitchen_duration_by_timeslot,
    create_kitchen_temperature_distribution,
    create_kitchen_temperature_gauge,
    create_kitchen_temp_by_timeslot,
    create_kitchen_variability_box
)


@tool
def generate_kitchen_statistics_dashboard(kitchen_data: dict) -> dict:
    """
    Genera un dashboard con statistiche descrittive della cucina (media ± std dev).

    Questo tool si aspetta dati dal tool analyze_kitchen_statistics che contiene:
    - Statistiche complete per durata, temperatura, frequenza

    Mostra 3 metriche principali:
    - Durata media delle attività
    - Temperatura massima media
    - Frequenza giornaliera media

    Usa questo tool quando l'utente chiede:
    - Statistiche cucina
    - Media e variabilità
    - Panoramica statistica
    - Dati aggregati cucina

    Args:
        kitchen_data: Dizionario con i dati che può contenere:
            - "statistics": KitchenStatisticsResult
            - oppure direttamente le chiavi di KitchenStatisticsResult
            - subject_id

    Returns:
        GraphData con il grafico Plotly
    """
    try:
        if "error" in kitchen_data:
            return {"error": "Dati della cucina non disponibili"}

        # Estrai i dati corretti
        if "results" in kitchen_data:
            statistics_data = None
            for result in kitchen_data["results"]:
                if "duration_minutes" in result and isinstance(result.get("duration_minutes"), dict):
                    statistics_data = result
                    break
            if not statistics_data:
                return {"error": "Dati statistici cucina non disponibili"}
        elif "statistics" in kitchen_data:
            statistics_data = kitchen_data["statistics"]
        elif "duration_minutes" in kitchen_data and isinstance(kitchen_data.get("duration_minutes"), dict):
            statistics_data = kitchen_data
        else:
            return {"error": "Formato dati non valido per statistiche"}

        graph = create_kitchen_statistics_dashboard(statistics_data)
        return graph
    except Exception as e:
        return {"error": f"Errore nella generazione del grafico: {str(e)}"}


@tool
def generate_kitchen_variability_box(kitchen_data: dict) -> dict:
    """
    Genera box plot per mostrare la variabilità delle metriche cucina.

    Questo tool si aspetta dati dal tool analyze_kitchen_statistics che contiene:
    - Statistiche complete (min, median, average, max, std_dev) per ogni metrica

    Mostra min, Q1, mediana, Q3, max per:
    - Durata attività
    - Temperatura massima

    Usa questo tool quando l'utente chiede:
    - Variabilità cucina
    - Range valori
    - Distribuzione metriche
    - Consistenza utilizzo cucina

    Args:
        kitchen_data: Dizionario con i dati che può contenere:
            - "statistics": KitchenStatisticsResult
            - oppure direttamente le statistiche complete
            - subject_id

    Returns:
        GraphData con il grafico Plotly
    """
    try:
        if "error" in kitchen_data:
            return {"error": "Dati della cucina non disponibili"}

        # Estrai i dati corretti
        if "results" in kitchen_data:
            statistics_data = None
            for result in kitchen_data["results"]:
                if "duration_minutes" in result and isinstance(result.get("duration_minutes"), dict):
                    statistics_data = result
                    break
            if not statistics_data:
                return {"error": "Dati statistici per variabilità non disponibili"}
        elif "statistics" in kitchen_data:
            statistics_data = kitchen_data["statistics"]
        elif "duration_minutes" in kitchen_data and isinstance(kitchen_data.get("duration_minutes"), dict):
            statistics_data = kitchen_data
        else:
            return {"error": "Formato dati non valido per variabilità"}

        graph = create_kitchen_variability_box(statistics_data)
        return graph
    except Exception as e:
        return {"error": f"Errore nella generazione del grafico: {str(e)}"}


@tool
def generate_kitchen_timeslot_chart(kitchen_data: dict) -> dict:
    """
    Genera un grafico a barre che mostra l'utilizzo della cucina per fascia oraria.

    Questo tool si aspetta dati dal tool analyze_kitchen_usage_pattern che contiene:
    - timeslot_distribution con count, avg_duration, percentage per ogni fascia

    Usa questo tool quando l'utente chiede informazioni su:
    - Quando usa la cucina
    - Distribuzione delle attività in cucina
    - Orari dei pasti (colazione, pranzo, cena)
    - Fasce orarie di utilizzo cucina
    - Quando cucina di più

    Args:
        kitchen_data: Dizionario con i dati che può contenere:
            - "usage_pattern": KitchenUsagePatternResult
            - oppure direttamente timeslot_distribution
            - subject_id

    Returns:
        GraphData con il grafico Plotly
    """
    try:
        if "error" in kitchen_data:
            return {"error": "Dati della cucina non disponibili"}

        # Estrai i dati corretti
        if "results" in kitchen_data:
            pattern_data = None
            for result in kitchen_data["results"]:
                if "timeslot_distribution" in result and "most_active_slot" in result:
                    pattern_data = result
                    break
            if not pattern_data:
                return {"error": "Dati pattern cucina non disponibili"}
        elif "usage_pattern" in kitchen_data:
            pattern_data = kitchen_data["usage_pattern"]
        elif "timeslot_distribution" in kitchen_data:
            pattern_data = kitchen_data
        else:
            return {"error": "Formato dati non valido per timeslot"}

        graph = create_kitchen_timeslot_bar(pattern_data)
        return graph
    except Exception as e:
        return {"error": f"Errore nella generazione del grafico: {str(e)}"}


@tool
def generate_kitchen_duration_by_timeslot(kitchen_data: dict) -> dict:
    """
    Genera un grafico a barre per la durata media delle attività per fascia oraria.

    Questo tool si aspetta dati dal tool analyze_kitchen_usage_pattern che contiene:
    - timeslot_distribution con avg_duration per ogni fascia

    Mostra quanto tempo mediamente si passa in cucina in ogni fascia.

    Usa questo tool quando l'utente chiede:
    - Durata attività per fascia
    - Quanto tempo passa in cucina a pranzo/cena/mattina
    - Tempo medio per pasto
    - Analisi durata temporale

    Args:
        kitchen_data: Dizionario con i dati che può contenere:
            - "usage_pattern": KitchenUsagePatternResult
            - oppure direttamente timeslot_distribution
            - subject_id

    Returns:
        GraphData con il grafico Plotly
    """
    try:
        if "error" in kitchen_data:
            return {"error": "Dati della cucina non disponibili"}

        # Estrai i dati corretti
        if "results" in kitchen_data:
            pattern_data = None
            for result in kitchen_data["results"]:
                if "timeslot_distribution" in result and "most_active_slot" in result:
                    pattern_data = result
                    break
            if not pattern_data:
                return {"error": "Dati pattern cucina non disponibili"}
        elif "usage_pattern" in kitchen_data:
            pattern_data = kitchen_data["usage_pattern"]
        elif "timeslot_distribution" in kitchen_data:
            pattern_data = kitchen_data
        else:
            return {"error": "Formato dati non valido per durata"}

        graph = create_kitchen_duration_by_timeslot(pattern_data)
        return graph
    except Exception as e:
        return {"error": f"Errore nella generazione del grafico: {str(e)}"}


@tool
def generate_kitchen_temperature_distribution(kitchen_data: dict) -> dict:
    """
    Genera un grafico a barre per la distribuzione delle attività per intensità di temperatura.

    Questo tool si aspetta dati dal tool analyze_kitchen_temperature che contiene:
    - low_temp_count, medium_temp_count, high_temp_count

    Mostra quante attività sono a bassa (<50°C), media (50-150°C) o alta (>150°C) temperatura.

    Usa questo tool quando l'utente chiede:
    - Intensità cottura
    - Distribuzione temperature
    - Tipi di cottura
    - Quanto scalda quando cucina

    Args:
        kitchen_data: Dizionario con i dati che può contenere:
            - "temperature": KitchenTemperatureAnalysisResult
            - oppure direttamente low/medium/high_temp_count
            - subject_id

    Returns:
        GraphData con il grafico Plotly
    """
    try:
        if "error" in kitchen_data:
            return {"error": "Dati della cucina non disponibili"}

        # Estrai i dati corretti
        if "results" in kitchen_data:
            temp_data = None
            for result in kitchen_data["results"]:
                if "low_temp_count" in result and "temp_vs_duration_correlation" in result:
                    temp_data = result
                    break
            if not temp_data:
                return {"error": "Dati temperatura cucina non disponibili"}
        elif "temperature" in kitchen_data:
            temp_data = kitchen_data["temperature"]
        elif "low_temp_count" in kitchen_data:
            temp_data = kitchen_data
        else:
            return {"error": "Formato dati non valido per temperatura"}

        graph = create_kitchen_temperature_distribution(temp_data)
        return graph
    except Exception as e:
        return {"error": f"Errore nella generazione del grafico: {str(e)}"}


@tool
def generate_kitchen_temperature_gauge(kitchen_data: dict) -> dict:
    """
    Genera un gauge per la temperatura media raggiunta in cucina.

    Questo tool si aspetta dati dal tool analyze_kitchen_temperature che contiene:
    - avg_temperature, min_temperature, max_temperature

    Mostra la temperatura media con fasce colorate per intensità.

    Usa questo tool quando l'utente chiede:
    - Temperatura media cucina
    - Quanto scalda mediamente
    - Range temperature
    - Livello di cottura medio

    Args:
        kitchen_data: Dizionario con i dati che può contenere:
            - "temperature": KitchenTemperatureAnalysisResult
            - oppure direttamente avg/min/max_temperature
            - subject_id

    Returns:
        GraphData con il grafico Plotly
    """
    try:
        if "error" in kitchen_data:
            return {"error": "Dati della cucina non disponibili"}

        # Estrai i dati corretti
        if "results" in kitchen_data:
            temp_data = None
            for result in kitchen_data["results"]:
                if "avg_temperature" in result and "temp_vs_duration_correlation" in result:
                    temp_data = result
                    break
            if not temp_data:
                return {"error": "Dati temperatura cucina non disponibili"}
        elif "temperature" in kitchen_data:
            temp_data = kitchen_data["temperature"]
        elif "avg_temperature" in kitchen_data:
            temp_data = kitchen_data
        else:
            return {"error": "Formato dati non valido per gauge temperatura"}

        graph = create_kitchen_temperature_gauge(temp_data)
        return graph
    except Exception as e:
        return {"error": f"Errore nella generazione del grafico: {str(e)}"}


@tool
def generate_kitchen_temp_by_timeslot(kitchen_data: dict) -> dict:
    """
    Genera un grafico a barre per la temperatura media per fascia oraria.

    Questo tool si aspetta dati dal tool analyze_kitchen_temperature che contiene:
    - avg_temp_by_timeslot (dict con mattina, pranzo, cena)

    Mostra se si cucina più intensamente in certe fasce orarie.

    Usa questo tool quando l'utente chiede:
    - Temperatura per fascia oraria
    - Quando cucina più intensamente
    - Cotture più calde a pranzo o cena
    - Pattern temperatura temporale

    Args:
        kitchen_data: Dizionario con i dati che può contenere:
            - "temperature": KitchenTemperatureAnalysisResult
            - oppure direttamente avg_temp_by_timeslot
            - subject_id

    Returns:
        GraphData con il grafico Plotly
    """
    try:
        if "error" in kitchen_data:
            return {"error": "Dati della cucina non disponibili"}

        # Estrai i dati corretti
        if "results" in kitchen_data:
            temp_data = None
            for result in kitchen_data["results"]:
                if "avg_temp_by_timeslot" in result and "temp_vs_duration_correlation" in result:
                    temp_data = result
                    break
            if not temp_data:
                return {"error": "Dati temperatura per timeslot non disponibili"}
        elif "temperature" in kitchen_data:
            temp_data = kitchen_data["temperature"]
        elif "avg_temp_by_timeslot" in kitchen_data:
            temp_data = kitchen_data
        else:
            return {"error": "Formato dati non valido per temp by timeslot"}

        graph = create_kitchen_temp_by_timeslot(temp_data)
        return graph
    except Exception as e:
        return {"error": f"Errore nella generazione del grafico: {str(e)}"}