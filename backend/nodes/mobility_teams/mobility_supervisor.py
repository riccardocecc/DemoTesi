from typing import Literal, TypedDict
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.types import Command
from langgraph.graph import END
from langchain_core.messages import AIMessage

from backend.models.state import State


def make_supervisor_mobility(llm: BaseChatModel, members: list[str]):
    """
    Crea il supervisor per il team Mobility.

    Il supervisor coordina i worker e decide se generare visualizzazioni.
    """

    # Options per il routing: worker + visualization + FINISH
    options = ["FINISH"] + members + ["mobility_visualization_node"]

    system_prompt = (
        "You are a supervisor coordinating mobility analysis tasks.\n"
        f"Available workers: {members}\n\n"
        "Workers and their capabilities:\n"
        "- analyze_mobility_node: Analyzes movement patterns within the home using environmental sensors\n"
        "- mobility_visualization_node: Generates Plotly graphs from collected data\n\n"
        "WORKFLOW RULES:\n"
        "1. FIRST PHASE - Data Collection:\n"
        "   - Analyze the user request\n"
        "   - Route to analyze_mobility_node to collect data\n"
        "   - Worker will return to you after completing the task\n\n"
        "2. SECOND PHASE - Visualization (Optional):\n"
        "   - After data worker has completed\n"
        "   - DECIDE if visualization is needed based on the user query\n"
        "   - Call 'mobility_visualization_node' if graphs would help\n"
        "   - Visualization will return to you after completion\n\n"
        "3. FINAL PHASE - Completion:\n"
        "   - After visualization (if called) returns\n"
        "   - Route to 'FINISH' to exit the mobility team\n\n"
        "WHEN TO USE VISUALIZATION:\n"
        "✅ Generate graphs if user asks for:\n"
        "   - Visual representation ('mostrami', 'visualizza', 'grafico')\n"
        "   - Analysis that benefits from graphs ('pattern di movimento', 'analizza mobilità')\n"
        "   - Room distribution or presence patterns\n"
        "   - Time-based analysis (activity by time slot)\n"
        "   - Spatial movement patterns\n"
        "   - Any query where a graph would help understand the data\n\n"
        "❌ Skip visualization if user asks for:\n"
        "   - Simple numeric answers ('quante volte si è mosso')\n"
        "   - Yes/no questions ('si muove molto?')\n"
        "   - Specific single values ('stanza più frequentata')\n"
        "   - Only textual explanations explicitly requested\n\n"
        "DECISION LOGIC:\n"
        "- If analyze_mobility_node not called yet → route to analyze_mobility_node\n"
        "- If analyze_mobility_node completed AND visualization NOT called:\n"
        "  → If visualization would help → route to 'mobility_visualization_node'\n"
        "  → If only text needed → route to 'FINISH'\n"
        "- If visualization completed → route to 'FINISH'\n\n"
        "DEFAULT: When in doubt, prefer visualization (users usually benefit from graphs).\n\n"
        "Analyze the state and user intent to decide the next step."
    )

    class Router(TypedDict):
        """Worker to route to next."""
        next: Literal[*options]

    def supervisor_node(state: State) -> Command[Literal[*members, "mobility_visualization_node", "__end__"]]:
        """
        LLM-based router che coordina worker e decide se generare visualizzazioni.
        """

        # Controlla quali task sono stati completati
        completed_tasks = state.get("completed_tasks", set())
        structured_responses = state.get("structured_responses", [])
        original_question = state.get("original_question", "")
        execution_plan = state.get("execution_plan")

        # Leggi il flag cross_domain
        cross_domain = execution_plan.cross_domain if execution_plan else False

        # Trova le risposte del mobility_team
        mobility_team_responses = []
        for team_resp in structured_responses:
            if team_resp["team_name"] == "mobility_team":
                mobility_team_responses = team_resp["structured_responses"]
                break

        # Estrai gli agenti che hanno già risposto
        completed_agents = set()
        for resp in mobility_team_responses:
            completed_agents.add(resp["agent_name"])

        # Controlla se la visualizzazione è già stata chiamata/completata
        visualization_called = False
        visualization_completed = False

        for msg in state["messages"]:
            if hasattr(msg, 'name') and msg.name == "mobility_supervisor":
                if "VISUALIZATION: Generating graphs" in msg.content:
                    visualization_called = True
            if hasattr(msg, 'name') and msg.name == "mobility_visualization":
                visualization_completed = True
                break

        print(f"\n{'=' * 60}")
        print("MOBILITY SUPERVISOR STATUS:")
        print(f"Original question: {original_question}")
        print(f"Completed tasks: {completed_tasks}")
        print(f"Cross-Domain Mode: {cross_domain}")
        print(f"Completed agents: {completed_agents}")
        print(f"Visualization called: {visualization_called}")
        print(f"Visualization completed: {visualization_completed}")
        print(f"{'=' * 60}\n")



        # Prepara il messaggio per l'LLM con context
        context_message = (
            f"CURRENT STATE:\n"
            f"- Original user question: '{original_question}'\n"
            f"- Cross-domain mode: {cross_domain} {'(SKIP VISUALIZATION!)' if cross_domain else ''}\n"
            f"- Completed agents: {list(completed_agents)}\n"
            f"- Available workers: {members}\n"
            f"- Data collected: {len(mobility_team_responses)} agent responses\n"
            f"- Visualization called: {visualization_called}\n"
            f"- Visualization completed: {visualization_completed}\n\n"
            f"TASK: Analyze the current state and decide:\n"
            f"1. Do we need to call more data workers?\n"
            f"2. Should we generate visualizations? (Remember: skip if cross_domain = True)\n"
            f"3. Are we ready to FINISH?\n\n"
        )

        if cross_domain:
            context_message += "⚠️ IMPORTANT: cross_domain = True, so skip visualization and go to FINISH after data collection!\n"
        else:
            context_message += "Remember: Prefer visualization unless the user explicitly wants only text/numbers.\n"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context_message}
        ] + state["messages"][-2:]  # Ultimi 2 messaggi per context

        response = llm.with_structured_output(Router).invoke(messages)
        goto = response["next"]

        # Safety checks
        if goto == "mobility_visualization_node" and (visualization_called or visualization_completed):
            print("⚠️  Visualization already called/completed, routing to FINISH")
            goto = "FINISH"

        if visualization_completed and goto != "FINISH":
            print("⚠️  Visualization completed, forcing FINISH")
            goto = "FINISH"

        if goto == "FINISH":
            goto = END

        print(f"Mobility supervisor decision: {goto}")
        print(f"{'=' * 60}\n")

        # Messaggio di tracking
        if goto == "mobility_visualization_node":
            tracking_msg = "VISUALIZATION: Generating graphs"
        elif goto == END:
            tracking_msg = "FINISH: Completing mobility team workflow"
        else:
            tracking_msg = f"ROUTING: Calling {goto}"

        update_msg = AIMessage(
            content=tracking_msg,
            name="mobility_supervisor"
        )

        return Command(
            goto=goto,
            update={
                "next": goto,
                "messages": [update_msg]
            }
        )

    return supervisor_node