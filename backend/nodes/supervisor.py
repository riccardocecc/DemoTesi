from typing import Literal
from langgraph.types import Command
from langchain_core.messages import HumanMessage, AIMessage

from backend.models.state import State


def make_supervisor_node(llm, members: list[str]):
    """
    Supervisor deterministico che segue l'execution plan.
    Non usa l'LLM per il routing, solo per assegnare task.
    Quando tutti i task sono completati, invia al correlation_analyzer_node.
    """

    def supervisor_node(state: State) -> Command[Literal[*members, "correlation_analyzer"]]:
        print(f"\n{'=' * 60}")
        print("SUPERVISOR - Processing state")
        print(f"{'=' * 60}")

        # Ottieni l'execution plan
        execution_plan = state.get("execution_plan")

        if not execution_plan:
            print("ERROR - No execution plan found!")
            return Command(
                goto="correlation_analyzer",
                update={
                    "messages": [AIMessage(content="Errore: nessun piano di esecuzione trovato.", name="supervisor")],
                    "next": "correlation_analyzer"
                }
            )

        # Ottieni task completati
        completed_tasks = state.get("completed_tasks", set())
        print(f"Completed tasks: {completed_tasks}")

        # Trova il prossimo task da eseguire
        next_task = execution_plan.get_next_task(completed_tasks)

        if next_task is None:
            # Tutti i task completati → invia al correlation analyzer
            print("All tasks completed - Routing to correlation_analyzer")

            return Command(
                goto="correlation_analyzer",
                update={
                    "next": "correlation_analyzer"
                }
            )

        # Assegna il prossimo task (deterministico, senza LLM)
        print(f"\nAssigning task to {next_task.agent}:")
        print(f"  Task: {next_task.instruction}")

        return Command(
            goto=next_task.agent,
            update={
                "messages": [HumanMessage(content=f"[TASK]: {next_task.instruction}", name="supervisor_instruction")],
                "next": next_task.agent
            }
        )

    return supervisor_node