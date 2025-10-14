import streamlit as st
import requests
import plotly.graph_objects as go

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


# Input della domanda
st.markdown("### Fai una domanda")
question = st.text_area(
    "Domanda:",
    placeholder="Es: Come ha dormito e come ha cucinato il soggetto 2 nell'ultima settimana?",
    height=100,
    label_visibility="collapsed"
)

# Bottone per inviare la query
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown("""
        <style>
        div.stButton > button:first-child {
            background-color: #374957;
            color: white;
            font-weight: bold;
            border-radius: 8px;
            height: 3em;
        }
        div.stButton > button:first-child:hover {
            background-color: #2c3a47;
            border-color: #2c3a47;
        }
        </style>
        """, unsafe_allow_html=True)
    submit_button = st.button("Invia Query", use_container_width=True)

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
                        "max_iterations": 15
                    },
                    timeout=120
                )

                if response.status_code == 200:
                    data = response.json()

                    # --- RISPOSTA TESTUALE ---
                    st.markdown("---")
                    st.markdown("## Risposta")

                    with st.container():
                        st.markdown(
                            f"""<div style='background-color: #f0f2f6; padding: 20px; 
                            border-radius: 10px; border-left: 5px solid #374957;'>
                            {data["answer"]}
                            </div>""",
                            unsafe_allow_html=True
                        )

                    # --- GRAFICI GENERATI ---
                    if data.get("graphs") and len(data["graphs"]) > 0:
                        st.markdown("---")
                        st.markdown("## Visualizzazioni")

                        graphs = data["graphs"]
                        st.info(f"Generati {len(graphs)} grafici per la tua domanda")

                        num_graphs = len(graphs)

                        if num_graphs == 1:
                            # Un solo grafico a tutta larghezza
                            graph = graphs[0]
                            st.markdown(f"### {graph['title']}")
                            fig = go.Figure(graph['plotly_json'])
                            st.plotly_chart(fig, use_container_width=True, key=f"graph_{graph['id']}")

                        elif num_graphs == 2:
                            # Due grafici affiancati
                            col1, col2 = st.columns(2)

                            with col1:
                                graph = graphs[0]
                                st.markdown(f"### {graph['title']}")
                                fig = go.Figure(graph['plotly_json'])
                                st.plotly_chart(fig, use_container_width=True, key=f"graph_{graph['id']}")

                            with col2:
                                graph = graphs[1]
                                st.markdown(f"### {graph['title']}")
                                fig = go.Figure(graph['plotly_json'])
                                st.plotly_chart(fig, use_container_width=True, key=f"graph_{graph['id']}")

                        else:
                            # 3 o più grafici: griglia 2 colonne
                            for i in range(0, num_graphs, 2):
                                col1, col2 = st.columns(2)

                                with col1:
                                    graph = graphs[i]
                                    st.markdown(f"### {graph['title']}")
                                    fig = go.Figure(graph['plotly_json'])
                                    st.plotly_chart(fig, use_container_width=True, key=f"graph_{graph['id']}_{i}")

                                # Secondo grafico della riga (se esiste)
                                if i + 1 < num_graphs:
                                    with col2:
                                        graph = graphs[i + 1]
                                        st.markdown(f"### {graph['title']}")
                                        fig = go.Figure(graph['plotly_json'])
                                        st.plotly_chart(fig, use_container_width=True,
                                                        key=f"graph_{graph['id']}_{i + 1}")

                    else:
                        st.info("Nessun grafico generato per questa query")

                else:
                    st.error(f"Errore {response.status_code}: {response.text}")

            except requests.exceptions.Timeout:
                st.error("Timeout: Il backend sta impiegando troppo tempo a rispondere.")
            except requests.exceptions.ConnectionError:
                st.error(
                    "Errore di connessione: Assicurati che il backend sia in esecuzione su http://localhost:8000"
                )
            except Exception as e:
                st.error(f"Errore imprevisto: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray; padding: 20px;'>"
    "Powered by LangGraph + Plotly | @RiccardoCeccarani"
    "</div>",
    unsafe_allow_html=True
)