"""
Nodo per la generazione di grafici cross-domain basato su LLM Intent Detection.
Questo nodo viene chiamato quando execution_plan.cross_domain = True.
"""

from typing import Literal
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pydantic import BaseModel, Field
from langgraph.types import Command
from langchain_core.messages import HumanMessage

from backend.models.state import State, GraphData


class GraphConfig(BaseModel):
    """Configurazione per generare un grafico cross-domain"""

    chart_type: Literal["bar_comparison", "indicator_cards"] = Field(
        description=(
            "Tipo di grafico da generare:\n"
            "- 'bar_comparison': barre affiancate per confrontare due metriche aggregate\n"
            "- 'indicator_cards': dashboard con 2 indicatori numerici affiancati"
        )
    )

    x_domain: Literal["sleep", "kitchen", "mobility"] = Field(
        description="Dominio per la prima metrica (es. 'sleep', 'kitchen', 'mobility')"
    )

    y_domain: Literal["sleep", "kitchen", "mobility"] = Field(
        description="Dominio per la seconda metrica"
    )

    x_metric: str = Field(
        description="Nome esatto della metrica dal primo dominio (es. 'avg_rem_sleep_minutes')"
    )

    y_metric: str = Field(
        description="Nome esatto della metrica dal secondo dominio (es. 'total_cooking_time_hours')"
    )

    x_label: str = Field(
        description="Label descrittivo per la prima metrica in italiano (es. 'Sonno REM (minuti)')"
    )

    y_label: str = Field(
        description="Label descrittivo per la seconda metrica in italiano (es. 'Tempo in Cucina (ore)')"
    )

    title: str = Field(
        description="Titolo del grafico in italiano (es. 'Confronto REM vs Tempo in Cucina')"
    )

    description: str = Field(
        description="Breve spiegazione del grafico e cosa mostra (1-2 frasi)"
    )


# System prompt per l'LLM
SYSTEM_PROMPT = """Sei un esperto nella creazione di visualizzazioni per correlazioni cross-domain tra dati sanitari e comportamentali.

Il tuo compito è analizzare una query dell'utente e i dati disponibili, poi generare una configurazione per un grafico che visualizzi la correlazione richiesta.

⚠️ IMPORTANTE: I dati disponibili sono AGGREGATI (medie, totali), NON dati giornalieri. Quindi puoi creare solo grafici comparativi, non scatter plot con punti multipli.

 DATI DISPONIBILI PER DOMINIO:

**SLEEP DOMAIN** (quando presente):
- avg_rem_sleep_minutes: Media minuti sonno REM
- avg_deep_sleep_minutes: Media minuti sonno profondo  
- avg_light_sleep_minutes: Media minuti sonno leggero
- avg_total_sleep_hours: Media ore sonno totale
- avg_wakeup_count: Media risvegli notturni per notte
- avg_out_of_bed_count: Media uscite dal letto per notte
- sleep_efficiency: Efficienza del sonno in percentuale (0-100)
- avg_hr: Media frequenza cardiaca notturna (bpm)
- avg_rr: Media frequenza respiratoria

**KITCHEN DOMAIN** (quando presente):
- activities_per_day: Numero medio attività giornaliere in cucina
- avg_duration_minutes: Durata media di ogni attività in minuti
- total_cooking_time_hours: Tempo totale passato in cucina in ore
- avg_temperature_max: Temperatura massima media raggiunta

**MOBILITY DOMAIN** (quando presente):
- detections_per_day: Numero medio rilevazioni movimento giornaliere
- avg_duration_minutes: Durata media di ogni movimento in minuti
- total_active_time_hours: Tempo attivo totale in ore
- room_distribution: Dizionario con distribuzione per stanza (usa le chiavi per contare stanze)

 TIPI DI GRAFICO DISPONIBILI:

1. **bar_comparison**: Due barre affiancate per confrontare valori
   - Usa quando: l'utente vuole confrontare/correlare due metriche aggregate
   - Esempio: "Correlazione tra REM e tempo in cucina"
   - Mostra: Due barre side-by-side con i valori

2. **indicator_cards**: Dashboard con 2 grandi numeri affiancati
   - Usa quando: l'utente vuole vedere due metriche insieme in modo chiaro
   - Esempio: "Mostra efficienza sonno e mobilità del soggetto"
   - Mostra: Due indicatori numerici grandi affiancati

 REGOLE FONDAMENTALI:

1. **Scegli chart_type appropriato**:
   - Se query menziona "correlazione", "relazione", "vs", "confronta" → bar_comparison
   - Se query menziona "mostra", "visualizza insieme", "dashboard" → indicator_cards
   - Default: bar_comparison

2. **Usa nomi metriche ESATTI**:
   - Copia esattamente i nomi dalle liste sopra (case-sensitive!)
   - Controlla che la metrica esista nei dati disponibili
   - Se una metrica non c'è, scegli l'alternativa più vicina

3. **Labels descrittivi in italiano**:
   - Traduci i nomi tecnici in linguaggio naturale
   - Includi unità di misura tra parentesi
   - Esempi: "Sonno REM (minuti)", "Attività Cucina (volte/giorno)"

4. **Title chiaro e specifico**:
   - Deve spiegare cosa viene confrontato
   - In italiano, conciso ma descrittivo
   - Esempi: "Confronto REM vs Tempo Cucina", "Efficienza Sonno e Mobilità"

5. **Description utile**:
   - Spiega in 1-2 frasi cosa mostra il grafico
   - Cosa l'utente può capire da questa visualizzazione
   - Mantieni tono professionale ma accessibile

 STRATEGIA DI MATCHING:

Se la query menziona:
- "REM" o "sonno REM" → usa avg_rem_sleep_minutes
- "sonno profondo" → usa avg_deep_sleep_minutes
- "risvegli" o "sveglie" → usa avg_wakeup_count
- "efficienza" → usa sleep_efficiency
- "cuore" o "battito" o "cardiaca" → usa avg_hr
- "cucina" o "cucinare" → usa total_cooking_time_hours o activities_per_day
- "mobilità" o "movimento" → usa detections_per_day o total_active_time_hours
- "stanze" o "ambienti" → usa room_distribution (conta le chiavi)

Restituisci SOLO il JSON con la configurazione GraphConfig.
"""


def extract_metric(data: dict, metric_name: str) -> float:
    """
    Estrae una metrica dai dati strutturati, gestendo diversi formati.

    Args:
        data: Dizionario con i dati del dominio
        metric_name: Nome della metrica da estrarre

    Returns:
        Valore numerico della metrica

    Raises:
        ValueError: Se la metrica non esiste
    """
    try:
        if metric_name in data:
            value = data[metric_name]

            # Se è un dizionario (es. daily_avg_hr), calcola la media
            if isinstance(value, dict):
                numeric_values = [v for v in value.values() if isinstance(v, (int, float))]
                if numeric_values:
                    return sum(numeric_values) / len(numeric_values)
                else:
                    raise ValueError(f"No numeric values in dict for {metric_name}")

            # Se è un numero, restituiscilo
            return float(value)
        else:
            # Prova a cercare in nested structures
            for key, val in data.items():
                if isinstance(val, dict) and metric_name in val:
                    return float(val[metric_name])

            raise ValueError(f"Metric '{metric_name}' not found in data. Available keys: {list(data.keys())}")

    except Exception as e:
        print(f"⚠️  Error extracting metric '{metric_name}': {e}")
        return 0.0


def create_bar_comparison(config: GraphConfig, available_data: dict) -> go.Figure:
    """
    Crea un grafico a barre per confrontare due metriche aggregate da domini diversi.

    Args:
        config: Configurazione del grafico
        available_data: Dizionario con i dati per dominio

    Returns:
        Figura Plotly
    """
    x_value = extract_metric(available_data[config.x_domain], config.x_metric)
    y_value = extract_metric(available_data[config.y_domain], config.y_metric)

    # Crea le barre
    fig = go.Figure(data=[
        go.Bar(
            name=config.x_label,
            x=[config.x_label],
            y=[x_value],
            marker=dict(color='#3498DB'),
            text=[f"{x_value:.2f}"],
            textposition='outside'
        ),
        go.Bar(
            name=config.y_label,
            x=[config.y_label],
            y=[y_value],
            marker=dict(color='#E74C3C'),
            text=[f"{y_value:.2f}"],
            textposition='outside'
        )
    ])

    fig.update_layout(
        title=config.title,
        barmode='group',
        height=400,
        showlegend=False,
        yaxis_title="Valore",
        xaxis=dict(tickangle=0),
        margin=dict(t=80, b=60, l=60, r=60)
    )

    return fig


def create_indicator_cards(config: GraphConfig, available_data: dict) -> go.Figure:
    """
    Crea un dashboard con due indicatori numerici affiancati.

    Args:
        config: Configurazione del grafico
        available_data: Dizionario con i dati per dominio

    Returns:
        Figura Plotly
    """
    x_value = extract_metric(available_data[config.x_domain], config.x_metric)
    y_value = extract_metric(available_data[config.y_domain], config.y_metric)

    # Crea subplots per due indicatori
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "indicator"}, {"type": "indicator"}]],
        subplot_titles=(config.x_label, config.y_label)
    )

    # Primo indicatore
    fig.add_trace(go.Indicator(
        mode="number",
        value=x_value,
        title={"text": config.x_label, "font": {"size": 16}},
        number={'font': {'size': 50}, 'valueformat': '.2f'},
        domain={'x': [0, 0.5], 'y': [0, 1]}
    ), row=1, col=1)

    # Secondo indicatore
    fig.add_trace(go.Indicator(
        mode="number",
        value=y_value,
        title={"text": config.y_label, "font": {"size": 16}},
        number={'font': {'size': 50}, 'valueformat': '.2f'},
        domain={'x': [0.5, 1], 'y': [0, 1]}
    ), row=1, col=2)

    fig.update_layout(
        title=config.title,
        height=300,
        margin=dict(t=80, b=40, l=40, r=40)
    )

    return fig


def detect_graph_intent(llm, question: str, available_data: dict) -> GraphConfig:
    """
    Usa l'LLM per determinare quale grafico generare basandosi sulla query e sui dati disponibili.

    Args:
        llm: Modello LLM configurato
        question: Query originale dell'utente
        available_data: Dizionario con i dati disponibili per dominio

    Returns:
        GraphConfig con la configurazione del grafico

    Raises:
        Exception: Se l'LLM non riesce a generare una configurazione valida
    """
    # Prepara informazioni sui dati disponibili
    domains_str = ", ".join(available_data.keys())

    sleep_metrics = []
    kitchen_metrics = []
    mobility_metrics = []

    if "sleep" in available_data:
        sleep_metrics = [k for k in available_data["sleep"].keys() if
                         k not in ["subject_id", "period", "num_nights", "trends"]]

    if "kitchen" in available_data:
        kitchen_metrics = [k for k in available_data["kitchen"].keys() if
                           k not in ["subject_id", "period", "trends", "time_slot_distribution"]]

    if "mobility" in available_data:
        mobility_metrics = [k for k in available_data["mobility"].keys() if
                            k not in ["subject_id", "period", "trends", "room_distribution", "room_percentages",
                                      "time_slot_activity"]]

    # Costruisci prompt utente
    user_prompt = f"""Query utente: "{question}"

Dati disponibili:
- Domini presenti: {domains_str}
- Metriche sleep disponibili: {sleep_metrics if sleep_metrics else "nessuna"}
- Metriche kitchen disponibili: {kitchen_metrics if kitchen_metrics else "nessuna"}
- Metriche mobility disponibili: {mobility_metrics if mobility_metrics else "nessuna"}

Genera la configurazione per il grafico che meglio risponde alla query dell'utente.
Ricorda: usa SOLO metriche che sono presenti nelle liste sopra!
"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    # Invoca LLM con structured output
    response = llm.with_structured_output(GraphConfig).invoke(messages)

    return response


def create_correlation_graph_node(llm):
    """
    Crea il nodo che genera grafici cross-domain basati su intent detection con LLM.

    Questo nodo:
    1. Verifica se deve essere eseguito (cross_domain = True)
    2. Raccoglie dati disponibili dai team responses
    3. Usa LLM per determinare quale grafico generare
    4. Genera il grafico Plotly
    5. Aggiorna lo state con il grafico generato

    Args:
        llm: Modello LLM da usare per l'intent detection (consigliato: llm_visualization)

    Returns:
        Funzione nodo compatibile con LangGraph
    """

    def correlation_graph_node(state: State) -> Command[Literal["correlation_analyzer"]]:
        """
        Genera grafici di correlazione cross-domain.
        """
        # STEP 1: Verifica se deve eseguire
        execution_plan = state.get("execution_plan")

        if not execution_plan:
            print("⏭️  Skipping correlation graph (no execution plan)")
            return Command(goto="correlation_analyzer")

        if not execution_plan.cross_domain:
            print("⏭️  Skipping correlation graph (cross_domain = False)")
            return Command(goto="correlation_analyzer")

        print(f"\n{'=' * 60}")
        print("CORRELATION GRAPH NODE - Generating cross-domain visualization")
        print(f"{'=' * 60}\n")

        # STEP 2: Raccogli dati disponibili dai team responses
        original_question = state.get("original_question", "")
        team_responses = state.get("structured_responses", [])

        available_data = {}

        for team_resp in team_responses:
            team_name = team_resp.get("team_name", "")

            # Estrai il nome del dominio dal team name (sleep_team → sleep)
            domain = team_name.replace("_team", "")

            # Raccogli dati da tutti gli agenti del team
            for agent_resp in team_resp.get("structured_responses", []):
                data = agent_resp.get("data", {})

                # Ignora errori
                if "error" not in data:
                    # Se il dominio non è ancora presente, inizializzalo
                    if domain not in available_data:
                        available_data[domain] = data
                    else:
                        # Merge dati da agenti diversi dello stesso team
                        available_data[domain].update(data)

        # Verifica che ci siano almeno 2 domini
        if len(available_data) < 2:
            print(f"⚠️  Not enough data for correlation (need at least 2 domains, found {len(available_data)})")
            print(f"   Available domains: {list(available_data.keys())}")
            return Command(goto="correlation_analyzer")

        print(f"✓ Available domains: {list(available_data.keys())}")

        # STEP 3: LLM Intent Detection
        try:
            print(f"🤖 Detecting graph intent with LLM...")
            config = detect_graph_intent(
                llm=llm,
                question=original_question,
                available_data=available_data
            )

            print(f"✓ Graph config generated:")
            print(f"   Type: {config.chart_type}")
            print(f"   X: {config.x_domain}.{config.x_metric} ({config.x_label})")
            print(f"   Y: {config.y_domain}.{config.y_metric} ({config.y_label})")
            print(f"   Title: {config.title}")

        except Exception as e:
            print(f"❌ Intent detection failed: {e}")
            print(f"   Skipping graph generation")
            return Command(goto="correlation_analyzer")

        # STEP 4: Genera grafico Plotly
        try:
            print(f"\n📊 Generating {config.chart_type} chart...")

            if config.chart_type == "bar_comparison":
                fig = create_bar_comparison(config, available_data)
            elif config.chart_type == "indicator_cards":
                fig = create_indicator_cards(config, available_data)
            else:
                print(f"⚠️  Unsupported chart type: {config.chart_type}")
                return Command(goto="correlation_analyzer")

            # Crea GraphData
            graph_data: GraphData = {
                "id": f"correlation_{config.x_domain}_{config.y_domain}",
                "title": config.title,
                "type": config.chart_type,
                "plotly_json": fig.to_dict()
            }

            print(f"✅ Graph generated successfully: {config.title}")
            print(f"   Description: {config.description}")
            print(f"{'=' * 60}\n")

        except Exception as e:
            print(f"❌ Graph generation failed: {e}")
            import traceback
            traceback.print_exc()
            return Command(goto="correlation_analyzer")

        # STEP 5: Update state con il grafico generato
        existing_graphs = state.get("graphs", [])

        return Command(
            goto="correlation_analyzer",
            update={
                "graphs": existing_graphs + [graph_data],
                "messages": [HumanMessage(
                    content=f"Correlation graph generated: {config.title}",
                    name="correlation_graph"
                )]
            }
        )

    return correlation_graph_node