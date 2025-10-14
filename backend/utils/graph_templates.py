"""
Template Plotly per la generazione di grafici basati sui TypedDict.
Ogni template è una funzione che riceve dati strutturati e ritorna una specifica Plotly.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Any

from backend.models.results import (
    SleepAnalysisResult,
    KitchenAnalysisResult,
    MobilityAnalysisResult,
    DailyHeartRateResult
)
from backend.models.state import GraphData


def create_sleep_phases_pie(data: SleepAnalysisResult) -> GraphData:
    """
    Genera un grafico a torta per la distribuzione delle fasi del sonno.
    Base: avg_rem/deep/light_sleep_minutes (sempre presenti)
    """
    labels = ["REM", "Sonno Profondo", "Sonno Leggero"]
    values = [
        data["avg_rem_sleep_minutes"],
        data["avg_deep_sleep_minutes"],
        data["avg_light_sleep_minutes"]
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
    fig.update_layout(
        title=f"Distribuzione Fasi del Sonno - Soggetto {data['subject_id']}",
        annotations=[dict(
            text=f"{data['avg_total_sleep_hours']:.1f}h",
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


def create_sleep_efficiency_gauge(data: SleepAnalysisResult) -> GraphData:
    """
    Genera un gauge per l'efficienza del sonno.
    Base: sleep_efficiency (sempre presente, range 0-100%)
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


def create_sleep_quality_bars(data: SleepAnalysisResult) -> GraphData:
    """
    Genera un grafico a barre per i problemi notturni.
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
        yaxis=dict(range=[0, max(values) * 1.3])
    )

    return {
        "id": "sleep_quality_bars",
        "title": "Disturbi del Sonno",
        "type": "bar",
        "plotly_json": fig.to_dict()
    }


def create_kitchen_timeslot_bar(data: KitchenAnalysisResult) -> GraphData:
    """
    Genera un grafico a barre per l'utilizzo della cucina per fascia oraria.
    Base: time_slot_distribution (sempre 3 chiavi: mattina, pranzo, cena)
    """
    slots = ["Mattina", "Pranzo", "Cena"]
    distribution = data["time_slot_distribution"]

    values = [distribution["mattina"], distribution["pranzo"], distribution["cena"]]

    # Colori che rappresentano i momenti della giornata
    colors = ['#F39C12', '#E67E22', '#C0392B']

    fig = go.Figure(data=[go.Bar(
        x=slots,
        y=values,
        marker=dict(color=colors),
        text=values,
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Attività: %{y}<extra></extra>'
    )])

    fig.update_layout(
        title=f"Utilizzo Cucina per Fascia Oraria - Soggetto {data['subject_id']}",
        xaxis_title="Fascia Oraria",
        yaxis_title="Numero Attività",
        height=400,
        showlegend=False,
        yaxis=dict(range=[0, max(values) * 1.2])
    )

    return {
        "id": "kitchen_timeslot_distribution",
        "title": "Utilizzo Cucina per Fascia Oraria",
        "type": "bar",
        "plotly_json": fig.to_dict()
    }


def create_kitchen_metrics_cards(data: KitchenAnalysisResult) -> GraphData:
    """
    Genera un dashboard con metriche chiave della cucina.
    Base: activities_per_day, avg_duration_minutes, total_cooking_time_hours
    """
    fig = make_subplots(
        rows=1, cols=3,
        subplot_titles=("Frequenza", "Durata Media", "Tempo Totale"),
        specs=[[{"type": "indicator"}, {"type": "indicator"}, {"type": "indicator"}]]
    )

    # Frequenza giornaliera
    fig.add_trace(go.Indicator(
        mode="number",
        value=data["activities_per_day"],
        title={"text": "Attività/giorno"},
        number={'suffix': " volte", 'font': {'size': 40}},
        domain={'x': [0, 0.33], 'y': [0, 1]}
    ), row=1, col=1)

    # Durata media
    fig.add_trace(go.Indicator(
        mode="number",
        value=data["avg_duration_minutes"],
        title={"text": "Durata media"},
        number={'suffix': " min", 'font': {'size': 40}},
        domain={'x': [0.33, 0.66], 'y': [0, 1]}
    ), row=1, col=2)

    # Tempo totale
    fig.add_trace(go.Indicator(
        mode="number",
        value=data["total_cooking_time_hours"],
        title={"text": "Tempo totale"},
        number={'suffix': " ore", 'font': {'size': 40}},
        domain={'x': [0.66, 1], 'y': [0, 1]}
    ), row=1, col=3)

    fig.update_layout(
        title=f"Metriche Cucina - Soggetto {data['subject_id']}",
        height=300,
        margin=dict(t=80, b=20)
    )

    return {
        "id": "kitchen_metrics_cards",
        "title": "Metriche Cucina",
        "type": "indicator",
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