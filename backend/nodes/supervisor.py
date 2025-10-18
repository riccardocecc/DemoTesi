from typing import Literal, TypedDict
from langgraph.types import Command
from langchain_core.messages import HumanMessage, AIMessage

from backend.models.state import State


def make_supervisor_node(llm, teams: list[str]):
    """
    Supervisor deterministico che segue l'execution plan.
    Non usa l'LLM per il routing, solo per coordinare i teams.

    Quando tutti i task sono completati:
    - Se cross_domain = True → invia a correlation_graph_node
    - Se cross_domain = False → invia a correlation_analyzer
    """

    def supervisor_node(state: State) -> Command[Literal[*teams, "correlation_graph_node", "correlation_analyzer"]]:
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

        # Ottieni il prossimo task da eseguire
        next_task = execution_plan.get_next_task(completed_tasks)

        if next_task is None:
            # Tutti i task completati - decidi dove andare in base a cross_domain
            if execution_plan.cross_domain:
                print("\n✅ All tasks completed - Routing to correlation_graph_node (cross_domain = True)")
                print(f"{'=' * 60}\n")

                return Command(
                    goto="correlation_graph_node",
                    update={
                        "next": "correlation_graph_node"
                    }
                )
            else:
                print("\n✅ All tasks completed - Routing to correlation_analyzer (cross_domain = False)")
                print(f"{'=' * 60}\n")

                return Command(
                    goto="correlation_analyzer",
                    update={
                        "next": "correlation_analyzer"
                    }
                )

        # Assegna il prossimo task al team appropriato
        print(f"\n▶️  Assigning task to {next_task.team}:")
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