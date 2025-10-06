from dotenv import load_dotenv
import os
from pathlib import Path
# Carica le variabili dal file .env
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI

# Recupera la chiave dall'ambiente
google_api_key = os.getenv("GOOGLE_API")

llm_supervisor  = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=google_api_key,
    temperature=0.3,  # ✅ Leggermente creativo per sintesi naturale
    top_p=0.5,  # ✅ Più varietà lessicale
    top_k=20,  # ✅ Considera più opzioni per linguaggio naturale
    max_output_tokens=4096,  # ✅ Risposta completa e dettagliata
    timeout=60.0,
    max_retries=2
)

llm_agents = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",       # ✅ Miglior balance qualità/velocità
    google_api_key=google_api_key,
    temperature=0,                  # ✅ Precisione nei tool calls
    top_p=0.1,                     # ✅ Molto focale
    top_k=1,                       # ✅ Decisioni deterministiche
    max_output_tokens=2048,        # ✅ Sufficiente per dati strutturati
    timeout=60.0,
    max_retries=2
)

llm_query = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    google_api_key=google_api_key,
    temperature=0,  # ✅ Completamente deterministico
    top_p=0.1,  # ✅ Solo i token più probabili
    top_k=1,  # ✅ Solo il migliore
    max_output_tokens=1024,  # ✅ Piano è breve (JSON piccolo)
    timeout=30.0,
    max_retries=2
)



PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Path assoluti ai file
SLEEP_DATA_PATH = DATA_DIR / "sonno_data.csv"
KITCHEN_DATA_PATH = DATA_DIR / "cucina_data.csv"
SENSOR_DATA_PATH = DATA_DIR / "sensor_data.csv"