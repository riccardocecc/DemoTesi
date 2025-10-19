from __future__ import annotations

from datetime import timedelta
from typing import Annotated
from langchain_core.tools import tool
import pandas as pd
import numpy as np

from backend.config.settings import KITCHEN_DATA_PATH
from backend.models.results import (
    KitchenStatisticsResult,
    KitchenUsagePatternResult,
    KitchenTemperatureAnalysisResult,
    ErrorResult
)


@tool
def analyze_kitchen_statistics(
        subject_id: Annotated[int, "ID of the subject to analyze, integer"],
        period: Annotated[
            str, "Period to analyze in format 'YYYY-MM-DD,YYYY-MM-DD' or 'last_N_days' (e.g., 'last_30_days')"]
) -> KitchenStatisticsResult | ErrorResult:
    """
    Calcola statistiche descrittive dettagliate per le attività in cucina.

    Questo tool fornisce un'analisi statistica completa includendo:
    - Media (average): valore medio della metrica nel periodo
    - Mediana (median): valore centrale, utile per identificare valori tipici
    - Deviazione standard (std_dev): misura della variabilità dei dati
    - Minimo e Massimo: range completo dei valori osservati

    Le metriche analizzate sono:
    - durata_attivita_minuti: durata di ogni attività in cucina
    - temperatura_max: temperatura massima raggiunta durante l'attività
    - activities_per_day: numero di attività giornaliere

    Usa questo tool quando l'utente chiede:
    - "Statistiche utilizzo cucina"
    - "Media e variabilità attività cucina"
    - "Analisi statistica cucina"
    - "Range durata attività"
    - "Quanto tempo passa in cucina mediamente"

    Args:
        subject_id: ID numerico del soggetto da analizzare
        period: Periodo in formato 'last_N_days' o 'YYYY-MM-DD,YYYY-MM-DD'

    Returns:
        KitchenStatisticsResult con statistiche per ogni metrica, oppure ErrorResult
    """
    try:
        df = pd.read_csv(KITCHEN_DATA_PATH)
        df['timestamp_picco'] = pd.to_datetime(df['timestamp_picco'])
        df['start_time_attivita'] = pd.to_datetime(df['start_time_attivita'])

        df_subject = df[df['subject_id'] == subject_id].copy()

        if df_subject.empty:
            return ErrorResult(error=f"Nessun dato trovato per il soggetto {subject_id}")

        # Parsing del periodo
        if period.startswith('last_'):
            days = int(period.split('_')[1])
            end_date = df_subject['timestamp_picco'].max()
            start_date = end_date - timedelta(days=days)
        else:
            dates = period.split(',')
            start_date = pd.to_datetime(dates[0])
            end_date = pd.to_datetime(dates[1])

        df_period = df_subject[
            (df_subject['timestamp_picco'] >= start_date) &
            (df_subject['timestamp_picco'] <= end_date)
            ].copy()

        if df_period.empty:
            return ErrorResult(error="Nessun dato disponibile per il periodo specificato")

        # Calcola attività per giorno
        num_days = (end_date - start_date).days + 1
        activities_per_day_series = df_period.groupby(df_period['timestamp_picco'].dt.date).size()

        # Funzione helper per calcolare statistiche
        def calc_stats(series):
            return {
                "average": round(float(series.mean()), 2),
                "median": round(float(series.median()), 2),
                "std_dev": round(float(series.std()), 2),
                "min": round(float(series.min()), 2),
                "max": round(float(series.max()), 2)
            }

        result: KitchenStatisticsResult = {
            "subject_id": subject_id,
            "period": f"{start_date.date()} to {end_date.date()}",
            "total_activities": len(df_period),
            "num_days": num_days,
            "duration_minutes": calc_stats(df_period['durata_attivita_minuti']),
            "temperature_max": calc_stats(df_period['temperatura_max']),
            "activities_per_day": calc_stats(activities_per_day_series)
        }

        return result

    except Exception as e:
        return ErrorResult(error=f"Errore nell'analisi statistica cucina: {str(e)}")


@tool
def analyze_kitchen_usage_pattern(
        subject_id: Annotated[int, "ID of the subject to analyze, integer"],
        period: Annotated[
            str, "Period to analyze in format 'YYYY-MM-DD,YYYY-MM-DD' or 'last_N_days' (e.g., 'last_30_days')"]
) -> KitchenUsagePatternResult | ErrorResult:
    """
    Analizza i pattern di utilizzo della cucina per fasce orarie.

    Questo tool studia quando e come viene utilizzata la cucina:

    1. Distribuzione per fascia oraria:
       - mattina: attività mattutine (colazione, caffè)
       - pranzo: attività del pranzo
       - cena: attività serali

    2. Metriche per ogni fascia:
       - count: numero totale di attività
       - avg_duration: durata media in minuti
       - percentage: percentuale sul totale delle attività

    3. Metriche aggregate:
       - total_cooking_time_hours: tempo totale in cucina
       - activities_per_day: media attività giornaliere
       - most_active_slot: fascia oraria più utilizzata

    Usa questo tool quando l'utente chiede:
    - "Quando usa di più la cucina?"
    - "Pattern utilizzo cucina"
    - "Distribuzione attività per pasto"
    - "Orari preferiti per cucinare"
    - "Analisi fasce orarie cucina"

    Args:
        subject_id: ID numerico del soggetto da analizzare
        period: Periodo in formato 'last_N_days' o 'YYYY-MM-DD,YYYY-MM-DD'

    Returns:
        KitchenUsagePatternResult con pattern temporali, oppure ErrorResult
    """
    try:
        df = pd.read_csv(KITCHEN_DATA_PATH)
        df['timestamp_picco'] = pd.to_datetime(df['timestamp_picco'])

        df_subject = df[df['subject_id'] == subject_id].copy()

        if df_subject.empty:
            return ErrorResult(error=f"Nessun dato trovato per il soggetto {subject_id}")

        # Parsing del periodo
        if period.startswith('last_'):
            days = int(period.split('_')[1])
            end_date = df_subject['timestamp_picco'].max()
            start_date = end_date - timedelta(days=days)
        else:
            dates = period.split(',')
            start_date = pd.to_datetime(dates[0])
            end_date = pd.to_datetime(dates[1])

        df_period = df_subject[
            (df_subject['timestamp_picco'] >= start_date) &
            (df_subject['timestamp_picco'] <= end_date)
            ].copy()

        if df_period.empty:
            return ErrorResult(error="Nessun dato disponibile per il periodo specificato")

        num_days = (end_date - start_date).days + 1
        total_activities = len(df_period)

        # Analizza per fascia oraria
        timeslot_groups = df_period.groupby('fascia_oraria')

        timeslot_distribution = {}
        for slot in ['mattina', 'pranzo', 'cena']:
            if slot in timeslot_groups.groups:
                slot_data = timeslot_groups.get_group(slot)
                count = len(slot_data)
                timeslot_distribution[slot] = {
                    "count": count,
                    "avg_duration": round(slot_data['durata_attivita_minuti'].mean(), 2),
                    "percentage": round(count / total_activities * 100, 2)
                }
            else:
                timeslot_distribution[slot] = {
                    "count": 0,
                    "avg_duration": 0.0,
                    "percentage": 0.0
                }

        # Trova fascia più attiva
        most_active_slot = max(timeslot_distribution.items(), key=lambda x: x[1]["count"])[0]

        result: KitchenUsagePatternResult = {
            "subject_id": subject_id,
            "period": f"{start_date.date()} to {end_date.date()}",
            "total_activities": total_activities,
            "activities_per_day": round(total_activities / num_days, 2),
            "total_cooking_time_hours": round(df_period['durata_attivita_minuti'].sum() / 60, 2),
            "timeslot_distribution": timeslot_distribution,
            "most_active_slot": most_active_slot
        }

        return result

    except Exception as e:
        return ErrorResult(error=f"Errore nell'analisi pattern cucina: {str(e)}")


@tool
def analyze_kitchen_temperature(
        subject_id: Annotated[int, "ID of the subject to analyze, integer"],
        period: Annotated[
            str, "Period to analyze in format 'YYYY-MM-DD,YYYY-MM-DD' or 'last_N_days' (e.g., 'last_30_days')"]
) -> KitchenTemperatureAnalysisResult | ErrorResult:
    """
    Analizza le temperature raggiunte durante le attività in cucina.

    Questo tool studia l'intensità dell'uso della cucina attraverso le temperature:

    1. Statistiche temperatura:
       - avg_temperature: temperatura media raggiunta
       - max_temperature: temperatura massima registrata
       - min_temperature: temperatura minima registrata

    2. Distribuzione per intensità:
       - low_temp_count: attività a bassa temperatura (<50°C, es. riscaldare)
       - medium_temp_count: attività a media temperatura (50-150°C, es. cotture normali)
       - high_temp_count: attività ad alta temperatura (>150°C, es. fritture, forno)

    3. Correlazioni:
       - temp_vs_duration: correlazione tra temperatura e durata
         (temperature più alte richiedono attività più lunghe?)

    4. Pattern per fascia oraria:
       - avg_temp_by_timeslot: temperatura media per mattina/pranzo/cena

    Usa questo tool quando l'utente chiede:
    - "Temperature in cucina"
    - "Intensità utilizzo cucina"
    - "Tipo di cotture"
    - "Quanto scalda quando cucina"
    - "Analisi temperature cottura"

    Args:
        subject_id: ID numerico del soggetto da analizzare
        period: Periodo in formato 'last_N_days' o 'YYYY-MM-DD,YYYY-MM-DD'

    Returns:
        KitchenTemperatureAnalysisResult con analisi temperature, oppure ErrorResult
    """
    try:
        df = pd.read_csv(KITCHEN_DATA_PATH)
        df['timestamp_picco'] = pd.to_datetime(df['timestamp_picco'])

        df_subject = df[df['subject_id'] == subject_id].copy()

        if df_subject.empty:
            return ErrorResult(error=f"Nessun dato trovato per il soggetto {subject_id}")

        # Parsing del periodo
        if period.startswith('last_'):
            days = int(period.split('_')[1])
            end_date = df_subject['timestamp_picco'].max()
            start_date = end_date - timedelta(days=days)
        else:
            dates = period.split(',')
            start_date = pd.to_datetime(dates[0])
            end_date = pd.to_datetime(dates[1])

        df_period = df_subject[
            (df_subject['timestamp_picco'] >= start_date) &
            (df_subject['timestamp_picco'] <= end_date)
            ].copy()

        if df_period.empty:
            return ErrorResult(error="Nessun dato disponibile per il periodo specificato")

        # Statistiche temperatura
        avg_temp = df_period['temperatura_max'].mean()
        max_temp = df_period['temperatura_max'].max()
        min_temp = df_period['temperatura_max'].min()

        # Distribuzione per intensità
        low_temp_count = len(df_period[df_period['temperatura_max'] < 50])
        medium_temp_count = len(df_period[(df_period['temperatura_max'] >= 50) & (df_period['temperatura_max'] <= 150)])
        high_temp_count = len(df_period[df_period['temperatura_max'] > 150])

        # Correlazione temperatura vs durata
        if len(df_period) >= 3:
            temp_vs_duration_corr = df_period['temperatura_max'].corr(df_period['durata_attivita_minuti'])
            temp_vs_duration = round(float(temp_vs_duration_corr), 3) if not pd.isna(temp_vs_duration_corr) else 0.0
        else:
            temp_vs_duration = 0.0

        # Temperature medie per fascia oraria
        avg_temp_by_timeslot = {}
        for slot in ['mattina', 'pranzo', 'cena']:
            slot_data = df_period[df_period['fascia_oraria'] == slot]
            if len(slot_data) > 0:
                avg_temp_by_timeslot[slot] = round(slot_data['temperatura_max'].mean(), 2)
            else:
                avg_temp_by_timeslot[slot] = 0.0

        result: KitchenTemperatureAnalysisResult = {
            "subject_id": subject_id,
            "period": f"{start_date.date()} to {end_date.date()}",
            "avg_temperature": round(avg_temp, 2),
            "max_temperature": round(max_temp, 2),
            "min_temperature": round(min_temp, 2),
            "low_temp_count": low_temp_count,
            "medium_temp_count": medium_temp_count,
            "high_temp_count": high_temp_count,
            "temp_vs_duration_correlation": temp_vs_duration,
            "avg_temp_by_timeslot": avg_temp_by_timeslot
        }

        return result

    except Exception as e:
        return ErrorResult(error=f"Errore nell'analisi temperatura cucina: {str(e)}")