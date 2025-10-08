import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configurazione della pagina
st.set_page_config(
    page_title="Demo Multi Agent LLM",
    page_icon="",
    layout="wide"
)

# URL del backend
BACKEND_URL = "http://localhost:8000"

# Titolo
st.title("Demo Multi Agent LLM")
st.markdown("---")

# Sidebar per configurazioni
with st.sidebar:
    st.header("Configurazioni")

    # Health check
    if st.button("Verifica Connessione"):
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if response.status_code == 200:
                st.success("Backend connesso!")
            else:
                st.error("Backend non disponibile")
        except Exception as e:
            st.error(f"Errore di connessione: {str(e)}")


def create_daily_heart_rate_chart(data):
    """Crea grafico per il battito cardiaco giornaliero"""
    if "error" in data:
        st.error(f"{data['error']}")
        return

    # Estrai i dati giornalieri
    daily_hr = data.get('daily_avg_hr', {})

    if not daily_hr:
        st.warning("Nessun dato disponibile per la frequenza cardiaca giornaliera")
        return

    # Converti in DataFrame
    hr_df = pd.DataFrame({
        'Data': list(daily_hr.keys()),
        'HR Media': list(daily_hr.values())
    })
    hr_df['Data'] = pd.to_datetime(hr_df['Data'])
    hr_df = hr_df.sort_values('Data')

    # Metriche principali
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("HR Media Periodo", f"{hr_df['HR Media'].mean():.1f} bpm")
    with col2:
        st.metric("HR Minima", f"{hr_df['HR Media'].min():.1f} bpm")
    with col3:
        st.metric("HR Massima", f"{hr_df['HR Media'].max():.1f} bpm")
    with col4:
        st.metric("Giorni Monitorati", len(hr_df))

    # Grafico temporale
    st.subheader("Andamento Frequenza Cardiaca Giornaliera")

    fig = go.Figure()

    # Linea principale
    fig.add_trace(go.Scatter(
        x=hr_df['Data'],
        y=hr_df['HR Media'],
        mode='lines+markers',
        name='HR Media',
        line=dict(color='#FF6B6B', width=3),
        marker=dict(size=8),
        hovertemplate='<b>Data:</b> %{x|%Y-%m-%d}<br><b>HR:</b> %{y:.1f} bpm<extra></extra>'
    ))

    # Media del periodo (linea tratteggiata)
    avg_hr = hr_df['HR Media'].mean()
    fig.add_hline(
        y=avg_hr,
        line_dash="dash",
        line_color="gray",
        annotation_text=f"Media: {avg_hr:.1f} bpm",
        annotation_position="right"
    )

    # Range normale (60-100 bpm)
    fig.add_hrect(
        y0=60, y1=100,
        fillcolor="lightgreen",
        opacity=0.1,
        layer="below",
        line_width=0,
        annotation_text="Range Normale",
        annotation_position="top left"
    )

    fig.update_layout(
        height=400,
        xaxis_title="Data",
        yaxis_title="Frequenza Cardiaca (bpm)",
        hovermode='x unified',
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

    # Statistiche aggiuntive
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribuzione HR")
        fig_hist = px.histogram(
            hr_df,
            x='HR Media',
            nbins=20,
            color_discrete_sequence=['#FF6B6B'],
            labels={'HR Media': 'Frequenza Cardiaca (bpm)', 'count': 'Frequenza'}
        )
        fig_hist.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig_hist, use_container_width=True)

    with col2:
        st.subheader("Variabilita HR")

        # Calcola variazioni giornaliere
        hr_df['Variazione'] = hr_df['HR Media'].diff()

        # Statistiche variabilità
        stats_df = pd.DataFrame({
            'Metrica': ['Deviazione Standard', 'Variazione Media', 'Range'],
            'Valore': [
                f"{hr_df['HR Media'].std():.2f} bpm",
                f"{abs(hr_df['Variazione'].mean()):.2f} bpm/giorno",
                f"{hr_df['HR Media'].max() - hr_df['HR Media'].min():.1f} bpm"
            ]
        })

        st.dataframe(stats_df, hide_index=True, use_container_width=True)

        # Indicatore stabilità
        std_hr = hr_df['HR Media'].std()
        if std_hr < 3:
            stability = "Molto Stabile"
            st.success(f"**Stabilita HR:** {stability}")
        elif std_hr < 5:
            stability = "Stabile"
            st.info(f"**Stabilita HR:** {stability}")
        elif std_hr < 7:
            stability = "Moderata"
            st.warning(f"**Stabilita HR:** {stability}")
        else:
            stability = "Variabile"
            st.error(f"**Stabilita HR:** {stability}")


def create_sleep_charts(data):
    """Crea grafici per i dati del sonno"""
    if "error" in data:
        st.error(f"{data['error']}")
        return

    # Metriche principali
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Notti Analizzate", data.get("num_nights", 0))
    with col2:
        st.metric("Ore Sonno Medio", f"{data.get('avg_total_sleep_hours', 0):.1f}h")
    with col3:
        st.metric("Efficienza Sonno", f"{data.get('sleep_efficiency', 0):.1f}%")
    with col4:
        st.metric("Risvegli Medi", f"{data.get('avg_wakeup_count', 0):.1f}")

    # Grafico fasi del sonno
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Fasi del Sonno")
        sleep_phases = pd.DataFrame({
            'Fase': ['REM', 'Sonno Profondo', 'Sonno Leggero'],
            'Minuti': [
                data.get('avg_rem_sleep_minutes', 0),
                data.get('avg_deep_sleep_minutes', 0),
                data.get('avg_light_sleep_minutes', 0)
            ]
        })

        fig = px.pie(sleep_phases, values='Minuti', names='Fase',
                     color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#95E1D3'],
                     hole=0.4)
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Parametri Vitali")
        vitals_data = pd.DataFrame({
            'Parametro': ['Frequenza Cardiaca', 'Frequenza Respiratoria'],
            'Valore': [data.get('avg_hr', 0), data.get('avg_rr', 0)],
            'Unita': ['bpm', 'rpm']
        })

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=vitals_data['Parametro'],
            y=vitals_data['Valore'],
            text=[f"{v:.1f} {u}" for v, u in zip(vitals_data['Valore'], vitals_data['Unita'])],
            textposition='auto',
            marker_color=['#FF6B6B', '#4ECDC4']
        ))
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    # Trend (se disponibili)
    if data.get('trends'):
        st.subheader("Trend nel Periodo")
        trends = data['trends']

        col1, col2, col3 = st.columns(3)
        with col1:
            change = trends.get('sleep_time_change_minutes', 0)
            st.metric(
                "Variazione Tempo Sonno",
                f"{abs(change):.1f} min",
                delta=f"{change:+.1f} min",
                delta_color="normal" if change >= 0 else "inverse"
            )
        with col2:
            change = trends.get('wakeup_count_change', 0)
            st.metric(
                "Variazione Risvegli",
                f"{abs(change):.1f}",
                delta=f"{change:+.1f}",
                delta_color="inverse" if change >= 0 else "normal"
            )
        with col3:
            change = trends.get('deep_sleep_change_minutes', 0)
            st.metric(
                "Variazione Sonno Profondo",
                f"{abs(change):.1f} min",
                delta=f"{change:+.1f} min",
                delta_color="normal" if change >= 0 else "inverse"
            )


def create_kitchen_charts(data):
    """Crea grafici per i dati della cucina"""
    if "error" in data:
        st.error(f"{data['error']}")
        return

    # Metriche principali
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Attivita Totali", data.get("total_activities", 0))
    with col2:
        st.metric("Attivita/Giorno", f"{data.get('activities_per_day', 0):.1f}")
    with col3:
        st.metric("Durata Media", f"{data.get('avg_duration_minutes', 0):.1f} min")
    with col4:
        st.metric("Temp. Media Max", f"{data.get('avg_temperature_max', 0):.1f} C")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribuzione per Fascia Oraria")
        time_dist = data.get('time_slot_distribution', {})

        if time_dist:
            time_df = pd.DataFrame({
                'Fascia': ['Mattina', 'Pranzo', 'Cena'],
                'Attivita': [
                    time_dist.get('mattina', 0),
                    time_dist.get('pranzo', 0),
                    time_dist.get('cena', 0)
                ]
            })

            fig = px.bar(time_df, x='Fascia', y='Attivita',
                         color='Attivita',
                         color_continuous_scale='Oranges',
                         text='Attivita')
            fig.update_traces(textposition='outside')
            fig.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Tempo Totale di Cottura")
        total_hours = data.get('total_cooking_time_hours', 0)

        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=total_hours,
            title={'text': "Ore Totali"},
            gauge={
                'axis': {'range': [None, max(total_hours * 1.5, 10)]},
                'bar': {'color': "#FF6B6B"},
                'steps': [
                    {'range': [0, total_hours * 0.5], 'color': "lightgray"},
                    {'range': [total_hours * 0.5, total_hours], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': total_hours * 0.9
                }
            }
        ))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    # Trend
    if data.get('trends'):
        st.subheader("Trend nel Periodo")
        trends = data['trends']

        col1, col2 = st.columns(2)
        with col1:
            change = trends.get('activity_frequency_change', 0)
            st.metric(
                "Variazione Frequenza Attivita",
                f"{abs(change):.2f} attivita/giorno",
                delta=f"{change:+.2f}",
                delta_color="normal" if change >= 0 else "inverse"
            )
        with col2:
            change = trends.get('avg_duration_change_minutes', 0)
            st.metric(
                "Variazione Durata Media",
                f"{abs(change):.1f} min",
                delta=f"{change:+.1f} min",
                delta_color="normal" if change >= 0 else "inverse"
            )


def create_mobility_charts(data):
    """Crea grafici per i dati della mobilita"""
    if "error" in data:
        st.error(f"{data['error']}")
        return

    # Metriche principali
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Rilevazioni Totali", data.get("total_detections", 0))
    with col2:
        st.metric("Rilevazioni/Giorno", f"{data.get('detections_per_day', 0):.1f}")
    with col3:
        st.metric("Durata Media", f"{data.get('avg_duration_minutes', 0):.1f} min")
    with col4:
        st.metric("Tempo Attivo Totale", f"{data.get('total_active_time_hours', 0):.1f}h")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribuzione per Stanza")
        room_dist = data.get('room_distribution', {})
        room_pct = data.get('room_percentages', {})

        if room_dist:
            room_df = pd.DataFrame({
                'Stanza': list(room_dist.keys()),
                'Rilevazioni': list(room_dist.values()),
                'Percentuale': [room_pct.get(room, 0) for room in room_dist.keys()]
            })

            fig = px.bar(room_df, x='Stanza', y='Rilevazioni',
                         text='Percentuale',
                         color='Rilevazioni',
                         color_continuous_scale='Viridis',
                         labels={'Stanza': 'Stanza', 'Rilevazioni': 'Numero Rilevazioni'})
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Percentuale Tempo per Stanza")
        if room_pct:
            room_pct_df = pd.DataFrame({
                'Stanza': list(room_pct.keys()),
                'Percentuale': list(room_pct.values())
            })

            fig = px.pie(room_pct_df, values='Percentuale', names='Stanza',
                         color_discrete_sequence=px.colors.qualitative.Set3,
                         hole=0.4)
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

    # Attività per fascia oraria
    if data.get('time_slot_activity'):
        st.subheader("Attivita per Fascia Oraria")
        time_slots = data['time_slot_activity']

        time_df = pd.DataFrame({
            'Fascia': list(time_slots.keys()),
            'Attivita': list(time_slots.values())
        })

        # Ordina per fascia oraria logica
        order = ['notte', 'mattina', 'pomeriggio', 'sera']
        time_df['Fascia'] = pd.Categorical(time_df['Fascia'], categories=order, ordered=True)
        time_df = time_df.sort_values('Fascia')

        fig = px.line(time_df, x='Fascia', y='Attivita',
                      markers=True,
                      line_shape='spline',
                      color_discrete_sequence=['#4ECDC4'])
        fig.update_traces(marker=dict(size=12), line=dict(width=3))
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

    # Trend
    if data.get('trends'):
        st.subheader("Trend nel Periodo")
        trends = data['trends']

        col1, col2 = st.columns(2)
        with col1:
            change = trends.get('activity_frequency_change', 0)
            st.metric(
                "Variazione Frequenza Attivita",
                f"{abs(change):.2f} rilevazioni/giorno",
                delta=f"{change:+.2f}",
                delta_color="normal" if change >= 0 else "inverse"
            )
        with col2:
            change = trends.get('avg_duration_change_minutes', 0)
            st.metric(
                "Variazione Durata Media",
                f"{abs(change):.1f} min",
                delta=f"{change:+.1f} min",
                delta_color="normal" if change >= 0 else "inverse"
            )


# Input della domanda
question = st.text_area(
    "Domanda:",
    placeholder="Es: Come ha dormito e come ha cucinato il soggetto 2 nell'ultima settimana?",
    height=100
)

# Bottone per inviare la query
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
           <style>
           div.stButton > button:first-child {
               background-color: #374957;
               color: white;
           }
           </style>
           """, unsafe_allow_html=True)
    submit_button = st.button("Invia", use_container_width=True)

# Gestione della risposta
if submit_button:
    if not question.strip():
        st.warning("Inserisci una domanda prima di inviare!")
    else:
        # Mostra spinner durante il caricamento
        with st.spinner("Elaborazione in corso..."):
            try:
                # Chiamata al backend
                response = requests.post(
                    f"{BACKEND_URL}/query",
                    json={
                        "question": question,
                        "max_iterations": 10
                    },
                    timeout=120
                )

                if response.status_code == 200:
                    data = response.json()

                    st.subheader("Risposta Finale")
                    st.markdown(data["answer"])

                    # Grafici per ogni agente
                    if data.get("structured_responses"):
                        st.markdown("---")

                        for response in data["structured_responses"]:
                            agent_name = response.get("agent_name", "Unknown")
                            agent_data = response.get("data", {})

                            # Mappa titoli e colori per tutti gli agenti
                            agent_info = {
                                "sleep_agent": ("Analisi del Sonno", "#FF6B6B"),
                                "heart_freq_agent": ("Analisi Frequenza Cardiaca", "#FF4444"),
                                "kitchen_agent": ("Analisi Attivita Cucina", "#FFA500"),
                                "mobility_agent": ("Analisi Mobilita", "#4ECDC4")
                            }

                            title, color = agent_info.get(agent_name, ("Analisi", "#808080"))

                            st.markdown(f"### {title}")

                            # Crea grafici specifici per tipo di agente
                            if agent_name == "sleep_agent":
                                create_sleep_charts(agent_data)
                            elif agent_name == "heart_freq_agent":
                                create_daily_heart_rate_chart(agent_data)
                            elif agent_name == "kitchen_agent":
                                create_kitchen_charts(agent_data)
                            elif agent_name == "mobility_agent":
                                create_mobility_charts(agent_data)
                            else:
                                # Gestione agenti sconosciuti o futuri
                                st.info(f"Tipo di agente '{agent_name}' non riconosciuto")
                                st.json(agent_data)

                            st.markdown("---")

                else:
                    st.error(f"Errore {response.status_code}: {response.text}")

            except requests.exceptions.Timeout:
                st.error("Timeout: Il backend sta impiegando troppo tempo a rispondere.")
            except requests.exceptions.ConnectionError:
                st.error("Errore di connessione: Assicurati che il backend sia in esecuzione su http://localhost:8000")
            except Exception as e:
                st.error(f"Errore imprevisto: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "@RiccardoCeccarani"
    "</div>",
    unsafe_allow_html=True
)