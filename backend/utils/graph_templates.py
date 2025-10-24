"""
Template Plotly per la generazione di grafici basati sui TypedDict.
Ogni template è una funzione che riceve dati strutturati e ritorna una specifica Plotly.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Any

from backend.models.results import (
    SleepStatisticsResult,
    SleepDistributionResult,
    SleepQualityCorrelationResult,
    KitchenStatisticsResult,
    KitchenUsagePatternResult,
    KitchenTemperatureAnalysisResult,
    MobilityAnalysisResult,
    DailyHeartRateResult
)
from backend.models.state import GraphData


# =============================================================================
# SLEEP DOMAIN - Grafici basati sui nuovi tool
# =============================================================================

def create_sleep_phases_pie(data: SleepDistributionResult) -> GraphData:
    """
    Genera un grafico a torta per la distribuzione delle fasi del sonno.
    Usa i dati del tool analyze_sleep_distribution.

    Base: rem_sleep, deep_sleep, light_sleep (ognuno con avg_minutes e percentage)
    """
    labels = ["REM", "Sonno Profondo", "Sonno Leggero"]
    values = [
        data["rem_sleep"]["avg_minutes"],
        data["deep_sleep"]["avg_minutes"],
        data["light_sleep"]["avg_minutes"]
    ]

    # Colori standard medicina del sonno
    colors = ['#9B59B6', '#3498DB', '#85C1E2']

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        marker=dict(colors=colors),
        textinfo='label+percent',
        textfont=dict(size=14),
        hovertemplate='<b>%{label}</b><br>%{value:.1f} minuti<br>%{percent}<extra></extra>'
    )])

    # Annotazione centrale con durata totale
    total_hours = data["total_sleep_minutes"] / 60
    fig.update_layout(
        title=f"Distribuzione Fasi del Sonno - Soggetto {data['subject_id']}",
        annotations=[dict(
            text=f"{total_hours:.1f}h",
            x=0.5, y=0.5,
            font_size=24,
            font_color='#2C3E50',
            showarrow=False
        )],
        height=400,
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.05
        )
    )

    return {
        "id": "sleep_phases_distribution",
        "title": "Distribuzione Fasi del Sonno",
        "type": "pie",
        "plotly_json": fig.to_dict()
    }


def create_sleep_efficiency_gauge(data: SleepDistributionResult) -> GraphData:
    """
    Genera un gauge per l'efficienza del sonno.
    Usa i dati del tool analyze_sleep_distribution.

    Base: sleep_efficiency (0-100%)
    """
    efficiency = data["sleep_efficiency"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=efficiency,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Efficienza del Sonno (%)", 'font': {'size': 20}},
        delta={'reference': 85, 'suffix': "%"},
        number={'suffix': "%"},
        gauge={
            'axis': {'range': [None, 100], 'ticksuffix': "%"},
            'bar': {'color': "#2C3E50"},
            'steps': [
                {'range': [0, 70], 'color': "#E74C3C"},  # Scarso
                {'range': [70, 85], 'color': "#F39C12"},  # Buono
                {'range': [85, 100], 'color': "#27AE60"}  # Eccellente
            ],
            'threshold': {
                'line': {'color': "black", 'width': 3},
                'thickness': 0.75,
                'value': 85
            }
        }
    ))

    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    return {
        "id": "sleep_efficiency_gauge",
        "title": "Efficienza del Sonno",
        "type": "indicator",
        "plotly_json": fig.to_dict()
    }


def create_sleep_statistics_dashboard(data: SleepStatisticsResult) -> GraphData:
    """
    Genera un dashboard con le statistiche chiave del sonno (media ± std dev).
    Usa i dati del tool analyze_sleep_statistics.

    Mostra 4 metriche principali con media e deviazione standard.
    """
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Durata Totale",
            "Sonno Profondo",
            "Risvegli",
            "Frequenza Cardiaca"
        ),
        specs=[
            [{"type": "indicator"}, {"type": "indicator"}],
            [{"type": "indicator"}, {"type": "indicator"}]
        ],
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )

    # Durata totale sonno (converti minuti in ore)
    total_sleep_avg = data["total_sleep_time"]["average"] / 60
    total_sleep_std = data["total_sleep_time"]["std_dev"] / 60

    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=total_sleep_avg,
        delta={
            'reference': total_sleep_std,
            'relative': False,
            'valueformat': '.1f',
            'suffix': 'h'
        },
        number={'suffix': " h", 'font': {'size': 32}},
        title={"text": f"Media ± {total_sleep_std:.1f}h"}
    ), row=1, col=1)

    # Sonno profondo
    deep_avg = data["deep_sleep_duration"]["average"]
    deep_std = data["deep_sleep_duration"]["std_dev"]

    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=deep_avg,
        delta={
            'reference': deep_std,
            'relative': False,
            'valueformat': '.0f',
            'suffix': 'm'
        },
        number={'suffix': " min", 'font': {'size': 32}},
        title={"text": f"Media ± {deep_std:.0f}m"}
    ), row=1, col=2)

    # Risvegli
    wakeup_avg = data["wakeup_count"]["average"]
    wakeup_std = data["wakeup_count"]["std_dev"]

    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=wakeup_avg,
        delta={
            'reference': wakeup_std,
            'relative': False,
            'valueformat': '.1f'
        },
        number={'suffix': " volte", 'font': {'size': 32}},
        title={"text": f"Media ± {wakeup_std:.1f}"}
    ), row=2, col=1)

    # Frequenza cardiaca
    hr_avg = data["hr_average"]["average"]
    hr_std = data["hr_average"]["std_dev"]

    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=hr_avg,
        delta={
            'reference': hr_std,
            'relative': False,
            'valueformat': '.0f',
            'suffix': ' bpm'
        },
        number={'suffix': " bpm", 'font': {'size': 32}},
        title={"text": f"Media ± {hr_std:.0f}"}
    ), row=2, col=2)

    fig.update_layout(
        height=500,
        margin=dict(t=100, b=20, l=20, r=20)
    )

    return {
        "id": "sleep_statistics_dashboard",
        "title": f"Statistiche del Sonno - Soggetto {data['subject_id']}",
        "type": "indicator",
        "plotly_json": fig.to_dict()
    }


def create_sleep_quality_bars(data: SleepQualityCorrelationResult) -> GraphData:
    """
    Genera un grafico a barre per i disturbi del sonno.
    Usa i dati del tool analyze_sleep_quality_correlation.

    Base: avg_wakeup_count, avg_out_of_bed_count
    """
    metrics = ["Risvegli", "Uscite dal letto"]
    values = [
        data["avg_wakeup_count"],
        data["avg_out_of_bed_count"]
    ]

    colors = ['#E67E22', '#E74C3C']

    fig = go.Figure(data=[go.Bar(
        x=metrics,
        y=values,
        marker=dict(color=colors),
        text=[f"{v:.1f}" for v in values],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Media: %{y:.2f} per notte<extra></extra>'
    )])

    fig.update_layout(
        title=f"Disturbi del Sonno - Soggetto {data['subject_id']}",
        yaxis_title="Frequenza Media per Notte",
        height=400,
        showlegend=False,
        yaxis=dict(range=[0, max(values) * 1.3] if max(values) > 0 else [0, 1])
    )

    return {
        "id": "sleep_quality_bars",
        "title": "Disturbi del Sonno",
        "type": "bar",
        "plotly_json": fig.to_dict()
    }


def create_sleep_correlation_heatmap(data: SleepQualityCorrelationResult) -> GraphData:
    """
    Genera una heatmap delle correlazioni tra interruzioni e qualità del sonno.
    Usa i dati del tool analyze_sleep_quality_correlation.

    Mostra visivamente la forza delle correlazioni con colori.
    """
    correlations = data["correlations"]

    # Struttura i dati per la heatmap
    z_values = [
        [correlations["wakeup_vs_sleep_time"],
         correlations["wakeup_vs_efficiency"],
         correlations["wakeup_vs_deep_sleep"]],
        [correlations["out_of_bed_vs_sleep_time"],
         correlations["out_of_bed_vs_efficiency"],
         correlations["out_of_bed_vs_deep_sleep"]]
    ]

    y_labels = ["Risvegli", "Uscite dal letto"]
    x_labels = ["Durata Sonno", "Efficienza", "Sonno Profondo"]

    # Crea annotazioni con i valori
    annotations = []
    for i, y_label in enumerate(y_labels):
        for j, x_label in enumerate(x_labels):
            value = z_values[i][j]
            color = "white" if abs(value) > 0.5 else "black"
            annotations.append(
                dict(
                    x=j,
                    y=i,
                    text=f"{value:.2f}",
                    showarrow=False,
                    font=dict(color=color, size=14)
                )
            )

    fig = go.Figure(data=go.Heatmap(
        z=z_values,
        x=x_labels,
        y=y_labels,
        colorscale='RdBu_r',  # Rosso = negativo, Blu = positivo
        zmid=0,
        zmin=-1,
        zmax=1,
        colorbar=dict(
            title="Correlazione",
            tickvals=[-1, -0.5, 0, 0.5, 1],
            ticktext=["-1<br>(forte negativa)", "-0.5", "0", "0.5", "1<br>(forte positiva)"]
        ),
        hovertemplate='%{y} vs %{x}<br>Correlazione: %{z:.3f}<extra></extra>'
    ))

    fig.update_layout(
        title=f"Correlazioni Interruzioni-Qualità - Soggetto {data['subject_id']}",
        annotations=annotations,
        height=400,
        xaxis=dict(side='bottom'),
        margin=dict(l=120, r=120, t=80, b=80)
    )

    return {
        "id": "sleep_correlation_heatmap",
        "title": "Correlazioni Sonno",
        "type": "heatmap",
        "plotly_json": fig.to_dict()
    }


def create_sleep_variability_box(data: SleepStatisticsResult) -> GraphData:
    """
    Genera box plot per mostrare la variabilità delle metriche del sonno.
    Usa i dati del tool analyze_sleep_statistics.

    Mostra min, Q1, mediana, Q3, max per le metriche principali.
    """
    # Preparazione dati per box plot
    # Approssimiamo Q1 e Q3 usando mean ± 0.675*std_dev (circa 25° e 75° percentile per distribuzione normale)

    metrics_names = ["Durata Totale (h)", "REM (min)", "Profondo (min)", "Leggero (min)"]

    # Converti durata totale in ore
    total_sleep_stats = data["total_sleep_time"]
    total_data = {
        "min": total_sleep_stats["min"] / 60,
        "median": total_sleep_stats["median"] / 60,
        "mean": total_sleep_stats["average"] / 60,
        "max": total_sleep_stats["max"] / 60,
        "q1": (total_sleep_stats["average"] - 0.675 * total_sleep_stats["std_dev"]) / 60,
        "q3": (total_sleep_stats["average"] + 0.675 * total_sleep_stats["std_dev"]) / 60
    }

    # REM
    rem_stats = data["rem_sleep_duration"]
    rem_data = {
        "min": rem_stats["min"],
        "median": rem_stats["median"],
        "mean": rem_stats["average"],
        "max": rem_stats["max"],
        "q1": rem_stats["average"] - 0.675 * rem_stats["std_dev"],
        "q3": rem_stats["average"] + 0.675 * rem_stats["std_dev"]
    }

    # Profondo
    deep_stats = data["deep_sleep_duration"]
    deep_data = {
        "min": deep_stats["min"],
        "median": deep_stats["median"],
        "mean": deep_stats["average"],
        "max": deep_stats["max"],
        "q1": deep_stats["average"] - 0.675 * deep_stats["std_dev"],
        "q3": deep_stats["average"] + 0.675 * deep_stats["std_dev"]
    }

    # Leggero
    light_stats = data["light_sleep_duration"]
    light_data = {
        "min": light_stats["min"],
        "median": light_stats["median"],
        "mean": light_stats["average"],
        "max": light_stats["max"],
        "q1": light_stats["average"] - 0.675 * light_stats["std_dev"],
        "q3": light_stats["average"] + 0.675 * light_stats["std_dev"]
    }

    all_data = [total_data, rem_data, deep_data, light_data]

    fig = go.Figure()

    colors = ['#3498DB', '#9B59B6', '#2ECC71', '#85C1E2']

    for i, (name, stats, color) in enumerate(zip(metrics_names, all_data, colors)):
        fig.add_trace(go.Box(
            y=[stats["min"], stats["q1"], stats["median"], stats["q3"], stats["max"]],
            name=name,
            marker_color=color,
            boxmean='sd',  # Mostra media e std dev
            hovertemplate=(
                f'<b>{name}</b><br>'
                'Max: %{y:.1f}<br>'
                'Q3: %{q3:.1f}<br>'
                'Mediana: %{median:.1f}<br>'
                'Q1: %{q1:.1f}<br>'
                'Min: %{y:.1f}<br>'
                '<extra></extra>'
            )
        ))

    fig.update_layout(
        title=f"Variabilità Metriche del Sonno - Soggetto {data['subject_id']}",
        yaxis_title="Valore",
        height=450,
        showlegend=True,
        hovermode='x unified'
    )

    return {
        "id": "sleep_variability_box",
        "title": "Variabilità del Sonno",
        "type": "box",
        "plotly_json": fig.to_dict()
    }


# =============================================================================
# KITCHEN DOMAIN - Grafici basati sui nuovi tool
# =============================================================================

def create_kitchen_statistics_dashboard(data: KitchenStatisticsResult) -> GraphData:
    """
    Genera un dashboard con le statistiche chiave delle attività in cucina (media ± std dev).
    Usa i dati del tool analyze_kitchen_statistics.

    Mostra 3 metriche principali con media e deviazione standard.
    """
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=(
            "Durata Attività",
            "Temperatura Max",
            "Frequenza Giornaliera"
        ),
        specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]],
        horizontal_spacing=0.15
    )

    # Durata attività
    duration_avg = data["duration_minutes"]["average"]
    duration_std = data["duration_minutes"]["std_dev"]

    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=duration_avg,
        delta={
            'reference': duration_std,
            'relative': False,
            'valueformat': '.1f',
            'suffix': 'm'
        },
        number={'suffix': " min", 'font': {'size': 32}},
        title={"text": f"Media ± {duration_std:.1f}m"}
    ), row=1, col=1)

    # Temperatura massima
    temp_avg = data["temperature_max"]["average"]
    temp_std = data["temperature_max"]["std_dev"]

    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=temp_avg,
        delta={
            'reference': temp_std,
            'relative': False,
            'valueformat': '.0f',
            'suffix': '°C'
        },
        number={'suffix': "°C", 'font': {'size': 32}},
        title={"text": f"Media ± {temp_std:.0f}°C"}
    ), row=1, col=2)

    # Attività per giorno
    freq_avg = data["activities_per_day"]["average"]
    freq_std = data["activities_per_day"]["std_dev"]

    fig.add_trace(go.Indicator(
        mode="number+delta",
        value=freq_avg,
        delta={
            'reference': freq_std,
            'relative': False,
            'valueformat': '.1f'
        },
        number={'suffix': " volte", 'font': {'size': 32}},
        title={"text": f"Media ± {freq_std:.1f}"}
    ), row=1, col=3)

    fig.update_layout(
        title=f"Statistiche Utilizzo Cucina - Soggetto {data['subject_id']}",
        height=400,
        margin=dict(t=100, b=20, l=20, r=20)
    )

    return {
        "id": "kitchen_statistics_dashboard",
        "title": "Statistiche Cucina",
        "type": "indicator",
        "plotly_json": fig.to_dict()
    }


def create_kitchen_timeslot_bar(data: KitchenUsagePatternResult) -> GraphData:
    """
    Genera un grafico a barre per l'utilizzo della cucina per fascia oraria.
    Usa i dati del tool analyze_kitchen_usage_pattern.

    Base: timeslot_distribution con count, avg_duration, percentage per ogni fascia
    """
    slots = ["Mattina", "Pranzo", "Cena"]
    distribution = data["timeslot_distribution"]

    values = [
        distribution["mattina"]["count"],
        distribution["pranzo"]["count"],
        distribution["cena"]["count"]
    ]
    percentages = [
        distribution["mattina"]["percentage"],
        distribution["pranzo"]["percentage"],
        distribution["cena"]["percentage"]
    ]

    colors = ['#F39C12', '#E67E22', '#C0392B']

    fig = go.Figure(data=[go.Bar(
        x=slots,
        y=values,
        marker=dict(color=colors),
        text=[f"{v}<br>({p:.1f}%)" for v, p in zip(values, percentages)],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Attività: %{y}<br>Percentuale: %{customdata:.1f}%<extra></extra>',
        customdata=percentages
    )])

    fig.update_layout(
        title=f"Utilizzo Cucina per Fascia Oraria - Soggetto {data['subject_id']}",
        xaxis_title="Fascia Oraria",
        yaxis_title="Numero Attività",
        height=400,
        showlegend=False,
        yaxis=dict(range=[0, max(values) * 1.3] if max(values) > 0 else [0, 1])
    )

    return {
        "id": "kitchen_timeslot_distribution",
        "title": "Utilizzo Cucina per Fascia Oraria",
        "type": "bar",
        "plotly_json": fig.to_dict()
    }


def create_kitchen_duration_by_timeslot(data: KitchenUsagePatternResult) -> GraphData:
    """
    Genera un grafico a barre che mostra la durata media per fascia oraria.
    Usa i dati del tool analyze_kitchen_usage_pattern.

    Mostra quanto tempo mediamente si passa in cucina in ogni fascia.
    """
    slots = ["Mattina", "Pranzo", "Cena"]
    distribution = data["timeslot_distribution"]

    durations = [
        distribution["mattina"]["avg_duration"],
        distribution["pranzo"]["avg_duration"],
        distribution["cena"]["avg_duration"]
    ]

    colors = ['#F39C12', '#E67E22', '#C0392B']

    fig = go.Figure(data=[go.Bar(
        x=slots,
        y=durations,
        marker=dict(color=colors),
        text=[f"{d:.1f} min" for d in durations],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Durata media: %{y:.1f} minuti<extra></extra>'
    )])

    fig.update_layout(
        title=f"Durata Media Attività per Fascia - Soggetto {data['subject_id']}",
        xaxis_title="Fascia Oraria",
        yaxis_title="Durata Media (minuti)",
        height=400,
        showlegend=False,
        yaxis=dict(range=[0, max(durations) * 1.3] if max(durations) > 0 else [0, 1])
    )

    return {
        "id": "kitchen_duration_by_timeslot",
        "title": "Durata per Fascia Oraria",
        "type": "bar",
        "plotly_json": fig.to_dict()
    }


def create_kitchen_temperature_distribution(data: KitchenTemperatureAnalysisResult) -> GraphData:
    """
    Genera un grafico a barre per la distribuzione delle attività per intensità di temperatura.
    Usa i dati del tool analyze_kitchen_temperature.

    Mostra quante attività sono a bassa/media/alta temperatura.
    """
    categories = ["Bassa Temp\n(<50°C)", "Media Temp\n(50-150°C)", "Alta Temp\n(>150°C)"]
    values = [
        data["low_temp_count"],
        data["medium_temp_count"],
        data["high_temp_count"]
    ]

    colors = ['#3498DB', '#F39C12', '#E74C3C']

    fig = go.Figure(data=[go.Bar(
        x=categories,
        y=values,
        marker=dict(color=colors),
        text=values,
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Attività: %{y}<extra></extra>'
    )])

    fig.update_layout(
        title=f"Distribuzione Intensità Cottura - Soggetto {data['subject_id']}",
        xaxis_title="Intensità",
        yaxis_title="Numero Attività",
        height=400,
        showlegend=False,
        yaxis=dict(range=[0, max(values) * 1.3] if max(values) > 0 else [0, 1])
    )

    return {
        "id": "kitchen_temperature_distribution",
        "title": "Distribuzione Intensità Cottura",
        "type": "bar",
        "plotly_json": fig.to_dict()
    }


def create_kitchen_temperature_gauge(data: KitchenTemperatureAnalysisResult) -> GraphData:
    """
    Genera un gauge per la temperatura media raggiunta in cucina.
    Usa i dati del tool analyze_kitchen_temperature.

    Mostra la temperatura media con range min-max.
    """
    avg_temp = data["avg_temperature"]
    min_temp = data["min_temperature"]
    max_temp = data["max_temperature"]

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=avg_temp,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Temperatura Media (°C)", 'font': {'size': 20}},
        delta={'reference': 100, 'suffix': "°C"},
        number={'suffix': "°C"},
        gauge={
            'axis': {'range': [0, 250], 'ticksuffix': "°C"},
            'bar': {'color': "#E74C3C"},
            'steps': [
                {'range': [0, 50], 'color': "#3498DB"},  # Freddo/riscaldare
                {'range': [50, 150], 'color': "#F39C12"},  # Cottura normale
                {'range': [150, 250], 'color': "#E74C3C"}  # Alta temperatura
            ],
            'threshold': {
                'line': {'color': "black", 'width': 3},
                'thickness': 0.75,
                'value': avg_temp
            }
        }
    ))

    fig.add_annotation(
        text=f"Range: {min_temp:.0f}°C - {max_temp:.0f}°C",
        xref="paper",
        yref="paper",
        x=0.5,
        y=-0.1,
        showarrow=False,
        font=dict(size=14)
    )

    fig.update_layout(
        height=350,
        margin=dict(l=20, r=20, t=60, b=60)
    )

    return {
        "id": "kitchen_temperature_gauge",
        "title": "Temperatura Media Cucina",
        "type": "indicator",
        "plotly_json": fig.to_dict()
    }


def create_kitchen_temp_by_timeslot(data: KitchenTemperatureAnalysisResult) -> GraphData:
    """
    Genera un grafico a barre per la temperatura media per fascia oraria.
    Usa i dati del tool analyze_kitchen_temperature.

    Mostra se si cucina più intensamente in certe fasce orarie.
    """
    slots = ["Mattina", "Pranzo", "Cena"]
    temp_by_slot = data["avg_temp_by_timeslot"]

    temperatures = [
        temp_by_slot.get("mattina", 0),
        temp_by_slot.get("pranzo", 0),
        temp_by_slot.get("cena", 0)
    ]

    colors = ['#F39C12', '#E67E22', '#C0392B']

    fig = go.Figure(data=[go.Bar(
        x=slots,
        y=temperatures,
        marker=dict(color=colors),
        text=[f"{t:.0f}°C" for t in temperatures],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Temp media: %{y:.1f}°C<extra></extra>'
    )])

    fig.update_layout(
        title=f"Temperatura Media per Fascia Oraria - Soggetto {data['subject_id']}",
        xaxis_title="Fascia Oraria",
        yaxis_title="Temperatura Media (°C)",
        height=400,
        showlegend=False,
        yaxis=dict(range=[0, max(temperatures) * 1.2] if max(temperatures) > 0 else [0, 1])
    )

    return {
        "id": "kitchen_temp_by_timeslot",
        "title": "Temperatura per Fascia Oraria",
        "type": "bar",
        "plotly_json": fig.to_dict()
    }


def create_kitchen_variability_box(data: KitchenStatisticsResult) -> GraphData:
    """
    Genera box plot per mostrare la variabilità delle metriche cucina.
    Usa i dati del tool analyze_kitchen_statistics.

    Mostra min, Q1, mediana, Q3, max per durata e temperatura.
    """
    metrics_names = ["Durata (min)", "Temperatura (°C)"]

    # Durata
    duration_stats = data["duration_minutes"]
    duration_data = {
        "min": duration_stats["min"],
        "median": duration_stats["median"],
        "mean": duration_stats["average"],
        "max": duration_stats["max"],
        "q1": duration_stats["average"] - 0.675 * duration_stats["std_dev"],
        "q3": duration_stats["average"] + 0.675 * duration_stats["std_dev"]
    }

    # Temperatura
    temp_stats = data["temperature_max"]
    temp_data = {
        "min": temp_stats["min"],
        "median": temp_stats["median"],
        "mean": temp_stats["average"],
        "max": temp_stats["max"],
        "q1": temp_stats["average"] - 0.675 * temp_stats["std_dev"],
        "q3": temp_stats["average"] + 0.675 * temp_stats["std_dev"]
    }

    all_data = [duration_data, temp_data]
    colors = ['#E67E22', '#E74C3C']

    fig = go.Figure()

    for i, (name, stats, color) in enumerate(zip(metrics_names, all_data, colors)):
        fig.add_trace(go.Box(
            y=[stats["min"], stats["q1"], stats["median"], stats["q3"], stats["max"]],
            name=name,
            marker_color=color,
            boxmean='sd',
            hovertemplate=(
                f'<b>{name}</b><br>'
                'Max: %{y:.1f}<br>'
                'Mediana: %{median:.1f}<br>'
                'Min: %{y:.1f}<br>'
                '<extra></extra>'
            )
        ))

    fig.update_layout(
        title=f"Variabilità Metriche Cucina - Soggetto {data['subject_id']}",
        yaxis_title="Valore",
        height=450,
        showlegend=True,
        hovermode='x unified'
    )

    return {
        "id": "kitchen_variability_box",
        "title": "Variabilità Cucina",
        "type": "box",
        "plotly_json": fig.to_dict()
    }

def create_mobility_room_bars(data: MobilityAnalysisResult) -> GraphData:
    """
    Genera un grafico a barre per la distribuzione nelle stanze.
    Base: room_distribution (chiavi dinamiche), room_percentages
    """
    room_dist = data["room_distribution"]
    room_pct = data["room_percentages"]

    # Ordina per frequenza
    sorted_rooms = sorted(room_dist.items(), key=lambda x: x[1], reverse=True)

    rooms = [room.replace("_", " ").title() for room, _ in sorted_rooms]
    counts = [count for _, count in sorted_rooms]
    percentages = [room_pct[room] for room, _ in sorted_rooms]

    fig = go.Figure(data=[go.Bar(
        x=rooms,
        y=counts,
        text=[f"{count}<br>{pct:.1f}%" for count, pct in zip(counts, percentages)],
        textposition='outside',
        marker=dict(
            color=counts,
            colorscale='Viridis',
            showscale=False
        ),
        hovertemplate='<b>%{x}</b><br>Rilevazioni: %{y}<br>Percentuale: %{text}<extra></extra>'
    )])

    fig.update_layout(
        title=f"Distribuzione Presenza per Stanza - Soggetto {data['subject_id']}",
        xaxis_title="Stanza",
        yaxis_title="Numero Rilevazioni",
        height=400,
        showlegend=False
    )

    return {
        "id": "mobility_room_distribution",
        "title": "Distribuzione Presenza per Stanza",
        "type": "bar",
        "plotly_json": fig.to_dict()
    }


def create_mobility_timeslot_bar(data: MobilityAnalysisResult) -> GraphData:
    """
    Genera un grafico a barre per l'attività di mobilità per fascia oraria.
    Base: time_slot_activity (chiavi dinamiche)
    """
    time_slot_activity = data["time_slot_activity"]

    # Ordine cronologico
    slot_order = ["notte", "mattina", "pomeriggio", "sera"]
    slots_labels = ["Notte", "Mattina", "Pomeriggio", "Sera"]

    # Filtra solo le chiavi presenti
    slots = []
    values = []
    for slot, label in zip(slot_order, slots_labels):
        if slot in time_slot_activity:
            slots.append(label)
            values.append(time_slot_activity[slot])

    colors = ['#34495E', '#F39C12', '#3498DB', '#9B59B6'][:len(values)]

    fig = go.Figure(data=[go.Bar(
        x=slots,
        y=values,
        marker=dict(color=colors),
        text=values,
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Rilevazioni: %{y}<extra></extra>'
    )])

    fig.update_layout(
        title=f"Attività per Fascia Oraria - Soggetto {data['subject_id']}",
        xaxis_title="Fascia Oraria",
        yaxis_title="Numero Rilevazioni",
        height=400,
        showlegend=False,
        yaxis=dict(range=[0, max(values) * 1.2] if values else [0, 1])
    )

    return {
        "id": "mobility_timeslot_activity",
        "title": "Attività per Fascia Oraria",
        "type": "bar",
        "plotly_json": fig.to_dict()
    }


def create_heart_rate_line(data: DailyHeartRateResult) -> GraphData:
    """
    Genera un grafico a linee per la frequenza cardiaca giornaliera.
    Base: daily_avg_hr (dict con date come chiavi)
    """
    daily_hr = data["daily_avg_hr"]

    # Ordina per data
    sorted_items = sorted(daily_hr.items())
    dates = [item[0] for item in sorted_items]
    hr_values = [item[1] for item in sorted_items]

    fig = go.Figure()

    # Linea principale
    fig.add_trace(go.Scatter(
        x=dates,
        y=hr_values,
        mode='lines+markers',
        name='Frequenza Cardiaca',
        line=dict(color='#E74C3C', width=2),
        marker=dict(size=8),
        hovertemplate='<b>%{x}</b><br>FC: %{y:.1f} bpm<extra></extra>'
    ))

    # Media del periodo
    avg_hr = sum(hr_values) / len(hr_values) if hr_values else 0
    fig.add_hline(
        y=avg_hr,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Media: {avg_hr:.1f} bpm",
        annotation_position="right"
    )

    fig.update_layout(
        title=f"Frequenza Cardiaca Notturna - Soggetto {data['subject_id']}",
        xaxis_title="Data",
        yaxis_title="Frequenza Cardiaca (bpm)",
        height=400,
        showlegend=False,
        hovermode='x unified'
    )

    return {
        "id": "heart_rate_timeline",
        "title": "Frequenza Cardiaca Notturna",
        "type": "line",
        "plotly_json": fig.to_dict()
    }




def create_no_data_placeholder(title: str) -> GraphData:
    """Crea un grafico placeholder quando i dati non sono disponibili"""
    fig = go.Figure()

    fig.add_annotation(
        text="Dati non disponibili",
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=20, color="gray")
    )

    fig.update_layout(
        title=title,
        height=400,
        xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        yaxis=dict(showgrid=False, showticklabels=False, zeroline=False)
    )

    return {
        "id": "no_data",
        "title": title,
        "type": "placeholder",
        "plotly_json": fig.to_dict()
    }