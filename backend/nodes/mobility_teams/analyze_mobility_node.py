import json
from typing import Literal
from google.api_core import exceptions
from langgraph.prebuilt import create_react_agent

from backend.config.settings import invoke_with_retry
from backend.models.results import MobilityAnalysisResult, ErrorResult
from backend.models.state import State, AgentResponse, TeamResponse
from langgraph.types import Command
from langchain_core.messages import HumanMessage, ToolMessage

from backend.tools.mobility_tools import analyze_mobility_patterns


def create_analyze_mobility_agent(llm):
    tools = [analyze_mobility_patterns]
    return create_react_agent(llm, tools=tools)


def create_analyze_mobility_node(analyze_mobility_agent):
    def _node(state: State) -> Command[Literal["mobility_team_supervisor"]]:
        # Estrai task
        task = None
        for msg in reversed(state["messages"]):
            if hasattr(msg, 'name') and msg.name == "supervisor_instruction":
                task = msg.content.replace("[TASK]: ", "")
                break

        print(f"DEBUG - Mobility agent received task: '{task}'")
        message = task or "Analizza la mobilità del soggetto richiesto."


        try:
            result = invoke_with_retry(analyze_mobility_agent, [HumanMessage(content=message)], 3)
        except exceptions.ResourceExhausted as e:
            print(f"Failed after all retries: {e}")
        print("result " + str(result))


        agent_data: MobilityAnalysisResult | ErrorResult | None = None
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
            agent_data = {"error": "Nessuna risposta dall'agente mobility"}


        agent_response: AgentResponse = {
            "task": message,
            "agent_name": "mobility_agent",
            "data": agent_data
        }

        print(f"DEBUG - Mobility agent response type: {type(agent_response['data'])}")


        current_responses = state.get("structured_responses", [])


        mobility_team_response = None
        for team_resp in current_responses:
            if team_resp["team_name"] == "mobility_team":
                mobility_team_response = team_resp
                break


        if mobility_team_response:

            mobility_team_response["structured_responses"].append(agent_response)
            updated_responses = current_responses
        else:

            new_team_response: TeamResponse = {
                "structured_responses": [agent_response],
                "team_name": "mobility_team"
            }
            updated_responses = current_responses + [new_team_response]


        completed_tasks = state.get("completed_tasks", set())
        completed_tasks.add(task)

        return Command(
            update={
                "structured_responses": updated_responses,
                "completed_tasks": completed_tasks,
                "messages": [HumanMessage(content=f"Mobility completed: {task}", name="mobility_node_response")]
            },
            goto="mobility_team_supervisor"
        )

    return _node