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
    temperature=0.3,  # creativo
    top_p=0.5,  # varietà lessicale
    top_k=20,  # maggiori opzioni (da vedere meglio)
    max_output_tokens=2096,  #lunghezza risposta (forse anche meno)
    timeout=60.0,
    max_retries=2
)

llm_agents = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=google_api_key,
    temperature=0,
    top_p=0.1,
    top_k=1,
    max_output_tokens=2048,
    timeout=60.0,
    max_retries=2
)

llm_query = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    google_api_key=google_api_key,
    temperature=0,  #deterministico
    top_p=0.1,  #token più probabili
    top_k=1,  #solo il migliore
    max_output_tokens=1024,  #per json dovrebbe bastare
    timeout=30.0,
    max_retries=2
)

llm_visualization = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=google_api_key,
    temperature=0,  # Leggermente creativo per intent detection
    top_p=0,
    top_k=10,
    max_output_tokens=1024,
    timeout=30.0,
    max_retries=2
)




PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"


SLEEP_DATA_PATH = DATA_DIR / "sonno_data.csv"
KITCHEN_DATA_PATH = DATA_DIR / "cucina_data.csv"
SENSOR_DATA_PATH = DATA_DIR / "sensor_data.csv"