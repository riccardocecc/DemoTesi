from typing import Literal
from langgraph.types import Command
from langgraph.graph import END
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backend.models.state import State


def create_correlation_analyzer_node(llm):
    """
    Nodo finale che analizza le correlazioni tra i dati ricevuti
    e sintetizza la risposta finale all'utente.
    """

    def correlation_analyzer_node(state: State) -> Command[Literal["__end__"]]:
        """
        Riceve tutti i dati strutturati dagli agenti e genera
        una risposta finale completa, analizzando eventuali correlazioni.
        """
        print(f"\n{'=' * 60}")
        print("CORRELATION ANALYZER - Synthesizing final answer")
        print(f"{'=' * 60}\n")

        original_question = state.get("original_question", "")
        team_responses = state.get("structured_responses", [])

        # Estrai tutti gli AgentResponse da tutti i TeamResponse
        all_agent_responses = []
        for team_resp in team_responses:
            all_agent_responses.extend(team_resp["structured_responses"])

        analysis_prompt = (
            f"Domanda originale: {original_question}\n\n"
            f"Dati strutturati ricevuti dagli agenti:\n"
        )

        for resp in all_agent_responses:
            analysis_prompt += f"\n{resp['agent_name']}:\n{resp['data']}\n"

        analysis_prompt += (
            f"\n{'=' * 60}\n"
            f"ISTRUZIONI PER LA RISPOSTA:\n"
            f"{'=' * 60}\n\n"
            f"1. ANALISI DEI DATI:\n"
            f"   - Interpreta tutti i dati TypedDict ricevuti da ciascun agente\n"
            f"   - Identifica pattern, trend e anomalie\n\n"
            f"2. CORRELAZIONI:\n"
            f"   - Se la domanda richiede correlazioni tra diversi domini (es. sonno e mobilità),\n"
            f"     analizza le relazioni tra i dati\n"
            f"   - Cerca pattern temporali comuni o divergenti\n"
            f"   - Evidenzia cause-effetto potenziali\n\n"
            f"3. FORMATO DELLA RISPOSTA:\n"
            f"   - Usa un linguaggio naturale, chiaro e professionale in italiano\n"
            f"   - Struttura la risposta in modo logico e leggibile\n"
            f"   - Evidenzia i punti chiave usando grassetto o elenchi quando appropriato\n"
            f"   - Se ci sono metriche numeriche, spiegale in modo comprensibile\n\n"
            f"4. COMPLETEZZA:\n"
            f"   - Rispondi direttamente e completamente alla domanda originale\n"
            f"   - Non omettere informazioni rilevanti dai dati ricevuti\n"
            f"   - Se i dati mostrano trend, descrivili chiaramente\n\n"
            f"5. INSIGHTS:\n"
            f"   - Fornisci interpretazioni significative dei dati\n"
        )

        messages = [
            SystemMessage(content=(
                "Sei un assistente esperto nell'analisi di dati sanitari e comportamentali. "
                "Il tuo compito è analizzare dati strutturati provenienti da diversi agenti "
                "(sonno, cucina, mobilità) e identificare correlazioni, pattern e insight significativi. "
                "Trasforma questi dati tecnici in risposte chiare, accessibili e ricche di significato "
                "per l'utente finale. Usa un tono professionale ma empatico."
            )),
            HumanMessage(content=analysis_prompt)
        ]

        # Invoca l'LLM per la sintesi
        final_response = llm.invoke(messages)

        print(f"\nFINAL ANSWER:")
        print(f"{'-' * 60}")
        print(final_response.content)
        print(f"{'-' * 60}\n")

        return Command(
            goto=END,
            update={
                "messages": [AIMessage(content=final_response.content, name="correlation_analyzer")],
                "next": "FINISH"
            }
        )

    return correlation_analyzer_node