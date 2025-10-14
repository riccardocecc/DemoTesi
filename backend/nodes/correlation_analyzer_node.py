from typing import Literal
from langgraph.types import Command
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from backend.models.state import State


def create_correlation_analyzer_node(llm):
    """
    Nodo finale che analizza le correlazioni tra i dati ricevuti
    e sintetizza la risposta finale all'utente.
    """

    def correlation_analyzer_node(state: State) -> Command[Literal["visualization_node"]]:  # ← CAMBIATO DA __end__
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
            f"1. Analizza i dati ricevuti identificando pattern, trend e anomalie\n"
            f"2. Se richiesto, evidenzia correlazioni tra diversi domini\n"
            f"3. Rispondi in italiano con linguaggio chiaro e professionale\n"
            f"4. Usa grassetto per i punti chiave e spiega le metriche in modo comprensibile\n"
            f"5. Fornisci una sintesi concisa ma completa, senza omettere informazioni rilevanti\n"
        )

        messages = [
            SystemMessage(content=(
                "Sei un assistente esperto nell'analisi di dati sanitari e comportamentali. "
                "Il tuo compito è analizzare dati strutturati provenienti da diversi agenti "
                "(sonno, cucina, mobilità) e identificare correlazioni, pattern e insight significativi. "
                "Trasforma questi dati tecnici in risposte chiare ma brevi "
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
            goto="visualization_node",  # ← CAMBIATO DA END
            update={
                "messages": [AIMessage(content=final_response.content, name="correlation_analyzer")],
                "next": "visualization_node"  # ← CAMBIATO DA FINISH
            }
        )

    return correlation_analyzer_node