from typing_extensions import TypedDict
from typing import Optional, Dict


class MetricStatistics(TypedDict):
    """Statistiche descrittive per una singola metrica"""
    average: float
    median: float
    std_dev: float
    min: float
    max: float


class SleepStatisticsResult(TypedDict):
    """
    Risultato dell'analisi statistica completa del sonno.
    Contiene statistiche descrittive (media, mediana, deviazione standard, min, max)
    per ogni metrica del sonno.
    """
    subject_id: int
    period: str
    num_nights: int
    total_sleep_time: MetricStatistics
    rem_sleep_duration: MetricStatistics
    deep_sleep_duration: MetricStatistics
    light_sleep_duration: MetricStatistics
    wakeup_count: MetricStatistics
    out_of_bed_count: MetricStatistics
    hr_average: MetricStatistics
    rr_average: MetricStatistics


class SleepPhaseData(TypedDict):
    """Dati per una singola fase del sonno"""
    avg_minutes: float
    percentage: float


class SleepDistributionResult(TypedDict):
    """
    Risultato dell'analisi della distribuzione delle fasi del sonno.
    Mostra come il tempo di sonno è distribuito tra REM, profondo e leggero,
    con valori assoluti e percentuali.
    """
    subject_id: int
    period: str
    num_nights: int
    rem_sleep: SleepPhaseData
    deep_sleep: SleepPhaseData
    light_sleep: SleepPhaseData
    total_sleep_minutes: float
    sleep_efficiency: float


class CorrelationData(TypedDict):
    """Coefficienti di correlazione tra interruzioni e qualità del sonno"""
    wakeup_vs_sleep_time: float
    wakeup_vs_efficiency: float
    wakeup_vs_deep_sleep: float
    out_of_bed_vs_sleep_time: float
    out_of_bed_vs_efficiency: float
    out_of_bed_vs_deep_sleep: float


class SleepQualityCorrelationResult(TypedDict):
    """
    Risultato dell'analisi delle correlazioni tra interruzioni del sonno
    e metriche di qualità (durata, efficienza, sonno profondo).
    I coefficienti di correlazione variano da -1 a +1.
    """
    subject_id: int
    period: str
    num_nights: int
    avg_wakeup_count: float
    avg_out_of_bed_count: float
    avg_total_sleep_hours: float
    avg_sleep_efficiency: float
    avg_deep_sleep_minutes: float
    correlations: CorrelationData


class DailyHeartRateResult(TypedDict):
    """Risultato del tool analyze_daily_heart_rate"""
    subject_id: int
    period: str
    daily_avg_hr: Dict[str, float]


# --- KITCHEN DOMAIN ---

class KitchenStatisticsResult(TypedDict):
    """
    Risultato dell'analisi statistica completa delle attività in cucina.
    Contiene statistiche descrittive per durata, temperatura e frequenza.
    """
    subject_id: int
    period: str
    total_activities: int
    num_days: int
    duration_minutes: MetricStatistics
    temperature_max: MetricStatistics
    activities_per_day: MetricStatistics


class TimeslotStats(TypedDict):
    """Statistiche per una fascia oraria"""
    count: int
    avg_duration: float
    percentage: float


class TimeslotDistribution(TypedDict):
    """Distribuzione attività per fascia oraria"""
    mattina: TimeslotStats
    pranzo: TimeslotStats
    cena: TimeslotStats


class KitchenUsagePatternResult(TypedDict):
    """
    Risultato dell'analisi dei pattern di utilizzo della cucina.
    Mostra quando e come viene utilizzata la cucina.
    """
    subject_id: int
    period: str
    total_activities: int
    activities_per_day: float
    total_cooking_time_hours: float
    timeslot_distribution: TimeslotDistribution
    most_active_slot: str


class KitchenTemperatureAnalysisResult(TypedDict):
    """
    Risultato dell'analisi delle temperature in cucina.
    Studia l'intensità dell'uso attraverso le temperature raggiunte.
    """
    subject_id: int
    period: str
    avg_temperature: float
    max_temperature: float
    min_temperature: float
    low_temp_count: int
    medium_temp_count: int
    high_temp_count: int
    temp_vs_duration_correlation: float
    avg_temp_by_timeslot: dict[str, float]

class TimeSlotDistribution(TypedDict):
    mattina: int
    pranzo: int
    cena: int


class KitchenTrendData(TypedDict):
    """Rappresenta le variazioni nelle attività in cucina su un periodo di osservazione."""
    activity_frequency_change: float
    avg_duration_change_minutes: float


class KitchenAnalysisResult(TypedDict):
    """Risultati aggregati dell'analisi delle attività in cucina."""
    subject_id: int
    period: str
    total_activities: int
    activities_per_day: float
    avg_duration_minutes: float
    avg_temperature_max: float
    total_cooking_time_hours: float
    time_slot_distribution: TimeSlotDistribution
    trends: Optional[KitchenTrendData]


# --- MOBILITY DOMAIN ---

class RoomDistribution(TypedDict, total=False):
    """Distribution dinamica delle stanze"""
    cucina: int
    soggiorno: int
    camera_letto: int
    bagno: int
    ingresso: int


class RoomPercentages(TypedDict, total=False):
    """Percentuali dinamiche per stanza"""
    cucina: float
    soggiorno: float
    camera_letto: float
    bagno: float
    ingresso: float


class TimeSlotActivity(TypedDict, total=False):
    """Attività per fascia oraria"""
    notte: int
    mattina: int
    pomeriggio: int
    sera: int


class MobilityTrendData(TypedDict):
    """Rappresenta le variazioni nelle attività di mobilità indoor su un periodo di osservazione."""
    activity_frequency_change: float
    avg_duration_change_minutes: float


class MobilityAnalysisResult(TypedDict):
    """Risultati aggregati dell'analisi della mobilità indoor."""
    subject_id: int
    period: str
    total_detections: int
    detections_per_day: float
    avg_duration_minutes: float
    total_active_time_hours: float
    room_distribution: RoomDistribution
    room_percentages: RoomPercentages
    time_slot_activity: TimeSlotActivity
    trends: Optional[MobilityTrendData]


# --- ERROR HANDLING ---

class ErrorResult(TypedDict):
    error: str