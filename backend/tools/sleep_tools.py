from __future__ import annotations

from datetime import timedelta
from typing import Annotated
from langchain_core.tools import tool
import pandas as pd

from backend.config.settings import SLEEP_DATA_PATH
from backend.models.results import SleepAnalysisResult, ErrorResult, SleepTrendData, DailyHeartRateResult


@tool
def analyze_sleep_changes(
    subject_id: Annotated[int, "ID of the subject to analyze, integer"],
    period: Annotated[str, "Period to analyze in format 'YYYY-MM-DD,YYYY-MM-DD' or 'last_N_days' (e.g., 'last_30_days')"]
) -> SleepAnalysisResult | ErrorResult:
    """
    Analyzes changes in a subject's sleep patterns over a specific period.
    Returns aggregate sleep metrics and trends.
    """
    df = pd.read_csv(SLEEP_DATA_PATH)
    df['data'] = pd.to_datetime(df['data'])


    # Filtra per soggetto
    df_subject = df[df['subject_id'] == subject_id].copy()

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
    df_period = df_subject[(df_subject['data'] >= start_date) & (df_subject['data'] <= end_date)]

    if df_period.empty:
        return ErrorResult(error="Nessun dato disponibile per il periodo specificato")

    # Calcola metriche aggregate
    results: SleepAnalysisResult = {
        "subject_id": subject_id,
        "period": f"{start_date.date()} to {end_date.date()}",
        "num_nights": len(df_period),
        "avg_total_sleep_hours": round(df_period['total_sleep_time'].mean() / 60, 2),
        "avg_rem_sleep_minutes": round(df_period['rem_sleep_duration'].mean(), 2),
        "avg_deep_sleep_minutes": round(df_period['deep_sleep_duration'].mean(), 2),
        "avg_light_sleep_minutes": round(df_period['light_sleep_duration'].mean(), 2),
        "avg_wakeup_count": round(df_period['wakeup_count'].mean(), 2),
        "avg_out_of_bed_count": round(df_period['out_of_bed_count'].mean(), 2),
        "avg_hr": round(df_period['hr_average'].mean(), 2),
        "avg_rr": round(df_period['rr_average'].mean(), 2),
        "sleep_efficiency": round((df_period['rem_sleep_duration'].mean() +
                                   df_period['deep_sleep_duration'].mean() +
                                   df_period['light_sleep_duration'].mean()) /
                                  df_period['total_sleep_time'].mean() * 100, 2),
        "trends": None
    }

    # Trend analysis (confronto prima/seconda metà del periodo)
    mid_point = start_date + (end_date - start_date) / 2
    first_half = df_period[df_period['data'] < mid_point]
    second_half = df_period[df_period['data'] >= mid_point]

    if len(first_half) > 0 and len(second_half) > 0:
        results["trends"] = SleepTrendData(
            sleep_time_change_minutes=round(second_half['total_sleep_time'].mean() - first_half['total_sleep_time'].mean(), 2),
            wakeup_count_change=round(second_half['wakeup_count'].mean() - first_half['wakeup_count'].mean(), 2),
            deep_sleep_change_minutes=round(second_half['deep_sleep_duration'].mean() - first_half['deep_sleep_duration'].mean(), 2)
        )

    return results


@tool
def analyze_daily_heart_rate(
  subject_id: Annotated[int, "ID of the subject to analyze, integer"],
  period: Annotated[str, "Period to analyze in format 'YYYY-MM-DD,YYYY-MM-DD' or 'last_N_days'"]
) -> DailyHeartRateResult | ErrorResult:
  """
  Returns the average heart rate (HR) of the subject during sleep over the specified period.
  """

  df = pd.read_csv(SLEEP_DATA_PATH)
  df['data'] = pd.to_datetime(df['data'])

  # Filtra per soggetto
  df_subject = df[df['subject_id'] == subject_id].copy()

  # Determina il periodo da analizzare
  if period.startswith('last_'):
      days = int(period.split('_')[1])
      end_date = df_subject['data'].max()
      start_date = max(df_subject['data'].min(), end_date - timedelta(days=days))
  else:
      dates = period.split(',')
      start_date = pd.to_datetime(dates[0])
      end_date = pd.to_datetime(dates[1])

  # Filtra i dati per il periodo selezionato
  df_period = df_subject[(df_subject['data'] >= start_date) & (df_subject['data'] <= end_date)]

  if df_period.empty:
      return ErrorResult(error="Nessun dato disponibile per il periodo specificato")

  # Calcola la media giornaliera del battito cardiaco
  daily_avg = df_period.groupby('data')['hr_average'].mean().round(2)
  daily_avg = {date.strftime('%Y-%m-%d'): float(hr) for date, hr in daily_avg.items()}

  return DailyHeartRateResult(
      subject_id=subject_id,
      period=f"{start_date.date()} to {end_date.date()}",
      daily_avg_hr=daily_avg
  )