import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Configurazione della pagina
st.set_page_config(
    page_title="Demo Multi Agent LLM",
    page_icon="🤖",
    layout="wide"
)

# URL del backend
BACKEND_URL = "http://localhost:8000"

# Titolo
st.title("🤖 Demo Multi Agent LLM")
st.markdown("---")

# Sidebar per configurazioni
with st.sidebar:
    st.header("⚙️ Configurazioni")
    max_iterations = st.slider(
        "Iterazioni massime",
        min_value=5,
        max_value=50,
        value=10,
        step=5
    )

    st.markdown("---")

    # Health check
    if st.button("🔍 Verifica Connessione"):
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ Backend connesso!")
            else:
                st.error("❌ Backend non disponibile")
        except Exception as e:
            st.error(f"❌ Errore di connessione: {str(e)}")


# Funzioni per creare grafici
def create_sleep_charts(data):
    """Crea grafici per i dati del sonno"""
    if "error" in data:
        st.error(f"❌ {data['error']}")
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
            'Unità': ['bpm', 'rpm']
        })

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=vitals_data['Parametro'],
            y=vitals_data['Valore'],
            text=[f"{v:.1f} {u}" for v, u in zip(vitals_data['Valore'], vitals_data['Unità'])],
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
        st.error(f"❌ {data['error']}")
        return

    # Metriche principali
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Attività Totali", data.get("total_activities", 0))
    with col2:
        st.metric("Attività/Giorno", f"{data.get('activities_per_day', 0):.1f}")
    with col3:
        st.metric("Durata Media", f"{data.get('avg_duration_minutes', 0):.1f} min")
    with col4:
        st.metric("Temp. Media Max", f"{data.get('avg_temperature_max', 0):.1f}°C")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Distribuzione per Fascia Oraria")
        time_dist = data.get('time_slot_distribution', {})

        if time_dist:
            time_df = pd.DataFrame({
                'Fascia': ['Mattina', 'Pranzo', 'Cena'],
                'Attività': [
                    time_dist.get('mattina', 0),
                    time_dist.get('pranzo', 0),
                    time_dist.get('cena', 0)
                ]
            })

            fig = px.bar(time_df, x='Fascia', y='Attività',
                         color='Attività',
                         color_continuous_scale='Oranges',
                         text='Attività')
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
                "Variazione Frequenza Attività",
                f"{abs(change):.2f} attività/giorno",
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
    """Crea grafici per i dati della mobilità"""
    if "error" in data:
        st.error(f"❌ {data['error']}")
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

            # Mappa emoji per stanze
            emoji_map = {
                'cucina': '🍳',
                'soggiorno': '🛋️',
                'camera_letto': '🛏️',
                'bagno': '🚿',
                'ingresso': '🚪'
            }
            room_df['Label'] = room_df['Stanza'].apply(
                lambda x: f"{emoji_map.get(x, '📍')} {x.replace('_', ' ').title()}"
            )

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
        st.subheader("Attività per Fascia Oraria")
        time_slots = data['time_slot_activity']

        time_df = pd.DataFrame({
            'Fascia': list(time_slots.keys()),
            'Attività': list(time_slots.values())
        })

        # Ordina per fascia oraria logica
        order = ['notte', 'mattina', 'pomeriggio', 'sera']
        time_df['Fascia'] = pd.Categorical(time_df['Fascia'], categories=order, ordered=True)
        time_df = time_df.sort_values('Fascia')

        fig = px.line(time_df, x='Fascia', y='Attività',
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
                "Variazione Frequenza Attività",
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
    "💬 Domanda:",
    placeholder="Es: Come ha dormito e come ha cucinato il soggetto 2 nell'ultima settimana?",
    height=100
)

# Bottone per inviare la query
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    submit_button = st.button("🚀 Invia", use_container_width=True, type="primary")

# Gestione della risposta
if submit_button:
    if not question.strip():
        st.warning("⚠️ Inserisci una domanda prima di inviare!")
    else:
        # Mostra spinner durante il caricamento
        with st.spinner("🔄 Elaborazione in corso..."):
            try:
                # Chiamata al backend
                response = requests.post(
                    f"{BACKEND_URL}/query",
                    json={
                        "question": question,
                        "max_iterations": max_iterations
                    },
                    timeout=120
                )

                if response.status_code == 200:
                    data = response.json()

                    # Tab per organizzare i contenuti
                    tab1, tab2, tab3 = st.tabs(["📊 Risposta e Grafici", "🔍 Dettagli Agenti", "📋 JSON Completo"])

                    with tab1:
                        st.subheader("📝 Domanda")
                        st.info(data["question"])

                        st.subheader("💡 Risposta Finale")
                        st.markdown(data["answer"])

                        # Grafici per ogni agente
                        if data.get("structured_responses"):
                            st.markdown("---")
                            st.header("📊 Analisi Dettagliata")

                            for response in data["structured_responses"]:
                                agent_name = response.get("agent_name", "Unknown")
                                agent_data = response.get("data", {})

                                # Mappa titoli e emoji
                                agent_info = {
                                    "sleep_agent": ("😴 Analisi del Sonno", "#FF6B6B"),
                                    "kitchen_agent": ("🍳 Analisi Attività Cucina", "#FFA500"),
                                    "mobility_agent": ("🚶 Analisi Mobilità", "#4ECDC4")
                                }

                                title, color = agent_info.get(agent_name, ("🤖 Analisi", "#808080"))

                                st.markdown(f"### {title}")

                                # Crea grafici specifici per tipo di agente
                                if agent_name == "sleep_agent":
                                    create_sleep_charts(agent_data)
                                elif agent_name == "kitchen_agent":
                                    create_kitchen_charts(agent_data)
                                elif agent_name == "mobility_agent":
                                    create_mobility_charts(agent_data)

                                st.markdown("---")

                    with tab2:
                        st.subheader("🔍 Risposte Strutturate degli Agenti")

                        if data.get("structured_responses"):
                            for idx, response in enumerate(data["structured_responses"], 1):
                                agent_name = response.get("agent_name", "Unknown")
                                task = response.get("task", "N/A")
                                agent_data = response.get("data", {})

                                emoji_map = {
                                    "sleep_agent": "😴",
                                    "kitchen_agent": "🍳",
                                    "mobility_agent": "🚶"
                                }
                                emoji = emoji_map.get(agent_name, "🤖")

                                with st.expander(f"{emoji} {agent_name.replace('_', ' ').title()} - Analisi {idx}",
                                                 expanded=True):
                                    st.markdown(f"**Task:** {task}")

                                    if "error" in agent_data:
                                        st.error(f"❌ {agent_data['error']}")
                                    else:
                                        st.json(agent_data)

                    with tab3:
                        st.subheader("📋 Risposta JSON Completa")
                        st.json(data)

                else:
                    st.error(f"❌ Errore {response.status_code}: {response.text}")

            except requests.exceptions.Timeout:
                st.error("⏱️ Timeout: Il backend sta impiegando troppo tempo a rispondere.")
            except requests.exceptions.ConnectionError:
                st.error(
                    "🔌 Errore di connessione: Assicurati che il backend sia in esecuzione su http://localhost:8000")
            except Exception as e:
                st.error(f"❌ Errore imprevisto: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "Made with ❤️ by @RiccardoCeccarani"
    "</div>",
    unsafe_allow_html=True
)