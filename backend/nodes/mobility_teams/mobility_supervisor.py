from typing import Literal, TypedDict
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.types import Command
from langgraph.graph import END
from langchain_core.messages import AIMessage
from google.api_core import exceptions

from backend.config.settings import invoke_with_structured_output
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
        "WHEN TO USE VISUALIZATION:\n"
        "Generate graphs if user asks for:\n"
        "   - Visual representation ('mostrami', 'visualizza', 'grafico')\n"
        "   - Analysis that benefits from graphs ('pattern di movimento', 'analizza mobilità')\n"
        "   - Room distribution or presence patterns\n"
        "   - Time-based analysis (activity by time slot)\n"
        "   - Spatial movement patterns\n"
        "   - Any query where a graph would help understand the data\n\n"
        "Skip visualization if user asks for:\n"
        "   - Simple numeric answers ('quante volte si è mosso')\n"
        "   - Yes/no questions ('si muove molto?')\n"
        "   - Specific single values ('stanza più frequentata')\n"
        "   - Only textual explanations explicitly requested\n\n"
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

        print(f"\n{'=' * 60}")
        print("MOBILITY SUPERVISOR STATUS:")
        print(f"Original question: {original_question}")
        print(f"Completed tasks: {completed_tasks}")
        print(f"Cross-Domain Mode: {cross_domain}")
        print(f"Completed agents: {completed_agents}")
        print(f"{'=' * 60}\n")

        context_message = (
            f"CURRENT STATE:\n"
            f"- Original user question: '{original_question}'\n"
            f"- Cross-domain mode: {cross_domain} {'(SKIP VISUALIZATION!)' if cross_domain else ''}\n"
            f"- Completed agents: {list(completed_agents)}\n"
            f"- Available workers: {members}\n"
            f"- Data collected: {len(mobility_team_responses)} agent responses\n"
            f"TASK: Analyze the current state and decide:\n"
            f"1. Do we need to call more data workers?\n"
            f"2. Should we generate visualizations? (Remember: skip if cross_domain = True)\n"
            f"3. Are we ready to FINISH?\n\n"
        )

        if cross_domain:
            context_message += "IMPORTANT: cross_domain = True, so skip visualization and go to FINISH after data collection!\n"
        else:
            context_message += "Remember: Prefer visualization unless the user explicitly wants only text/numbers.\n"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": context_message}
        ] + state["messages"][-2:]  # Ultimi 2 messaggi per context


        try:
            response = invoke_with_structured_output(llm, Router, messages, 3 )
        except exceptions.ResourceExhausted as e:
            print(f"Failed after all retries: {e}")
        goto = response["next"]

        if goto == "FINISH":
            goto = END

        print(f"Mobility supervisor decision: {goto}")
        print(f"{'=' * 60}\n")

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