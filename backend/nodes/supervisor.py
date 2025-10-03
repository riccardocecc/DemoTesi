from typing import Literal
from langgraph.types import Command
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import END

from backend.models.state import State


def make_supervisor_node(llm, members: list[str]):
    """
    Supervisor deterministico che segue l'execution plan.
    Non usa l'LLM per il routing, solo per la sintesi finale.
    """

    def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:
        print(f"\n{'=' * 60}")
        print("SUPERVISOR - Processing state")
        print(f"{'=' * 60}")

        # Ottieni l'execution plan
        execution_plan = state.get("execution_plan")

        if not execution_plan:
            print("ERROR - No execution plan found!")
            return Command(
                goto=END,
                update={
                    "messages": [AIMessage(content="Errore: nessun piano di esecuzione trovato.", name="supervisor")],
                    "next": "FINISH"
                }
            )

        # Ottieni task completati
        completed_tasks = state.get("completed_tasks", set())
        print(f"Completed tasks: {completed_tasks}")

        # Trova il prossimo task da eseguire
        next_task = execution_plan.get_next_task(completed_tasks)

        if next_task is None:
            # Tutti i task completati → sintetizza risposta finale CON LLM
            print("All tasks completed - Synthesizing final answer")

            original_question = state.get("original_question", "")
            structured_responses = state.get("structured_responses", [])

            # QUI usiamo l'LLM per la sintesi
            synthesis_prompt = (
                f"Domanda originale: {original_question}\n\n"
                f"Dati strutturati ricevuti dagli agenti:\n"
            )

            for resp in structured_responses:
                synthesis_prompt += f"\n{resp['agent_name']}:\n{resp['data']}\n"

            synthesis_prompt += (
                f"\nISTRUZIONI:\n"
                f"1. Interpreta i dati TypedDict ricevuti da ogni agente\n"
                f"2. Fornisci una risposta completa, chiara e leggibile in italiano\n"
                f"3. Evidenzia trend o cambiamenti se presenti\n"
                f"4. Usa un linguaggio naturale e accessibile\n"
                f"5. Rispondi direttamente alla domanda originale\n"
                f"6. Se ci sono metriche numeriche, spiegale in modo comprensibile"
            )

            synthesis_messages = [
                SystemMessage(content=(
                    "Sei un assistente esperto nell'analizzare dati sanitari. "
                    "Ricevi dati strutturati (TypedDict) da agenti specializzati e li trasformi "
                    "in risposte chiare e comprensibili per l'utente finale. "
                    "Usa un tono professionale ma accessibile."
                )),
                HumanMessage(content=synthesis_prompt)
            ]

            final_response = llm.invoke(synthesis_messages)

            print(f"\nFINAL ANSWER:\n{final_response.content}")

            return Command(
                goto=END,
                update={
                    "messages": [AIMessage(content=final_response.content, name="supervisor")],
                    "next": "FINISH"
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