import streamlit as st
import requests
import json

# Configurazione della pagina
st.set_page_config(
    page_title="Demo Multi Agent LLM",
    page_icon="",
    layout="centered"
)

# URL del backend
BACKEND_URL = "http://localhost:8000"

# Titolo
st.title("Demo Multi Agent LLM")
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



# Input della domanda
question = st.text_area(
    "Domanda:",
    placeholder="Es: Come ha dormito e come ha cucinato il soggetto 2 nell'ultima settimana?",
    height=100
)

# Bottone per inviare la query
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    submit_button = st.button("invio", use_container_width=True)

# Gestione della risposta
if submit_button:
    if not question.strip():
        st.warning("⚠Inserisci una domanda prima di inviare!")
    else:
        # Mostra spinner durante il caricamento
        with st.spinner("Elaborazione in corso..."):
            try:
                # Chiamata al backend
                response = requests.post(
                    f"{BACKEND_URL}/query",
                    json={
                        "question": question,
                        "max_iterations": max_iterations
                    },
                    timeout=120  # Timeout di 2 minuti
                )

                if response.status_code == 200:
                    data = response.json()


                    st.subheader("Domanda:")
                    st.info(data["question"])

                    st.subheader("Risposta:")
                    st.markdown(data["answer"])

                    # Opzione per copiare la risposta
                    st.markdown("---")
                    with st.expander("📋 Copia risposta JSON"):
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
    "@RiccardoCeccarani"
    "</div>",
    unsafe_allow_html=True
)