import time
from time import sleep
from typing import Literal
from langgraph.types import Command
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from backend.models.state import State, ExecutionPlan


def create_planner_node(llm):
    """
    Crea un nodo planner che assegna i task ai team appropriati.
    Il planner estrae il dominio della query e crea istruzioni dettagliate per ogni team.
    """
    # Parser Pydantic per output strutturato
    parser = PydanticOutputParser(pydantic_object=ExecutionPlan)

    # Template del prompt con format instructions
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Sei un esperto nell'analisi di domande sulle attività quotidiane di soggetti monitorati.

Analizza la domanda dell'utente e crea un piano di esecuzione che specifichi:

1. **subject_id**: L'ID numerico del soggetto (1, 2, 3, etc.). Se non specificato, usa null.

2. **period**: Il periodo temporale da analizzare:
   - "last_N_days" per gli ultimi N giorni (es: "last_7_days", "last_14_days", "last_30_days")
   - "YYYY-MM-DD,YYYY-MM-DD" per un range specifico
   - Default: "last_30_days" se non specificato

3. **cross_domain**: Booleano che indica se la query richiede correlazioni tra domini
   - Imposta a **True**: Query richiede correlazioni/relazioni tra domini
     → I team di dominio (sleep/kitchen/mobility) raccolgono SOLO dati (NO grafici)
     → Il correlation_graph_node genera grafici di correlazione
   - Imposta    **False**: Query richiede analisi standard
     → I team di dominio generano i loro grafici normalmente
     → NON creare task per correlation_graph_node
     
     **IDENTIFICAZIONE KEYWORD PER CORRELAZIONI:**
        Questi termini indicano richieste di correlazione:
        - "correlazione", "correlato", "correlati"
        - "relazione", "relazionato", "collegato"
        - "confronta", "paragona", "vs", "rispetto a"
        - "influenza", "influenzato", "dipende"
        - "insieme", "in relazione a"
        - "impatto di X su Y", "effetto di X su Y"
        -"come ha dormito e come ha cucinato


4. **tasks**: Lista di task da eseguire. Per ogni task specifica:
   - **team**: quale team deve eseguirlo
     * "sleep_team": per tutto ciò che riguarda il sonno (qualità, durata, risvegli, frequenza cardiaca durante il sonno, respirazione notturna, fasi del sonno, etc.)
     * "kitchen_team": per tutto ciò che riguarda la cucina e i pasti (attività in cucina, cottura, preparazione pasti, utilizzo elettrodomestici, orari dei pasti, etc.)
     * "mobility_team": per tutto ciò che riguarda il movimento (stanze visitate, mobilità indoor, attività fisica, tempo trascorso in diverse aree, pattern di movimento, etc.)

   - **instruction**: istruzione completa e dettagliata in italiano che:
     * Include TUTTI gli aspetti da analizzare menzionati nella domanda originale per quel dominio
     * Specifica sempre subject_id e periodo
     * È autonoma e comprensibile senza contesto aggiuntivo
     * Contiene tutti i dettagli necessari per l'analisi

**REGOLE IMPORTANTI:**
- Estrai e separa gli aspetti della domanda per dominio di competenza
- Ogni team riceve UN'UNICA istruzione che include TUTTI gli aspetti del suo dominio
- Non duplicare informazioni tra team
- Se la domanda menziona più aspetti dello stesso dominio, includili tutti nella stessa istruzione
- Le istruzioni devono essere specifiche e dettagliate, non generiche

**ESEMPI:**

Domanda: "Come ha dormito il soggetto 2 negli ultimi 7 giorni?"
Piano:
- subject_id: 2
- period: "last_7_days"
- tasks: [
    {{"team": "sleep_team", "instruction": "Analizza come ha dormito il soggetto 2 negli ultimi 7 giorni"}}
  ]

Domanda: "come ha dormito e come si è comportato il cuore durante il sonno del soggetto 2 nelle ultime due settimane e come ha cucinato"
Piano:
- subject_id: 2
- period: "last_14_days"
- tasks: [
    {{"team": "sleep_team", "instruction": "Analizza come ha dormito il soggetto 2 nelle ultime due settimane e come si è comportato il cuore durante il sonno"}},
    {{"team": "kitchen_team", "instruction": "Analizza come ha cucinato il soggetto 2 nelle ultime due settimane"}}
  ]

Domanda: "Analizza sonno, frequenza cardiaca notturna e cucina del soggetto 1 nell'ultimo mese"
Piano:
- subject_id: 1
- period: "last_30_days"
- tasks: [
    {{"team": "sleep_team", "instruction": "Analizza il sonno e la frequenza cardiaca notturna del soggetto 1 negli ultimi 30 giorni"}},
    {{"team": "kitchen_team", "instruction": "Analizza l'attività in cucina del soggetto 1 negli ultimi 30 giorni"}}
  ]

Domanda: "Mobilità, tempo in cucina, sonno profondo e respiro notturno del soggetto 3 dal 2024-01-01 al 2024-01-31"
Piano:
- subject_id: 3
- period: "2024-01-01,2024-01-31"
- tasks: [
    {{"team": "sleep_team", "instruction": "Analizza il sonno profondo e il respiro notturno del soggetto 3 dal 2024-01-01 al 2024-01-31"}},
    {{"team": "kitchen_team", "instruction": "Analizza il tempo trascorso in cucina dal soggetto 3 dal 2024-01-01 al 2024-01-31"}},
    {{"team": "mobility_team", "instruction": "Analizza la mobilità del soggetto 3 dal 2024-01-01 al 2024-01-31"}}
  ]

Domanda: "Il soggetto 5 si muove abbastanza? E come cucina?"
Piano:
- subject_id: 5
- period: "last_30_days"
- tasks: [
    {{"team": "mobility_team", "instruction": "Analizza se il soggetto 5 si muove abbastanza negli ultimi 30 giorni"}},
    {{"team": "kitchen_team", "instruction": "Analizza come cucina il soggetto 5 negli ultimi 30 giorni"}}
  ]

{format_instructions}"""),
        MessagesPlaceholder(variable_name="messages"),
    ])

    # Chain: prompt -> LLM -> parser
    # 1. prompt: formatta la domanda con istruzioni per creare il piano
    # 2. llm: genera il piano in formato strutturato JSON
    # 3. parser: converte l'output JSON in oggetto ExecutionPlan validato
    planning_chain = prompt | llm | parser

    def planner_node(state: State) -> Command[Literal["supervisor"]]:
        """
        Crea un piano di esecuzione analizzando la domanda dell'utente.
        Assegna i task ai team appropriati in base al dominio della query.
        """
        # Prendi la domanda originale
        print(f"{'=' * 60}\n")

        # Esegui la planning chain
        plan: ExecutionPlan = planning_chain.invoke({
            "messages":state["messages"],
            "format_instructions": parser.get_format_instructions(),
        })
        print("CHIAMATA LLM")

        unique_teams = set(task.team for task in plan.tasks)
        if len(unique_teams) > 1:
            plan.cross_domain=True

        print(f"EXECUTION PLAN:")
        print(f"  Subject ID: {plan.subject_id}")
        print(f"  Period: {plan.period}")
        print(f"  Cross-Domain: {'YES' if plan.cross_domain else 'NO'}")
        print(f"  Tasks ({len(plan.tasks)}):")
        for i, task in enumerate(plan.tasks, 1):
            print(f"    {i}. [{task.team}]")
            print(f"       {task.instruction}")
        print(f"{'=' * 60}\n")

        plan_summary = (
            f"EXECUTION PLAN:\n"
            f"Subject: {plan.subject_id}, Period: {plan.period}\n"
            f"Cross-Domain: {plan.cross_domain}\n\n"
            f"Tasks to execute:\n"
        )
        for i, task in enumerate(plan.tasks, 1):
            plan_summary += f"{i}. [{task.team}]\n   {task.instruction}\n\n"

        return Command(
            goto="supervisor",
            update={
                "messages": [AIMessage(content=plan_summary)],
                "execution_plan": plan,
                "completed_tasks": set(),
                "structured_responses": [],
                "graphs": None,
                "next":None
            }
        )

    return planner_node