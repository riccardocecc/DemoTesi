from dotenv import load_dotenv
import os
from pathlib import Path
# Carica le variabili dal file .env
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI

# Recupera la chiave dall'ambiente
google_api_key = os.getenv("GOOGLE_API")

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=google_api_key,
    temperature=0,
    max_output_tokens=2000
)

llm_query = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-exp",
    google_api_key=google_api_key,
    temperature=0,
    max_output_tokens=2048,
)



PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Path assoluti ai file
SLEEP_DATA_PATH = DATA_DIR / "sonno_data.csv"
KITCHEN_DATA_PATH = DATA_DIR / "cucina_data.csv"
SENSOR_DATA_PATH = DATA_DIR / "sensor_data.csv"