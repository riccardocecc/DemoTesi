from typing_extensions import TypedDict
from typing import Optional
class SleepTrendData(TypedDict):
   """Rappresenta le variazioni nei parametri del sonno su un periodo di osservazione"""
   sleep_time_change_minutes: float
   wakeup_count_change: float
   deep_sleep_change_minutes: float

class KitchenTrendData(TypedDict):
    """Rappresenta le variazioni nelle attività in cucina su un periodo di osservazione."""
    activity_frequency_change: float
    avg_duration_change_minutes: float

class MobilityTrendData(TypedDict):
    """Rappresenta le variazioni nelle attività di mobilità indoor su un periodo di osservazione."""
    activity_frequency_change: float
    avg_duration_change_minutes: float


class SleepAnalysisResult(TypedDict):
    """Risultati aggregati dell'analisi del sonno per un soggetto e un periodo specifico."""
    subject_id: int
    period: str
    num_nights: int
    avg_total_sleep_hours: float
    avg_rem_sleep_minutes: float
    avg_deep_sleep_minutes: float
    avg_light_sleep_minutes: float
    avg_wakeup_count: float
    avg_out_of_bed_count: float
    avg_hr: float
    avg_rr: float
    sleep_efficiency: float
    trends: Optional[SleepTrendData]

class TimeSlotDistribution(TypedDict):
    mattina: int
    pranzo: int
    cena: int

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


class DailyHeartRateResult(TypedDict):
    """Risultato del tool analyze_daily_heart_rate"""
    subject_id: int
    period: str
    daily_avg_hr: dict[str, float]



class ErrorResult(TypedDict):
    error: str
