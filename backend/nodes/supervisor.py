from typing import Literal, TypedDict
from langgraph.types import Command
from langchain_core.messages import HumanMessage, AIMessage

from backend.models.state import State


def make_supervisor_node(llm, teams: list[str]):
    """
    Supervisor deterministico che segue l'execution plan.
    Non usa l'LLM per il routing, solo per coordinare i teams.
    Quando tutti i task sono completati, invia al correlation_analyzer_node.
    """

    def supervisor_node(state: State) -> Command[Literal[*teams, "correlation_analyzer"]]:
        print(f"\n{'=' * 60}")
        print("TOP SUPERVISOR - Processing state")
        print(f"{'=' * 60}")


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


        completed_tasks = state.get("completed_tasks", set())
        print(f"Completed tasks ({len(completed_tasks)}):")
        for task in completed_tasks:
            print(f"  ✓ {task[:80]}...")


        next_task = execution_plan.get_next_task(completed_tasks)

        if next_task is None:
            # Tutti i task completati invia al correlation analyzer
            print("\nAll tasks completed - Routing to correlation_analyzer")
            print(f"{'=' * 60}\n")

            return Command(
                goto="correlation_analyzer",
                update={
                    "next": "correlation_analyzer"
                }
            )

        # Assegna il prossimo task al team appropriato (senza LLM fa da router)
        print(f"\n"
              f"Assigning task to {next_task.team}:")
        print(f"   Task: {next_task.instruction}")
        print(f"{'=' * 60}\n")

        return Command(
            goto=next_task.team,
            update={
                "messages": [AIMessage(
                    content=f"[TASK]: {next_task.instruction}",
                    name="supervisor_instruction"
                )],
                "next": next_task.team
            }
        )

    return supervisor_node