"""
Tool per la generazione di grafici del dominio Sleep.
Ogni tool corrisponde a un template Plotly basato sui nuovi tool di analisi.
"""

from langchain_core.tools import tool
from typing import Any

from backend.models.results import (
    SleepStatisticsResult,
    SleepDistributionResult,
    SleepQualityCorrelationResult,
    DailyHeartRateResult
)
from backend.models.state import GraphData
from backend.utils.graph_templates import (
    create_sleep_phases_pie,
    create_sleep_efficiency_gauge,
    create_sleep_statistics_dashboard,
    create_sleep_quality_bars,
    create_sleep_correlation_heatmap,
    create_sleep_variability_box,
    create_heart_rate_line
)


@tool
def generate_sleep_phases_chart(sleep_data: dict) -> dict:
    """
    Genera un grafico a torta che mostra la distribuzione delle fasi del sonno.

    Questo tool si aspetta dati dal tool analyze_sleep_distribution che contiene:
    - rem_sleep, deep_sleep, light_sleep (con avg_minutes e percentage)
    - total_sleep_minutes
    - sleep_efficiency

    Usa questo tool quando l'utente chiede informazioni su:
    - Fasi del sonno (REM, profondo, leggero)
    - Distribuzione del tempo di sonno
    - Quanto tempo ha passato in ogni fase
    - Composizione del sonno
    - Percentuali delle fasi

    Args:
        sleep_data: Dizionario con i dati che può contenere:
            - "distribution": SleepDistributionResult
            - oppure direttamente le chiavi di SleepDistributionResult
            - subject_id

    Returns:
        GraphData con il grafico Plotly
    """
    try:
        if "error" in sleep_data:
            return {"error": "Dati del sonno non disponibili"}

        # Estrai i dati corretti
        # Se sleep_data contiene "results" (multipli tool), cerca distribution
        if "results" in sleep_data:
            distribution_data = None
            for result in sleep_data["results"]:
                if "rem_sleep" in result and "deep_sleep" in result:
                    distribution_data = result
                    break
            if not distribution_data:
                return {"error": "Dati di distribuzione del sonno non disponibili"}
        # Se sleep_data contiene "distribution" direttamente
        elif "distribution" in sleep_data:
            distribution_data = sleep_data["distribution"]
        # Se sleep_data è già il SleepDistributionResult
        elif "rem_sleep" in sleep_data and "deep_sleep" in sleep_data:
            distribution_data = sleep_data
        else:
            return {"error": "Formato dati non valido per distribuzione fasi"}

        graph = create_sleep_phases_pie(distribution_data)
        return graph
    except Exception as e:
        return {"error": f"Errore nella generazione del grafico: {str(e)}"}


@tool
def generate_sleep_efficiency_gauge(sleep_data: dict) -> dict:
    """
    Genera un indicatore gauge per l'efficienza del sonno.

    Questo tool si aspetta dati dal tool analyze_sleep_distribution che contiene:
    - sleep_efficiency (0-100%)

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
        sleep_data: Dizionario con i dati che può contenere:
            - "distribution": SleepDistributionResult
            - oppure direttamente sleep_efficiency
            - subject_id

    Returns:
        GraphData con il grafico Plotly
    """
    try:
        if "error" in sleep_data:
            return {"error": "Dati del sonno non disponibili"}

        # Estrai i dati corretti
        if "results" in sleep_data:
            distribution_data = None
            for result in sleep_data["results"]:
                if "sleep_efficiency" in result:
                    distribution_data = result
                    break
            if not distribution_data:
                return {"error": "Dati di efficienza del sonno non disponibili"}
        elif "distribution" in sleep_data:
            distribution_data = sleep_data["distribution"]
        elif "sleep_efficiency" in sleep_data:
            distribution_data = sleep_data
        else:
            return {"error": "Formato dati non valido per efficienza"}

        graph = create_sleep_efficiency_gauge(distribution_data)
        return graph
    except Exception as e:
        return {"error": f"Errore nella generazione del grafico: {str(e)}"}


@tool
def generate_sleep_statistics_dashboard(sleep_data: dict) -> dict:
    """
    Genera un dashboard con statistiche descrittive del sonno (media ± std dev).

    Questo tool si aspetta dati dal tool analyze_sleep_statistics che contiene:
    - Statistiche complete per ogni metrica (average, median, std_dev, min, max)

    Mostra 4 metriche principali:
    - Durata totale del sonno
    - Sonno profondo
    - Numero di risvegli
    - Frequenza cardiaca

    Usa questo tool quando l'utente chiede:
    - Statistiche del sonno
    - Media e deviazione standard
    - Variabilità dei parametri
    - Panoramica statistica
    - Dati aggregati con variabilità

    Args:
        sleep_data: Dizionario con i dati che può contenere:
            - "statistics": SleepStatisticsResult
            - oppure direttamente le chiavi di SleepStatisticsResult
            - subject_id

    Returns:
        GraphData con il grafico Plotly
    """
    try:
        if "error" in sleep_data:
            return {"error": "Dati del sonno non disponibili"}

        # Estrai i dati corretti
        if "results" in sleep_data:
            statistics_data = None
            for result in sleep_data["results"]:
                if "total_sleep_time" in result and isinstance(result.get("total_sleep_time"), dict):
                    statistics_data = result
                    break
            if not statistics_data:
                return {"error": "Dati statistici del sonno non disponibili"}
        elif "statistics" in sleep_data:
            statistics_data = sleep_data["statistics"]
        elif "total_sleep_time" in sleep_data and isinstance(sleep_data.get("total_sleep_time"), dict):
            statistics_data = sleep_data
        else:
            return {"error": "Formato dati non valido per statistiche"}

        graph = create_sleep_statistics_dashboard(statistics_data)
        return graph
    except Exception as e:
        return {"error": f"Errore nella generazione del grafico: {str(e)}"}


@tool
def generate_sleep_disturbances_chart(sleep_data: dict) -> dict:
    """
    Genera un grafico a barre per i disturbi del sonno.

    Questo tool si aspetta dati dal tool analyze_sleep_quality_correlation che contiene:
    - avg_wakeup_count
    - avg_out_of_bed_count

    Usa questo tool quando l'utente chiede informazioni su:
    - Risvegli notturni
    - Interruzioni del sonno
    - Uscite dal letto
    - Disturbi o problemi durante la notte
    - Continuità del sonno

    Args:
        sleep_data: Dizionario con i dati che può contenere:
            - "quality_correlation": SleepQualityCorrelationResult
            - oppure direttamente avg_wakeup_count e avg_out_of_bed_count
            - subject_id

    Returns:
        GraphData con il grafico Plotly
    """
    try:
        if "error" in sleep_data:
            return {"error": "Dati del sonno non disponibili"}

        # Estrai i dati corretti
        if "results" in sleep_data:
            correlation_data = None
            for result in sleep_data["results"]:
                if "correlations" in result or ("avg_wakeup_count" in result and "avg_out_of_bed_count" in result):
                    correlation_data = result
                    break
            if not correlation_data:
                return {"error": "Dati di disturbi del sonno non disponibili"}
        elif "quality_correlation" in sleep_data:
            correlation_data = sleep_data["quality_correlation"]
        elif "avg_wakeup_count" in sleep_data:
            correlation_data = sleep_data
        else:
            return {"error": "Formato dati non valido per disturbi"}

        graph = create_sleep_quality_bars(correlation_data)
        return graph
    except Exception as e:
        return {"error": f"Errore nella generazione del grafico: {str(e)}"}


@tool
def generate_sleep_correlation_heatmap(sleep_data: dict) -> dict:
    """
    Genera una heatmap delle correlazioni tra interruzioni e qualità del sonno.

    Questo tool si aspetta dati dal tool analyze_sleep_quality_correlation che contiene:
    - correlations: dict con 6 coefficienti di correlazione

    Mostra visivamente la forza delle relazioni tra:
    - Risvegli vs (durata sonno, efficienza, sonno profondo)
    - Uscite dal letto vs (durata sonno, efficienza, sonno profondo)

    Colori:
    - Rosso: correlazione negativa forte (più interruzioni → meno qualità)
    - Bianco: nessuna correlazione
    - Blu: correlazione positiva (inusuale)

    Usa questo tool quando l'utente chiede:
    - Correlazioni tra interruzioni e qualità
    - Impatto dei risvegli sul sonno
    - Come i disturbi influenzano il sonno
    - Relazione tra uscite dal letto e sonno profondo
    - Analisi delle correlazioni

    Args:
        sleep_data: Dizionario con i dati che può contenere:
            - "quality_correlation": SleepQualityCorrelationResult
            - oppure direttamente correlations
            - subject_id

    Returns:
        GraphData con il grafico Plotly
    """
    try:
        if "error" in sleep_data:
            return {"error": "Dati del sonno non disponibili"}

        # Estrai i dati corretti
        if "results" in sleep_data:
            correlation_data = None
            for result in sleep_data["results"]:
                if "correlations" in result:
                    correlation_data = result
                    break
            if not correlation_data:
                return {"error": "Dati di correlazione non disponibili"}
        elif "quality_correlation" in sleep_data:
            correlation_data = sleep_data["quality_correlation"]
        elif "correlations" in sleep_data:
            correlation_data = sleep_data
        else:
            return {"error": "Formato dati non valido per correlazioni"}

        graph = create_sleep_correlation_heatmap(correlation_data)
        return graph
    except Exception as e:
        return {"error": f"Errore nella generazione del grafico: {str(e)}"}


@tool
def generate_sleep_variability_box(sleep_data: dict) -> dict:
    """
    Genera box plot per mostrare la variabilità delle metriche del sonno.

    Questo tool si aspetta dati dal tool analyze_sleep_statistics che contiene:
    - Statistiche complete (min, median, average, max, std_dev) per ogni metrica

    Mostra min, Q1, mediana, Q3, max per:
    - Durata totale del sonno
    - Sonno REM
    - Sonno profondo
    - Sonno leggero

    Usa questo tool quando l'utente chiede:
    - Variabilità del sonno
    - Range dei valori
    - Distribuzione delle metriche
    - Quanto variano i parametri
    - Consistenza del sonno

    Args:
        sleep_data: Dizionario con i dati che può contenere:
            - "statistics": SleepStatisticsResult
            - oppure direttamente le statistiche complete
            - subject_id

    Returns:
        GraphData con il grafico Plotly
    """
    try:
        if "error" in sleep_data:
            return {"error": "Dati del sonno non disponibili"}

        # Estrai i dati corretti
        if "results" in sleep_data:
            statistics_data = None
            for result in sleep_data["results"]:
                if "total_sleep_time" in result and isinstance(result.get("total_sleep_time"), dict):
                    statistics_data = result
                    break
            if not statistics_data:
                return {"error": "Dati statistici per variabilità non disponibili"}
        elif "statistics" in sleep_data:
            statistics_data = sleep_data["statistics"]
        elif "total_sleep_time" in sleep_data and isinstance(sleep_data.get("total_sleep_time"), dict):
            statistics_data = sleep_data
        else:
            return {"error": "Formato dati non valido per variabilità"}

        graph = create_sleep_variability_box(statistics_data)
        return graph
    except Exception as e:
        return {"error": f"Errore nella generazione del grafico: {str(e)}"}


@tool
def generate_heart_rate_timeline(heart_data: dict) -> dict:
    """
    Genera un grafico a linee per la frequenza cardiaca notturna nel tempo.

    Questo tool si aspetta dati dal tool analyze_daily_heart_rate che contiene:
    - daily_avg_hr: dict con date (YYYY-MM-DD) come chiavi e FC come valori

    Mostra l'andamento giornaliero della FC notturna con:
    - Linea di trend
    - Media del periodo (linea tratteggiata)
    - Valori puntuali per ogni notte

    Usa questo tool quando l'utente chiede informazioni su:
    - Frequenza cardiaca durante il sonno
    - Battiti cardiaci notturni
    - Andamento del cuore
    - Trend della frequenza cardiaca
    - Heart rate nel tempo

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