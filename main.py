import streamlit as st
import sys
from pathlib import Path
from io import StringIO

from backend.config.settings import llm
from backend.graph.builder import build_graph

# Configurazione pagina
st.set_page_config(
    page_title="SERENADE - Health Monitoring System",
    page_icon="🏥",
    layout="wide"
)


# Inizializzazione del grafo (con caching per evitare di ricostruirlo ad ogni interazione)
@st.cache_resource
def get_serenade_graph():
    """Inizializza e caches il grafo del sistema"""
    return build_graph( llm)


serenade_graph = get_serenade_graph()


def run_demo_streamlit(question: str, max_iterations: int = 10):
    """
    Versione modificata di run_demo per Streamlit.
    Restituisce i risultati invece di stamparli.
    """
    results = {
        "question": question,
        "steps": [],
        "final_answer": None
    }

    step = 1
    for s in serenade_graph.stream(
            {"messages": [("user", question)]},
            {"recursion_limit": max_iterations},
    ):
        step_info = {
            "step_number": step,
            "nodes": []
        }

        for node_name, node_output in s.items():
            if node_output is None:
                step_info["nodes"].append({
                    "name": node_name,
                    "type": "debug",
                    "message": f"Node {node_name} returned None"
                })
                continue

            if node_name == "supervisor":
                next_agent = node_output.get("next", "Unknown")

                node_info = {
                    "name": "supervisor",
                    "type": "supervisor",
                    "next_agent": next_agent
                }

                if next_agent == "FINISH" and "messages" in node_output:
                    for msg in node_output["messages"]:
                        if hasattr(msg, 'name') and msg.name == "supervisor":
                            results["final_answer"] = msg.content
                            node_info["final_answer"] = msg.content

                step_info["nodes"].append(node_info)
            else:
                structured_responses = node_output.get("structured_responses", [])

                node_info = {
                    "name": node_name,
                    "type": "agent",
                    "responses": []
                }

                if not structured_responses:
                    node_info["message"] = "Nessuna risposta strutturata"
                else:
                    for response in structured_responses:
                        if isinstance(response, dict):
                            agent_name = response.get("agent_name", "Unknown")
                            data = response.get("data", {})
                            node_info["responses"].append({
                                "agent_name": agent_name,
                                "data": data
                            })

                step_info["nodes"].append(node_info)

        results["steps"].append(step_info)
        step += 1

    return results


# Titolo principale
st.title("🏥 SERENADE - Sistema di Monitoraggio Salute")
st.markdown("---")

# Sidebar con informazioni
with st.sidebar:
    st.header("ℹ️ Informazioni")
    st.markdown("""
    Questo sistema analizza:
    - 😴 **Sonno**: pattern, qualità, metriche
    - 🍳 **Cucina**: attività, frequenza, durata
    - 🚶 **Mobilità**: movimenti indoor, stanze

    ### Esempi di domande:
    - "Come ha dormito il soggetto 2 nell'ultima settimana?"
    - "Analizza l'attività in cucina del soggetto 1 negli ultimi 30 giorni"
    - "Mostra i pattern di mobilità del soggetto 3 dall'01-01-2024 al 31-01-2024"
    """)

    st.markdown("---")
    max_iterations = st.slider("Max iterazioni", 5, 20, 10)
    show_details = st.checkbox("Mostra dettagli processo", value=True)

# Input principale
st.subheader("🔍 Inserisci la tua domanda")
user_query = st.text_input(
    "Domanda:",
    placeholder="Es: Come ha dormito e cucinato il soggetto 2 nell'ultima settimana?",
    key="user_input"
)

# Bottone per avviare l'analisi
analyze_button = st.button("🚀 Analizza", type="primary", use_container_width=True)

if analyze_button and user_query:
    st.markdown("---")

    # Esegui l'analisi
    with st.spinner("🔄 Elaborazione in corso..."):
        results = run_demo_streamlit(user_query, max_iterations)

    # Mostra la domanda
    st.info(f"**Domanda:** {results['question']}")

    # Mostra i dettagli del processo
    if show_details:
        st.subheader("📊 Processo di analisi")

        with st.expander("🔎 Visualizza dettagli del processo", expanded=True):
            for step_info in results["steps"]:
                st.markdown(f"### Step {step_info['step_number']}")

                for node in step_info["nodes"]:
                    if node["type"] == "supervisor":
                        next_agent = node.get("next_agent", "Unknown")

                        if next_agent == "FINISH":
                            st.success(f"✅ **COORDINATORE**: Analisi completata")
                        else:
                            st.info(f"🎯 **COORDINATORE**: Instradamento verso → `{next_agent}`")

                    elif node["type"] == "agent":
                        # Emoji per tipo di agente
                        emoji_map = {
                            "sleep_node": "😴",
                            "kitchen_node": "🍳",
                            "mobility_node": "🚶"
                        }
                        emoji = emoji_map.get(node["name"], "🤖")

                        st.write(f"{emoji} **AGENTE {node['name'].upper()}**")

                        if "message" in node:
                            st.caption(node["message"])
                        elif node.get("responses"):
                            for resp in node["responses"]:
                                with st.container():
                                    st.caption(f"Agent: {resp['agent_name']}")

                                    # Mostra i dati in modo compatto
                                    data = resp['data']
                                    if 'error' in data:
                                        st.error(f"⚠️ {data['error']}")
                                    else:
                                        # Mostra solo le metriche principali
                                        cols = st.columns(3)

                                        if 'subject_id' in data:
                                            cols[0].metric("Soggetto", data['subject_id'])
                                        if 'period' in data:
                                            cols[1].metric("Periodo", data['period'])

                                        # Mostra metriche specifiche per tipo
                                        if 'num_nights' in data:
                                            cols[2].metric("Notti", data['num_nights'])
                                        elif 'total_activities' in data:
                                            cols[2].metric("Attività", data['total_activities'])
                                        elif 'total_detections' in data:
                                            cols[2].metric("Rilevazioni", data['total_detections'])

                st.markdown("---")

    # Mostra la risposta finale
    if results["final_answer"]:
        st.markdown("---")
        st.subheader("✨ Risposta Finale")
        st.success(results["final_answer"])
    else:
        st.error("⚠️ Nessuna risposta generata. Riprova con una domanda diversa.")

elif analyze_button and not user_query:
    st.warning("⚠️ Per favore, inserisci una domanda prima di analizzare.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray;'>
    💡 Sistema SERENADE - Multi-Agent Health Monitoring
    </div>
    """,
    unsafe_allow_html=True
)