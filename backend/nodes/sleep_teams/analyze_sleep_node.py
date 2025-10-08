import json
from typing import Literal

from langgraph.prebuilt import create_react_agent

from backend.models.results import SleepAnalysisResult, ErrorResult
from backend.models.state import State, AgentResponse, TeamResponse
from langgraph.types import Command
from langchain_core.messages import HumanMessage, ToolMessage

from backend.tools.sleep_tools import analyze_sleep_changes


def create_analyze_sleep_agent(llm):
    tools = [analyze_sleep_changes]
    system_message = (
        "You are a specialized agent for analyzing sleep patterns and quality. "
        "You MUST use the analyze_sleep_changes tool to retrieve sleep data. "
        "Always call the tool with the subject_id and period from the user's request. "
        "Focus exclusively on sleep metrics: sleep duration, sleep phases (REM, deep, light), "
        "sleep efficiency, wake-up counts, and out-of-bed episodes. "
        "Do NOT analyze heart rate or respiratory rate in detail - those are handled by other specialized agents."
    )
    return create_react_agent(llm, tools=tools, prompt=system_message)


def create_analyze_sleep_node(analyze_sleep_agent):
    def _node(state: State) -> Command[Literal["sleep_team_supervisor"]]:

        task = None
        for msg in reversed(state["messages"]):
            if hasattr(msg, 'name') and msg.name == "supervisor_instruction":
                task = msg.content.replace("[TASK]: ", "")
                break

        print(f"DEBUG - Sleep agent received task: '{task}'")
        message = task or "Analizza il sonno del soggetto richiesto."


        focused_state = {"messages": [HumanMessage(content=message)]}
        result = analyze_sleep_agent.invoke(focused_state)
        print("result " + str(result))


        agent_data: SleepAnalysisResult | ErrorResult | None = None
        for msg in result["messages"]:
            if isinstance(msg, ToolMessage):
                if isinstance(msg.content, dict):
                    raw_data = msg.content
                elif isinstance(msg.content, str):
                    try:
                        raw_data = json.loads(msg.content)
                    except json.JSONDecodeError:
                        raw_data = {"error": "JSON parsing failed"}
                else:
                    raw_data = {"error": f"Formato risposta non valido: {type(msg.content)}"}

                if "error" in raw_data:
                    agent_data = raw_data
                else:
                    agent_data = raw_data
                break

        if not agent_data:
            agent_data = {"error": "Nessuna risposta dall'agente sleep"}


        agent_response: AgentResponse = {
            "task": message,
            "agent_name": "sleep_agent",
            "data": agent_data
        }

        print(f"DEBUG - Sleep agent response type: {type(agent_response['data'])}")


        current_responses = state.get("structured_responses", [])


        sleep_team_response = None
        for team_resp in current_responses:
            if team_resp["team_name"] == "sleep_team":
                sleep_team_response = team_resp
                break


        if sleep_team_response:

            sleep_team_response["structured_responses"].append(agent_response)
            updated_responses = current_responses
        else:

            new_team_response: TeamResponse = {
                "structured_responses": [agent_response],
                "team_name": "sleep_team"
            }
            updated_responses = current_responses + [new_team_response]


        completed_tasks = state.get("completed_tasks", set())
        completed_tasks.add(task)

        return Command(
            update={
                "structured_responses": updated_responses,
                "completed_tasks": completed_tasks,
                "messages": [HumanMessage(content=f"SleepNode completed: {task}", name="sleep_node_response")],
            },
            goto="sleep_team_supervisor"
        )

    return _node