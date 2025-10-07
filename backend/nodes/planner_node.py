from typing import Literal
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from backend.models.state import State


class TeamTask(BaseModel):
    """Singolo task per un team specifico"""
    team: Literal["sleep_team", "kitchen_team", "mobility_team"] = Field(
        description="Nome del team che deve eseguire il task"
    )
    instruction: str = Field(
        description="Istruzione specifica e dettagliata per il team, che include tutti gli aspetti da analizzare nel dominio di competenza"
    )


class ExecutionPlan(BaseModel):
    """Piano di esecuzione completo"""
    subject_id: int | None = Field(
        description="ID del soggetto da analizzare (null se non specificato)"
    )
    period: str = Field(
        description="Periodo da analizzare: 'last_N_days' o 'YYYY-MM-DD,YYYY-MM-DD'",
        default="last_30_days"
    )
    tasks: list[TeamTask] = Field(
        description="Lista ordinata di task da eseguire, uno per ogni team coinvolto"
    )

    def get_next_task(self, completed: set[str]) -> TeamTask | None:
        """Restituisce il prossimo task non completato"""
        for task in self.tasks:
            if task.instruction not in completed:
                return task
        return None


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

3. **tasks**: Lista di task da eseguire. Per ogni task specifica:
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
    {{"team": "sleep_team", "instruction": "Analizza come ha dormito il soggetto 2 negli ultimi 7 giorni: qualità del sonno, durata, eventuali risvegli e pattern generali"}}
  ]

Domanda: "come ha dormito e come si è comportato il cuore durante il sonno del soggetto 2 nelle ultime due settimane e come ha cucinato"
Piano:
- subject_id: 2
- period: "last_14_days"
- tasks: [
    {{"team": "sleep_team", "instruction": "Analizza come ha dormito il soggetto 2 nelle ultime due settimane e come si è comportato il cuore durante il sonno: qualità del sonno, durata, frequenza cardiaca notturna, variazioni e anomalie"}},
    {{"team": "kitchen_team", "instruction": "Analizza come ha cucinato il soggetto 2 nelle ultime due settimane: frequenza delle attività in cucina, preparazione pasti e pattern culinari"}}
  ]

Domanda: "Analizza sonno, frequenza cardiaca notturna e cucina del soggetto 1 nell'ultimo mese"
Piano:
- subject_id: 1
- period: "last_30_days"
- tasks: [
    {{"team": "sleep_team", "instruction": "Analizza il sonno e la frequenza cardiaca notturna del soggetto 1 negli ultimi 30 giorni: qualità del sonno, durata, pattern cardiaci durante il sonno e eventuali anomalie"}},
    {{"team": "kitchen_team", "instruction": "Analizza l'attività in cucina del soggetto 1 negli ultimi 30 giorni: preparazione pasti, utilizzo elettrodomestici e pattern culinari"}}
  ]

Domanda: "Mobilità, tempo in cucina, sonno profondo e respiro notturno del soggetto 3 dal 2024-01-01 al 2024-01-31"
Piano:
- subject_id: 3
- period: "2024-01-01,2024-01-31"
- tasks: [
    {{"team": "sleep_team", "instruction": "Analizza il sonno profondo e il respiro notturno del soggetto 3 dal 2024-01-01 al 2024-01-31: fasi del sonno profondo, durata, qualità respiratoria notturna e pattern"}},
    {{"team": "kitchen_team", "instruction": "Analizza il tempo trascorso in cucina dal soggetto 3 dal 2024-01-01 al 2024-01-31: durata delle sessioni, frequenza e orari delle attività"}},
    {{"team": "mobility_team", "instruction": "Analizza la mobilità del soggetto 3 dal 2024-01-01 al 2024-01-31: stanze visitate, pattern di movimento e livello di attività"}}
  ]

Domanda: "Il soggetto 5 si muove abbastanza? E come cucina?"
Piano:
- subject_id: 5
- period: "last_30_days"
- tasks: [
    {{"team": "mobility_team", "instruction": "Analizza se il soggetto 5 si muove abbastanza negli ultimi 30 giorni: livello di attività fisica, mobilità indoor, tempo trascorso in movimento e confronto con livelli raccomandati"}},
    {{"team": "kitchen_team", "instruction": "Analizza come cucina il soggetto 5 negli ultimi 30 giorni: frequenza delle attività culinarie, preparazione pasti, utilizzo della cucina e pattern"}}
  ]

{format_instructions}"""),
        ("user", "{question}")
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
        original_question = state["messages"][0].content if state["messages"] else ""

        print(f"\n{'=' * 60}")
        print(f"PLANNER - Creating execution plan for:")
        print(f"{original_question}")
        print(f"{'=' * 60}\n")

        # Esegui la planning chain
        plan: ExecutionPlan = planning_chain.invoke({
            "question": original_question,
            "format_instructions": parser.get_format_instructions()
        })


        print(f"EXECUTION PLAN:")
        print(f"  Subject ID: {plan.subject_id}")
        print(f"  Period: {plan.period}")
        print(f"  Tasks ({len(plan.tasks)}):")
        for i, task in enumerate(plan.tasks, 1):
            print(f"    {i}. [{task.team}]")
            print(f"       {task.instruction}")
        print(f"{'=' * 60}\n")


        plan_summary = (
            f"EXECUTION PLAN:\n"
            f"Subject: {plan.subject_id}, Period: {plan.period}\n\n"
            f"Tasks to execute:\n"
        )
        for i, task in enumerate(plan.tasks, 1):
            plan_summary += f"{i}. [{task.team}]\n   {task.instruction}\n\n"

        return Command(
            goto="supervisor",
            update={
                "messages": [HumanMessage(content=plan_summary)],
                "original_question": original_question,
                "execution_plan": plan,
                "completed_tasks": set()
            }
        )

    return planner_node