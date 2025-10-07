from __future__ import annotations

from datetime import timedelta
from typing import Annotated
from langchain_core.tools import tool
import pandas as pd

from backend.config.settings import SENSOR_DATA_PATH
from backend.models.results import ErrorResult, MobilityAnalysisResult, MobilityTrendData
@tool
def analyze_mobility_patterns(
    subject_id: Annotated[int, "ID of the subject to analyze, integer"],
    period: Annotated[str, "Period to analyze in format 'YYYY-MM-DD,YYYY-MM-DD' or 'last_N_days' (e.g., 'last_30_days')"]
) -> MobilityAnalysisResult | ErrorResult:
    """
    Analyzes a subject's mobility patterns using environmental sensors.
    Returns activity per room, movement frequency, and temporal patterns.
    """
    df = pd.read_csv(SENSOR_DATA_PATH)
    df['timestamp'] = pd.to_datetime(df['timestamp'])


    df_subject = df[df['subject_id'] == subject_id].copy()


    if period.startswith('last_'):
        days = int(period.split('_')[1])
        end_date = df_subject['timestamp'].max()
        start_date = end_date - timedelta(days=days)
    else:
        dates = period.split(',')
        start_date = pd.to_datetime(dates[0])
        end_date = pd.to_datetime(dates[1])


    df_period = df_subject[(df_subject['timestamp'] >= start_date) &
                           (df_subject['timestamp'] <= end_date)]

    if df_period.empty:
        return ErrorResult(error="Nessun dato disponibile per il periodo specificato")


    num_days = (end_date - start_date).days + 1




    room_dist = df_period['room'].value_counts()

    df_period['hour'] = df_period['timestamp'].dt.hour
    df_period['time_slot'] = df_period['hour'].apply(
        lambda h: 'notte' if h < 6 else 'mattina' if h < 12 else 'pomeriggio' if h < 18 else 'sera'
    )
    time_slot_dist = df_period['time_slot'].value_counts()

    results: MobilityAnalysisResult = {
        "subject_id": subject_id,
        "period": f"{start_date.date()} to {end_date.date()}",
        "total_detections": len(df_period),
        "detections_per_day": round(len(df_period) / num_days, 2),
        "avg_duration_minutes": round(df_period['duration_seconds'].mean() / 60, 2),
        "total_active_time_hours": round(df_period['duration_seconds'].sum() / 3600, 2),
        "room_distribution": {room: int(count) for room, count in room_dist.items()},
        "room_percentages": {
            room: round(count / len(df_period) * 100, 2)
            for room, count in room_dist.items()
        },
        "time_slot_activity": {
            slot: int(count) for slot, count in time_slot_dist.items()
        },
        "trends": None
    }



    results["time_slot_activity"] = {slot: int(count) for slot, count in time_slot_dist.items()}



    mid_point = start_date + (end_date - start_date) / 2
    first_half = df_period[df_period['timestamp'] < mid_point]
    second_half = df_period[df_period['timestamp'] >= mid_point]

    if len(first_half) > 0 and len(second_half) > 0:
        days_first = (mid_point - start_date).days
        days_second = (end_date - mid_point).days
        results["trends"] = MobilityTrendData(
            activity_frequency_change=round((len(second_half) / days_second) - (len(first_half) / days_first), 2),
            avg_duration_change_minutes=round((second_half['duration_seconds'].mean() -
                                                  first_half['duration_seconds'].mean()) / 60, 2)
        )

    return results