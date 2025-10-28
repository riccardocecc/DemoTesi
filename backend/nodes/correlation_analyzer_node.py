from typing import Literal

from langgraph.prebuilt import create_react_agent
from langgraph.types import Command
from langgraph.graph import END
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from google.api_core import exceptions

from backend.config.settings import invoke_with_retry
from backend.models.state import State


def create_correlation_analyzer_node(llm):
    """
    Nodo finale che analizza le correlazioni tra i dati ricevuti
    e sintetizza la risposta finale all'utente.

    Nota: I grafici vengono generati INTERNAMENTE dai team (es. sleep_visualization)
    prima di arrivare qui, quindi sono già presenti nello state.
    """
    prompt = (
        "Sei un assistente esperto nell'analisi di dati sanitari. "
        "Rispondi alla domanda dell'utente in modo CONCISO e DIRETTO basandoti SOLO sui dati strutturati forniti.\n\n"

        "REGOLE FONDAMENTALI:\n"
        "1. Rispondi SOLO alla domanda specifica posta dall'utente (original_question)\n"
        "2. Usa MASSIMO 2-3 paragrafi brevi\n"
        "3. Evidenzia solo i dati più rilevanti per rispondere alla domanda\n"
        "4. Usa **grassetto** solo per metriche chiave (es: **439.6 minuti**, **4 risvegli**)\n"
        "5. Evita introduzioni lunghe o conclusioni generiche\n"
        "6. Se ci sono grafici disponibili, menzionali in UNA sola frase alla fine\n\n"

        "STILE DI RISPOSTA:\n"
        "- Professionale ma diretto\n"
        "- Dati prima, interpretazioni dopo\n"
        "- Niente ripetizioni o ridondanze\n"
        "- Numeri concreti invece di descrizioni vaghe\n\n"

        "FORMATO PREFERITO:\n"
        "Paragrafo 1: Risposta diretta alla domanda con i dati principali\n"
        "Paragrafo 2: Eventuali pattern o anomalie rilevanti\n"
        "Paragrafo 3 (opzionale): Breve contestualizzazione se necessaria\n"
        "Menzione grafici (se presenti): Una sola riga finale\n"
    )
    agent = create_react_agent(
        llm,
        tools=[],
        prompt=prompt
    )

    def correlation_analyzer_node(state: State) -> Command[Literal["__end__"]]:
        """
        Riceve tutti i dati strutturati dagli agenti e genera
        una risposta finale completa, analizzando eventuali correlazioni.
        """
        print(f"\n{'=' * 60}")
        print("CORRELATION ANALYZER - Synthesizing final answer")
        print(f"{'=' * 60}\n")

        team_responses = state.get("structured_responses", [])
        graphs = state.get("graphs", [])


        # Estrai tutti gli AgentResponse da tutti i TeamResponse
        all_agent_responses = []
        all_tasks = []

        for team_resp in team_responses:
            if "structured_responses" in team_resp:
                for agent_resp in team_resp["structured_responses"]:
                    all_agent_responses.append(agent_resp)
                    # Raccogli tutte le task
                    if "task" in agent_resp:
                        all_tasks.append(agent_resp["task"])

        # Ricostruisci la domanda originale dalle task
        if all_tasks:
            original_question = " Crea un analisi per eventuali correlazioni tra queste due task: ".join(all_tasks)
        else:
            original_question = state.get("original_question", "Analisi dati")

        print("ORIGINAL QUESTION: " + original_question)

        # Log dei grafici disponibili
        if graphs:
            print(f"Available graphs ({len(graphs)}):")
            for g in graphs:
                print(f"   - {g['id']}: {g['title']}")
        else:
            print("No graphs generated")

        # Costruisci il prompt per l'analisi
        analysis_prompt = (
            f"Domanda originale: {original_question}\n\n"
            f"Dati strutturati ricevuti dagli agenti:\n"
        )

        for resp in all_agent_responses:
            analysis_prompt += f"\n{resp['agent_name']}:\n{resp['data']}\n"

        # Informa l'LLM se ci sono grafici disponibili
        if graphs:
            analysis_prompt += (
                f"\n{'=' * 60}\n"
                f"GRAFICI DISPONIBILI:\n"
                f"Sono stati generati {len(graphs)} grafici che accompagnano questa risposta:\n"
            )
            for g in graphs:
                analysis_prompt += f"- {g['title']} ({g['type']})\n"
            analysis_prompt += (
                f"\nNOTA: Non descrivere i grafici in dettaglio, sono visibili separatamente.\n"
                f"Menziona solo la loro esistenza se rilevante per la risposta.\n"
            )



        try:
            result = invoke_with_retry(agent, HumanMessage(content=analysis_prompt),3)
        except exceptions.ResourceExhausted as e:
             print(f"retry fallita in {e} tentativi")


        final_response = result['messages'][-1]


        print(f"\nFINAL ANSWER:")
        print(f"{'-' * 60}")
        print(final_response)
        print(f"{'-' * 60}\n")

        return Command(
            goto=END,
            update={
                "messages": [AIMessage(content=final_response.content, name="correlation_analyzer")],
                "next": "FINISH"
            }
        )

    return correlation_analyzer_node