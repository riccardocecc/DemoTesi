from __future__ import annotations

from datetime import timedelta
from typing import Annotated
from langchain_core.tools import tool
import pandas as pd
import numpy as np

from backend.config.settings import SLEEP_DATA_PATH
from backend.models.results import (
    SleepStatisticsResult,
    SleepDistributionResult,
    SleepQualityCorrelationResult,
    DailyHeartRateResult,
    ErrorResult
)


@tool
def analyze_sleep_statistics(
        subject_id: Annotated[int, "ID of the subject to analyze, integer"],
        period: Annotated[
            str, "Period to analyze in format 'YYYY-MM-DD,YYYY-MM-DD' or 'last_N_days' (e.g., 'last_30_days')"]
) -> SleepStatisticsResult | ErrorResult:
    """
    Calcola statistiche descrittive dettagliate per ogni metrica del sonno.

    Questo tool fornisce un'analisi statistica completa includendo:
    - Media (average): valore medio della metrica nel periodo
    - Mediana (median): valore centrale, utile per identificare valori tipici
    - Deviazione standard (std_dev): misura della variabilità dei dati
    - Minimo e Massimo: range completo dei valori osservati

    Le metriche analizzate sono:
    - total_sleep_time: durata totale del sonno in minuti
    - rem_sleep_duration: durata fase REM in minuti
    - deep_sleep_duration: durata sonno profondo in minuti
    - light_sleep_duration: durata sonno leggero in minuti
    - wakeup_count: numero di risvegli per notte
    - out_of_bed_count: numero di uscite dal letto per notte
    - hr_average: frequenza cardiaca media notturna (bpm)
    - rr_average: frequenza respiratoria media (respiri/min)

    Usa questo tool quando l'utente chiede:
    - "Statistiche del sonno"
    - "Media e deviazione standard"
    - "Analisi statistica del sonno"
    - "Variabilità del sonno"
    - "Range dei valori del sonno"

    Args:
        subject_id: ID numerico del soggetto da analizzare
        period: Periodo in formato 'last_N_days' o 'YYYY-MM-DD,YYYY-MM-DD'

    Returns:
        SleepStatisticsResult con statistiche per ogni metrica, oppure ErrorResult
    """
    try:
        df = pd.read_csv(SLEEP_DATA_PATH)
        df['data'] = pd.to_datetime(df['data'])

        # Filtra per soggetto
        df_subject = df[df['subject_id'] == subject_id].copy()

        if df_subject.empty:
            return ErrorResult(error=f"Nessun dato trovato per il soggetto {subject_id}")

        # Parsing del periodo
        if period.startswith('last_'):
            days = int(period.split('_')[1])
            end_date = df_subject['data'].max()
            start_date = end_date - timedelta(days=days)
        else:
            dates = period.split(',')
            start_date = pd.to_datetime(dates[0])
            end_date = pd.to_datetime(dates[1])

        # Filtra per periodo
        df_period = df_subject[(df_subject['data'] >= start_date) &
                               (df_subject['data'] <= end_date)]

        if df_period.empty:
            return ErrorResult(error="Nessun dato disponibile per il periodo specificato")

        # Funzione helper per calcolare statistiche
        def calc_stats(series):
            return {
                "average": round(float(series.mean()), 2),
                "median": round(float(series.median()), 2),
                "std_dev": round(float(series.std()), 2),
                "min": round(float(series.min()), 2),
                "max": round(float(series.max()), 2)
            }

        # Calcola statistiche per ogni metrica
        result: SleepStatisticsResult = {
            "subject_id": subject_id,
            "period": f"{start_date.date()} to {end_date.date()}",
            "num_nights": len(df_period),
            "total_sleep_time": calc_stats(df_period['total_sleep_time']),
            "rem_sleep_duration": calc_stats(df_period['rem_sleep_duration']),
            "deep_sleep_duration": calc_stats(df_period['deep_sleep_duration']),
            "light_sleep_duration": calc_stats(df_period['light_sleep_duration']),
            "wakeup_count": calc_stats(df_period['wakeup_count']),
            "out_of_bed_count": calc_stats(df_period['out_of_bed_count']),
            "hr_average": calc_stats(df_period['hr_average']),
            "rr_average": calc_stats(df_period['rr_average'])
        }

        return result

    except Exception as e:
        return ErrorResult(error=f"Errore nell'analisi statistica: {str(e)}")


@tool
def analyze_sleep_distribution(
        subject_id: Annotated[int, "ID of the subject to analyze, integer"],
        period: Annotated[
            str, "Period to analyze in format 'YYYY-MM-DD,YYYY-MM-DD' or 'last_N_days' (e.g., 'last_30_days')"]
) -> SleepDistributionResult | ErrorResult:
    """
    Analizza la distribuzione del tempo nelle diverse fasi del sonno.

    Questo tool calcola come il tempo di sonno viene distribuito tra le fasi:
    - REM (Rapid Eye Movement): fase associata ai sogni e consolidamento memoria
    - Sonno Profondo (Deep Sleep): fase rigenerativa, recupero fisico
    - Sonno Leggero (Light Sleep): fase di transizione

    Fornisce sia valori assoluti (minuti medi) che percentuali sul totale.
    Include anche il calcolo dell'efficienza del sonno: percentuale di tempo
    effettivamente dormito rispetto al tempo totale a letto.

    Metriche calcolate:
    - avg_minutes: durata media in minuti per ogni fase
    - percentage: % di tempo in ogni fase sul sonno totale
    - total_sleep_minutes: durata media totale del sonno
    - sleep_efficiency: efficienza = (tempo dormito / tempo a letto) * 100

    Usa questo tool quando l'utente chiede:
    - "Distribuzione delle fasi del sonno"
    - "Quanto tempo passa in REM/profondo/leggero"
    - "Percentuale di sonno profondo"
    - "Composizione del sonno"
    - "Come è suddiviso il suo sonno"

    Args:
        subject_id: ID numerico del soggetto da analizzare
        period: Periodo in formato 'last_N_days' o 'YYYY-MM-DD,YYYY-MM-DD'

    Returns:
        SleepDistributionResult con distribuzione fasi e efficienza, oppure ErrorResult
    """
    try:
        df = pd.read_csv(SLEEP_DATA_PATH)
        df['data'] = pd.to_datetime(df['data'])

        df_subject = df[df['subject_id'] == subject_id].copy()

        if df_subject.empty:
            return ErrorResult(error=f"Nessun dato trovato per il soggetto {subject_id}")

        # Parsing del periodo
        if period.startswith('last_'):
            days = int(period.split('_')[1])
            end_date = df_subject['data'].max()
            start_date = end_date - timedelta(days=days)
        else:
            dates = period.split(',')
            start_date = pd.to_datetime(dates[0])
            end_date = pd.to_datetime(dates[1])

        df_period = df_subject[(df_subject['data'] >= start_date) &
                               (df_subject['data'] <= end_date)]

        if df_period.empty:
            return ErrorResult(error="Nessun dato disponibile per il periodo specificato")

        # Calcola medie per ogni fase
        avg_rem = df_period['rem_sleep_duration'].mean()
        avg_deep = df_period['deep_sleep_duration'].mean()
        avg_light = df_period['light_sleep_duration'].mean()
        total_sleep = avg_rem + avg_deep + avg_light

        # Calcola percentuali
        rem_pct = (avg_rem / total_sleep * 100) if total_sleep > 0 else 0
        deep_pct = (avg_deep / total_sleep * 100) if total_sleep > 0 else 0
        light_pct = (avg_light / total_sleep * 100) if total_sleep > 0 else 0

        # Calcola efficienza del sonno
        # Efficienza = (tempo effettivamente dormito / tempo totale) * 100
        avg_total_time = df_period['total_sleep_time'].mean()
        efficiency = (total_sleep / avg_total_time * 100) if avg_total_time > 0 else 0

        result: SleepDistributionResult = {
            "subject_id": subject_id,
            "period": f"{start_date.date()} to {end_date.date()}",
            "num_nights": len(df_period),
            "rem_sleep": {
                "avg_minutes": round(avg_rem, 2),
                "percentage": round(rem_pct, 2)
            },
            "deep_sleep": {
                "avg_minutes": round(avg_deep, 2),
                "percentage": round(deep_pct, 2)
            },
            "light_sleep": {
                "avg_minutes": round(avg_light, 2),
                "percentage": round(light_pct, 2)
            },
            "total_sleep_minutes": round(total_sleep, 2),
            "sleep_efficiency": round(efficiency, 2)
        }

        return result

    except Exception as e:
        return ErrorResult(error=f"Errore nell'analisi della distribuzione: {str(e)}")


@tool
def analyze_sleep_quality_correlation(
        subject_id: Annotated[int, "ID of the subject to analyze, integer"],
        period: Annotated[
            str, "Period to analyze in format 'YYYY-MM-DD,YYYY-MM-DD' or 'last_N_days' (e.g., 'last_30_days')"]
) -> SleepQualityCorrelationResult | ErrorResult:
    """
    Analizza la correlazione tra interruzioni del sonno e qualità/durata del sonno.

    Questo tool studia la relazione tra i disturbi notturni e la qualità del sonno:

    1. Interruzioni analizzate:
       - wakeup_count: numero di risvegli notturni
       - out_of_bed_count: numero di volte che il soggetto esce dal letto

    2. Indicatori di qualità correlati:
       - total_sleep_time: durata totale del sonno
       - sleep_efficiency: efficienza del sonno
       - deep_sleep_duration: quantità di sonno profondo (il più rigenerativo)

    3. Coefficienti di correlazione (range -1 a +1):
       - Valore negativo: più interruzioni → meno qualità (relazione inversa)
       - Valore positivo: più interruzioni → più qualità (inusuale)
       - Vicino a 0: nessuna relazione lineare
       - |r| > 0.7: correlazione forte
       - |r| 0.3-0.7: correlazione moderata
       - |r| < 0.3: correlazione debole

    4. Metriche aggregate:
       - avg_wakeup_count: media risvegli per notte
       - avg_out_of_bed_count: media uscite dal letto per notte
       - avg_total_sleep_hours: durata media del sonno
       - avg_sleep_efficiency: efficienza media
       - avg_deep_sleep_minutes: quantità media sonno profondo

    Usa questo tool quando l'utente chiede:
    - "I risvegli influenzano la qualità del sonno?"
    - "Correlazione tra interruzioni e sonno"
    - "L'alzarsi di notte peggiora il sonno?"
    - "Relazione tra disturbi e durata del sonno"
    - "Impatto dei risvegli sul sonno profondo"

    Args:
        subject_id: ID numerico del soggetto da analizzare
        period: Periodo in formato 'last_N_days' o 'YYYY-MM-DD,YYYY-MM-DD'

    Returns:
        SleepQualityCorrelationResult con coefficienti di correlazione e metriche, oppure ErrorResult
    """
    try:
        df = pd.read_csv(SLEEP_DATA_PATH)
        df['data'] = pd.to_datetime(df['data'])

        df_subject = df[df['subject_id'] == subject_id].copy()


        if df_subject.empty:
            return ErrorResult(error=f"Nessun dato trovato per il soggetto {subject_id}")

        # Parsing del periodo
        if period.startswith('last_'):
            days = int(period.split('_')[1])
            end_date = df_subject['data'].max()
            start_date = end_date - timedelta(days=days)
        else:
            dates = period.split(',')
            start_date = pd.to_datetime(dates[0])
            end_date = pd.to_datetime(dates[1])

        df_period = df_subject[(df_subject['data'] >= start_date) &
                               (df_subject['data'] <= end_date)].copy()

        if df_period.empty:
            return ErrorResult(error="Nessun dato disponibile per il periodo specificato")

        if len(df_period) < 3:
            return ErrorResult(error="Servono almeno 3 notti di dati per calcolare correlazioni affidabili")

        # Calcola efficienza del sonno per ogni notte
        df_period['sleep_efficiency'] = (
                (df_period['rem_sleep_duration'] +
                 df_period['deep_sleep_duration'] +
                 df_period['light_sleep_duration']) /
                df_period['total_sleep_time'] * 100
        )

        # Calcola correlazioni
        # Correlazione wakeup_count con metriche di qualità
        corr_wakeup_sleep_time = df_period['wakeup_count'].corr(df_period['total_sleep_time'])
        corr_wakeup_efficiency = df_period['wakeup_count'].corr(df_period['sleep_efficiency'])
        corr_wakeup_deep = df_period['wakeup_count'].corr(df_period['deep_sleep_duration'])

        # Correlazione out_of_bed_count con metriche di qualità
        corr_outbed_sleep_time = df_period['out_of_bed_count'].corr(df_period['total_sleep_time'])
        corr_outbed_efficiency = df_period['out_of_bed_count'].corr(df_period['sleep_efficiency'])
        corr_outbed_deep = df_period['out_of_bed_count'].corr(df_period['deep_sleep_duration'])

        # Gestisci NaN (succede se una colonna ha varianza zero)
        def safe_corr(value):
            return round(float(value), 3) if not pd.isna(value) else 0.0

        result: SleepQualityCorrelationResult = {
            "subject_id": subject_id,
            "period": f"{start_date.date()} to {end_date.date()}",
            "num_nights": len(df_period),
            "avg_wakeup_count": round(df_period['wakeup_count'].mean(), 2),
            "avg_out_of_bed_count": round(df_period['out_of_bed_count'].mean(), 2),
            "avg_total_sleep_hours": round(df_period['total_sleep_time'].mean() / 60, 2),
            "avg_sleep_efficiency": round(df_period['sleep_efficiency'].mean(), 2),
            "avg_deep_sleep_minutes": round(df_period['deep_sleep_duration'].mean(), 2),
            "correlations": {
                "wakeup_vs_sleep_time": safe_corr(corr_wakeup_sleep_time),
                "wakeup_vs_efficiency": safe_corr(corr_wakeup_efficiency),
                "wakeup_vs_deep_sleep": safe_corr(corr_wakeup_deep),
                "out_of_bed_vs_sleep_time": safe_corr(corr_outbed_sleep_time),
                "out_of_bed_vs_efficiency": safe_corr(corr_outbed_efficiency),
                "out_of_bed_vs_deep_sleep": safe_corr(corr_outbed_deep)
            }
        }

        return result

    except Exception as e:
        return ErrorResult(error=f"Errore nell'analisi delle correlazioni: {str(e)}")


@tool
def analyze_daily_heart_rate(
        subject_id: Annotated[int, "ID of the subject to analyze, integer"],
        period: Annotated[str, "Period to analyze in format 'YYYY-MM-DD,YYYY-MM-DD' or 'last_N_days'"]
) -> DailyHeartRateResult | ErrorResult:
    """
    Restituisce la frequenza cardiaca media del soggetto durante il sonno nel periodo specificato.

    Questo tool è specializzato nell'analisi della frequenza cardiaca notturna:
    - Fornisce la FC media per ogni singola notte
    - Utile per identificare trend e anomalie nel tempo
    - La FC notturna è un indicatore importante della salute cardiovascolare

    Valori tipici FC notturna:
    - Adulti: 40-60 bpm (più basso del giorno, normale)
    - Valori elevati possono indicare stress, febbre, o disturbi del sonno
    - Variazioni significative giorno-per-giorno meritano attenzione

    Usa questo tool quando l'utente chiede:
    - "Frequenza cardiaca durante il sonno"
    - "Battiti notturni"
    - "Andamento del cuore di notte"
    - "FC nel tempo"
    - "Trend frequenza cardiaca"

    Args:
        subject_id: ID numerico del soggetto da analizzare
        period: Periodo in formato 'last_N_days' o 'YYYY-MM-DD,YYYY-MM-DD'

    Returns:
        DailyHeartRateResult con FC giornaliera, oppure ErrorResult
    """
    try:
        df = pd.read_csv(SLEEP_DATA_PATH)
        df['data'] = pd.to_datetime(df['data'])

        df_subject = df[df['subject_id'] == subject_id].copy()

        if df_subject.empty:
            return ErrorResult(error=f"Nessun dato trovato per il soggetto {subject_id}")

        # Parsing del periodo
        if period.startswith('last_'):
            days = int(period.split('_')[1])
            end_date = df_subject['data'].max()
            start_date = max(df_subject['data'].min(), end_date - timedelta(days=days))
        else:
            dates = period.split(',')
            start_date = pd.to_datetime(dates[0])
            end_date = pd.to_datetime(dates[1])

        df_period = df_subject[(df_subject['data'] >= start_date) &
                               (df_subject['data'] <= end_date)]

        if df_period.empty:
            return ErrorResult(error="Nessun dato disponibile per il periodo specificato")

        # Calcola media giornaliera
        daily_avg = df_period.groupby('data')['hr_average'].mean().round(2)
        daily_avg = {date.strftime('%Y-%m-%d'): float(hr) for date, hr in daily_avg.items()}

        return DailyHeartRateResult(
            subject_id=subject_id,
            period=f"{start_date.date()} to {end_date.date()}",
            daily_avg_hr=daily_avg
        )

    except Exception as e:
        return ErrorResult(error=f"Errore nell'analisi della frequenza cardiaca: {str(e)}")