from typing import Literal
from langgraph.types import Command
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from backend.models.state import State
# User Question
#     ↓
# [ChatPromptTemplate] → Crea prompt con system instructions + format instructions
#     ↓
# [LLM (Gemini)] → Genera piano in formato JSON
#     ↓
# [PydanticOutputParser] → Valida e converte in ExecutionPlan object
#     ↓
# ExecutionPlan (typed, validated)


class AgentTask(BaseModel):
    """Singolo task per un agente specifico"""
    agent: Literal["sleep_node", "kitchen_node", "mobility_node"] = Field(
        description="Nome dell'agente che deve eseguire il task"
    )
    instruction: str = Field(
        description="Istruzione specifica per l'agente, inclusi subject_id e periodo"
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
    tasks: list[AgentTask] = Field(
        description="Lista ordinata di task da eseguire"
    )

    def get_next_task(self, completed: set[str]) -> AgentTask | None:
        """Restituisce il prossimo task non completato"""
        for task in self.tasks:
            if task.instruction not in completed:
                return task
        return None


def create_planner_node(llm):
    """
    Crea un nodo planner efficiente usando Pydantic per structured output.
    Questo approccio è più veloce e type-safe rispetto al question analyzer precedente.
    """

    # Parser Pydantic per output strutturato
    parser = PydanticOutputParser(pydantic_object=ExecutionPlan)

    # Template del prompt con format instructions
    prompt = ChatPromptTemplate.from_messages([
        ("system", """Sei un esperto nell'analisi di domande sulle attività quotidiane di soggetti monitorati.

Analizza la domanda dell'utente e crea un piano di esecuzione che specifichi:

1. **subject_id**: L'ID numerico del soggetto (1, 2, 3, etc.). Se non specificato, usa null.

2. **period**: Il periodo temporale da analizzare:
   - "last_N_days" per gli ultimi N giorni (es: "last_7_days", "last_30_days")
   - "YYYY-MM-DD,YYYY-MM-DD" per un range specifico
   - Default: "last_30_days" se non specificato

3. **tasks**: Lista di task da eseguire. Per ogni task specifica:
   - **agent**: quale agente deve eseguirlo
     * "sleep_node": per sonno, frequenza cardiaca, respirazione durante il sonno
     * "kitchen_node": per attività in cucina, cottura, pasti
     * "mobility_node": per movimento, stanze visitate, mobilità indoor
   - **instruction**: istruzione chiara in italiano che include subject_id e periodo

ESEMPI:

Domanda: "Come ha dormito il soggetto 2 negli ultimi 7 giorni?"
Piano:
- subject_id: 2
- period: "last_7_days"
- tasks: [
    {{"agent": "sleep_node", "instruction": "Analizza il sonno del soggetto 2 negli ultimi 7 giorni"}}
  ]

Domanda: "Analizza sonno e cucina del soggetto 1 nell'ultimo mese"
Piano:
- subject_id: 1
- period: "last_30_days"
- tasks: [
    {{"agent": "sleep_node", "instruction": "Analizza il sonno del soggetto 1 negli ultimi 30 giorni"}},
    {{"agent": "kitchen_node", "instruction": "Analizza l'attività in cucina del soggetto 1 negli ultimi 30 giorni"}}
  ]

Domanda: "Mobilità, sonno e cucina del soggetto 3 dal 2024-01-01 al 2024-01-31"
Piano:
- subject_id: 3
- period: "2024-01-01,2024-01-31"
- tasks: [
    {{"agent": "sleep_node", "instruction": "Analizza il sonno del soggetto 3 dal 2024-01-01 al 2024-01-31"}},
    {{"agent": "kitchen_node", "instruction": "Analizza l'attività in cucina del soggetto 3 dal 2024-01-01 al 2024-01-31"}},
    {{"agent": "mobility_node", "instruction": "Analizza la mobilità del soggetto 3 dal 2024-01-01 al 2024-01-31"}}
  ]

{format_instructions}"""),
        ("user", "{question}")
    ])

    # Chain: prompt -> LLM -> parser
    planning_chain = prompt | llm | parser

    def planner_node(state: State) -> Command[Literal["supervisor"]]:
        """
        Crea un piano di esecuzione analizzando la domanda dell'utente.
        Usa una chain ottimizzata con Pydantic per output strutturato.
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

        # Log del piano
        print(f"EXECUTION PLAN:")
        print(f"  Subject ID: {plan.subject_id}")
        print(f"  Period: {plan.period}")
        print(f"  Tasks ({len(plan.tasks)}):")
        for i, task in enumerate(plan.tasks, 1):
            print(f"    {i}. [{task.agent}] {task.instruction}")
        print(f"{'=' * 60}\n")

        # Crea messaggio informativo per il supervisor
        plan_summary = (
            f"EXECUTION PLAN:\n"
            f"Subject: {plan.subject_id}, Period: {plan.period}\n\n"
            f"Tasks to execute:\n"
        )
        for i, task in enumerate(plan.tasks, 1):
            plan_summary += f"{i}. [{task.agent}] {task.instruction}\n"

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