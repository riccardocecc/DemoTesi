from __future__ import annotations

from datetime import timedelta
from typing import Annotated
from langchain_core.tools import tool
import pandas as pd

from backend.config.settings import KITCHEN_DATA_PATH
from backend.models.results import ErrorResult, KitchenAnalysisResult, TimeSlotDistribution, KitchenTrendData


@tool
def analyze_kitchen_activity(
    subject_id: Annotated[int, "ID of the subject to analyze, integer"],
    period: Annotated[str, "Period to analyze in format 'YYYY-MM-DD,YYYY-MM-DD' or 'last_N_days' (e.g., 'last_30_days')"]
) -> KitchenAnalysisResult | ErrorResult:
    """
    Analyzes a subject's kitchen activity over a specific period.
    Returns usage frequency, average duration, and temporal patterns.
    """
    df = pd.read_csv(KITCHEN_DATA_PATH)
    df['timestamp_picco'] = pd.to_datetime(df['timestamp_picco'])
    df['start_time_attivita'] = pd.to_datetime(df['start_time_attivita'])


    df_subject = df[df['subject_id'] == subject_id].copy()

    if period.startswith('last_'):
        days = int(period.split('_')[1])
        end_date = df_subject['timestamp_picco'].max()
        start_date = end_date - timedelta(days=days)
    else:
        dates = period.split(',')
        start_date = pd.to_datetime(dates[0])
        end_date = pd.to_datetime(dates[1])




    df_period = df_subject[(df_subject['timestamp_picco'] >= start_date) &
                           (df_subject['timestamp_picco'] <= end_date)]

    if df_period.empty:
        return ErrorResult(error="Nessun dato disponibile per il periodo specificato")  # ← CAMBIA QUI



    num_days = (end_date - start_date).days + 1
    fascia_dist = df_period['fascia_oraria'].value_counts()

    results: KitchenAnalysisResult = {
        "subject_id": subject_id,
        "period": f"{start_date.date()} to {end_date.date()}",
        "total_activities": len(df_period),
        "activities_per_day": round(len(df_period) / num_days, 2),
        "avg_duration_minutes": round(df_period['durata_attivita_minuti'].mean(), 2),
        "avg_temperature_max": round(df_period['temperatura_max'].mean(), 2),
        "total_cooking_time_hours": round(df_period['durata_attivita_minuti'].sum() / 60, 2),
        "time_slot_distribution": TimeSlotDistribution(
            mattina=int(fascia_dist.get('mattina', 0)),
            pranzo=int(fascia_dist.get('pranzo', 0)),
            cena=int(fascia_dist.get('cena', 0))
        ),
        "trends": None
    }

    # Trend analysis
    mid_point = start_date + (end_date - start_date) / 2
    first_half = df_period[df_period['timestamp_picco'] < mid_point]
    second_half = df_period[df_period['timestamp_picco'] >= mid_point]

    if len(first_half) > 0 and len(second_half) > 0:
        days_first = (mid_point - start_date).days
        days_second = (end_date - mid_point).days
        results["trends"] = KitchenTrendData(
            activity_frequency_change=round((len(second_half) / days_second) - (len(first_half) / days_first), 2),
            avg_duration_change_minutes=round(second_half['durata_attivita_minuti'].mean() -
                                                 first_half['durata_attivita_minuti'].mean(), 2)
        )

    return results