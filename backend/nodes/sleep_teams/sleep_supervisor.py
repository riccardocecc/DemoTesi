from typing import Literal, TypedDict
from langchain_core.language_models.chat_models import BaseChatModel

from langgraph.graph import END
from langgraph.types import Command
from langchain_core.messages import HumanMessage, AIMessage

from backend.models.state import State


def make_supervisor_sleep(llm: BaseChatModel, members: list[str]):
    """
    Crea il supervisor per il team Sleep.

    Il supervisor coordina i worker e decide se generare visualizzazioni.
    """

    # Options per il routing: worker + visualization + FINISH
    options = ["FINISH"] + members + ["sleep_visualization"]

    system_prompt = (
        "You are a supervisor coordinating sleep analysis tasks.\n"
        f"Available workers: {members}\n\n"
        "Workers and their capabilities:\n"
        "- analyze_sleep_node: Analyzes sleep quality, duration, phases (REM, deep, light), awakenings\n"
        "- analyze_heart_node: Analyzes heart rate during sleep and its variations\n"
        "- sleep_visualization: Generates Plotly graphs from collected data\n\n"
        "WORKFLOW RULES:\n"
        "1. FIRST PHASE - Data Collection:\n"
        "   - Analyze the user request\n"
        "   - Route to appropriate worker(s) to collect data\n"
        "   - If query mentions BOTH sleep AND heart aspects, call BOTH workers\n"
        "   - Workers will return to you after completing their tasks\n\n"
        "2. SECOND PHASE - Visualization (Optional):\n"
        "   - After ALL data workers have completed\n"
        "   - DECIDE if visualization is needed based on the user query\n"
        "   - Call 'sleep_visualization' if graphs would help\n"
        "   - Visualization will return to you after completion\n\n"
        "3. FINAL PHASE - Completion:\n"
        "   - After visualization (if called) returns\n"
        "   - Route to 'FINISH' to exit the sleep team\n\n"
        "WHEN TO USE VISUALIZATION:\n"
        "✅ Generate graphs if user asks for:\n"
        "   - Visual representation ('mostrami', 'visualizza', 'grafico')\n"
        "   - Analysis that benefits from graphs ('come ha dormito', 'analizza il sonno')\n"
        "   - Trends, patterns, distributions\n"
        "   - Comparisons over time\n"
        "   - Any query where a graph would help understand the data\n\n"
        "❌ Skip visualization if user asks for:\n"
        "   - Simple numeric answers ('quante ore ha dormito')\n"
        "   - Yes/no questions ('ha dormito bene?')\n"
        "   - Specific single values ('qual è l'efficienza del sonno')\n"
        "   - Only textual explanations explicitly requested\n\n"
        "DECISION LOGIC:\n"
        "- If no workers called yet → route to appropriate data worker(s)\n"
        "- If data workers pending → route to pending workers\n"
        "- If ALL data workers completed AND visualization NOT called:\n"
        "  → If visualization would help → route to 'sleep_visualization'\n"
        "  → If only text needed → route to 'FINISH'\n"
        "- If visualization completed → route to 'FINISH'\n\n"
        "DEFAULT: When in doubt, prefer visualization (users usually benefit from graphs).\n\n"
        "Analyze the state and user intent to decide the next step."
    )

    class Router(TypedDict):
        """Worker to route to next."""
        next: Literal[*options]

    def supervisor_node(state: State) -> Command[Literal[*members, "sleep_visualization", "__end__"]]:
        """
        LLM-based router che coordina worker e decide se generare visualizzazioni.
        """

        # Controlla quali task sono stati completati
        completed_tasks = state.get("completed_tasks", set())
        structured_responses = state.get("structured_responses", [])
        original_question = state.get("original_question", "")

        # Trova le risposte del sleep_team
        sleep_team_responses = []
        for team_resp in structured_responses:
            if team_resp["team_name"] == "sleep_team":
                sleep_team_responses = team_resp["structured_responses"]
                break

        # Estrai gli agenti che hanno già risposto
        completed_agents = set()
        for resp in sleep_team_responses:
            completed_agents.add(resp["agent_name"])

        # Controlla se la visualizzazione è già stata chiamata/completata
        visualization_called = False
        visualization_completed = False

        for msg in state["messages"]:
            if hasattr(msg, 'name') and msg.name == "sleep_supervisor":
                if "VISUALIZATION: Generating graphs" in msg.content:
                    visualization_called = True
            if hasattr(msg, 'name') and msg.name == "sleep_visualization":
                visualization_completed = True
                break

        print(f"\n{'=' * 60}")
        print("SLEEP SUPERVISOR STATUS:")
        print(f"Original question: {original_question}")
        print(f"Completed tasks: {completed_tasks}")
        print(f"Completed agents: {completed_agents}")
        print(f"Visualization called: {visualization_called}")
        print(f"Visualization completed: {visualization_completed}")
        print(f"{'=' * 60}\n")

        # Prepara il messaggio per l'LLM con context
        context_message = (
            f"CURRENT STATE:\n"
            f"- Original user question: '{original_question}'\n"
            f"- Completed agents: {list(completed_agents)}\n"
            f"- Available workers: {members}\n"
            f"- Data collected: {len(sleep_team_responses)} agent responses\n"
            f"- Visualization called: {visualization_called}\n"
            f"- Visualization completed: {visualization_completed}\n\n"
            f"TASK: Analyze the current state and decide:\n"
            f"1. Do we need to call more data workers?\n"
            f"2. Should we generate visualizations?\n"
            f"3. Are we ready to FINISH?\n\n"
            f"Remember: Prefer visualization unless the user explicitly wants only text/numbers."
        )

        messages = [
                       {"role": "system", "content": system_prompt},
                       {"role": "user", "content": context_message}
                   ] + state["messages"][-2:]  # Ultimi 5 messaggi per context

        response = llm.with_structured_output(Router).invoke(messages)
        goto = response["next"]

        # Safety checks
        if goto == "sleep_visualization" and (visualization_called or visualization_completed):
            print("⚠️  Visualization already called/completed, routing to FINISH")
            goto = "FINISH"

        if visualization_completed and goto != "FINISH":
            print("⚠️  Visualization completed, forcing FINISH")
            goto = "FINISH"

        if goto == "FINISH":
            goto = END

        print(f"Sleep supervisor decision: {goto}")
        print(f"{'=' * 60}\n")

        # Messaggio di tracking
        if goto == "sleep_visualization":
            tracking_msg = "VISUALIZATION: Generating graphs"
        elif goto == END:
            tracking_msg = "FINISH: Completing sleep team workflow"
        else:
            tracking_msg = f"ROUTING: Calling {goto}"

        update_msg = AIMessage(
            content=tracking_msg,
            name="sleep_supervisor"
        )

        return Command(
            goto=goto,
            update={
                "next": goto,
                "messages": [update_msg]
            }
        )

    return supervisor_node