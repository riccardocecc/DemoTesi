import streamlit as st
import requests
import plotly.graph_objects as go
from uuid import uuid4
from streamlit_chat import message
import time

# Configurazione della pagina
st.set_page_config(
    page_title="Demo multi agent",
    page_icon="🤖",
    layout="wide"
)

# URL del backend
BACKEND_URL = "http://localhost:8000"

# Inizializza session state
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid4())
if "past" not in st.session_state:
    st.session_state.past = []  # User messages
if "generated" not in st.session_state:
    st.session_state.generated = []  # Assistant messages
if "graphs" not in st.session_state:
    st.session_state.graphs = {}  # Dict: message_index -> list[graphs]
if "is_loading" not in st.session_state:
    st.session_state.is_loading = False

# Custom CSS
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .stTextInput > div > div > input {
        border-radius: 20px;
    }

    .stButton > button {
        border-radius: 20px;
        background-color: #2c3e50;
        color: white;
        border: none;
        padding: 8px 16px;
    }

    .stButton > button:hover {
        background-color: #34495e;
    }

    .stForm {
        border: none;
        padding: 0;
    }

    /* Loading dots animation */
    .loading-dots {
        display: inline-flex;
        align-items: center;
        gap: 4px;
    }

    .loading-dots span {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #666;
        animation: bounce 1.4s infinite ease-in-out both;
    }

    .loading-dots span:nth-child(1) {
        animation-delay: -0.32s;
    }

    .loading-dots span:nth-child(2) {
        animation-delay: -0.16s;
    }

    @keyframes bounce {
        0%, 80%, 100% {
            transform: scale(0);
            opacity: 0.5;
        }
        40% {
            transform: scale(1);
            opacity: 1;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# Header
st.title("Demo multi agent")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("Settings")

    # Health check
    if st.button("Check Connection"):
        try:
            response = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if response.status_code == 200:
                st.success("Connected")
            else:
                st.error("Backend unavailable")
        except Exception as e:
            st.error(f"Connection error: {str(e)}")

    st.markdown("---")

    # New conversation
    if st.button("New Conversation"):
        st.session_state.thread_id = str(uuid4())
        st.session_state.past = []
        st.session_state.generated = []
        st.session_state.graphs = {}
        st.session_state.is_loading = False
        st.rerun()

    st.markdown("---")

    # Info
    st.subheader("Info")
    st.caption(f"Thread ID: {st.session_state.thread_id[:12]}...")
    st.caption(f"Messages: {len(st.session_state.past) + len(st.session_state.generated)}")
    st.caption(f"Graphs: {sum(len(g) for g in st.session_state.graphs.values())}")

# Chat container
chat_placeholder = st.container()

with chat_placeholder:
    # Display conversation
    for i in range(len(st.session_state.generated)):
        # User message
        if i < len(st.session_state.past):
            message(st.session_state.past[i], is_user=True, key=f"{i}_user", avatar_style="no-avatar")

        # Assistant message
        message(st.session_state.generated[i], key=f"{i}", avatar_style="thumbs")

        # Display graphs if any
        if i in st.session_state.graphs:
            graphs = st.session_state.graphs[i]

            if len(graphs) == 1:
                # Single graph full width
                graph = graphs[0]
                st.markdown(f"**{graph['title']}**")
                fig = go.Figure(graph['plotly_json'])
                fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
                st.plotly_chart(fig, use_container_width=True, key=f"graph_{i}_{graph['id']}")

            elif len(graphs) == 2:
                # Two graphs side by side
                col1, col2 = st.columns(2)
                with col1:
                    graph = graphs[0]
                    st.markdown(f"**{graph['title']}**")
                    fig = go.Figure(graph['plotly_json'])
                    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig, use_container_width=True, key=f"graph_{i}_{graph['id']}_0")
                with col2:
                    graph = graphs[1]
                    st.markdown(f"**{graph['title']}**")
                    fig = go.Figure(graph['plotly_json'])
                    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
                    st.plotly_chart(fig, use_container_width=True, key=f"graph_{i}_{graph['id']}_1")

            else:
                # Multiple graphs in grid
                for j in range(0, len(graphs), 2):
                    col1, col2 = st.columns(2)
                    with col1:
                        graph = graphs[j]
                        st.markdown(f"**{graph['title']}**")
                        fig = go.Figure(graph['plotly_json'])
                        fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
                        st.plotly_chart(fig, use_container_width=True, key=f"graph_{i}_{j}_{graph['id']}")

                    if j + 1 < len(graphs):
                        with col2:
                            graph = graphs[j + 1]
                            st.markdown(f"**{graph['title']}**")
                            fig = go.Figure(graph['plotly_json'])
                            fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
                            st.plotly_chart(fig, use_container_width=True, key=f"graph_{i}_{j + 1}_{graph['id']}")

    # Show loading state if currently processing
    if st.session_state.is_loading:
        # Show last user message
        if len(st.session_state.past) > len(st.session_state.generated):
            last_user_msg = st.session_state.past[-1]
            message(last_user_msg, is_user=True, key="loading_user", avatar_style="no-avatar")

        # Show loading indicator for bot
        message("...", key="loading_bot", avatar_style="thumbs")

# Input area
st.markdown("---")

# Input box - usando form per gestire meglio il submit
with st.form(key="chat_form", clear_on_submit=True):
    col1, col2 = st.columns([6, 1])

    with col1:
        user_input = st.text_input(
            "Message:",
            key="user_input_field",
            placeholder="Ask about sleep, kitchen, or mobility data...",
            label_visibility="collapsed"
        )

    with col2:
        submit_button = st.form_submit_button("Send", use_container_width=True)

# Handle form submission
if submit_button and user_input.strip():
    # Add user message immediately
    st.session_state.past.append(user_input)
    st.session_state.is_loading = True

    # Rerun to show the user message and loading indicator
    st.rerun()

# Process backend request if loading
if st.session_state.is_loading:
    # Get the last user message
    user_message = st.session_state.past[-1]

    try:
        response = requests.post(
            f"{BACKEND_URL}/chat",
            json={
                "message": user_message,
                "thread_id": st.session_state.thread_id,
                "max_iterations": 15
            },
            timeout=120
        )

        if response.status_code == 200:
            data = response.json()

            # Add assistant message
            st.session_state.generated.append(data["message"])

            # Store graphs for this message
            if data.get("graphs") and len(data["graphs"]) > 0:
                message_idx = len(st.session_state.generated) - 1
                st.session_state.graphs[message_idx] = data["graphs"]

            # Update thread_id
            st.session_state.thread_id = data["thread_id"]
        else:
            st.session_state.generated.append(f"Error: {response.status_code}")

    except requests.exceptions.Timeout:
        st.session_state.generated.append("Request timeout. Backend is taking too long.")
    except requests.exceptions.ConnectionError:
        st.session_state.generated.append("Connection error. Make sure backend is running.")
    except Exception as e:
        st.session_state.generated.append(f"Error: {str(e)}")

    finally:
        # Reset loading state
        st.session_state.is_loading = False
        st.rerun()