from typing import Literal
from langgraph.types import Command
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.graph import END

from backend.models.state import State, SupervisorRouter


def make_supervisor_node(llm, members: list[str]):
    options = ["FINISH"] + members
    system_prompt = (
        f"You are a smart supervisor coordinating these specialized agents: {members}.\n\n"
        f"AGENTS:\n"
        f"- sleep_agent: analyzes ONLY sleep\n"
        f"- kitchen_agent: analyzes ONLY the kitchen\n"
        f"- mobility_agent: analyzes ONLY mobility\n\n"
        f"IMPORTANT: Agents return PYTHON TypedDict data (AgentResponse) with this structure:\n"
        f'{{"task": "description of the task", "agent_name": "<agent_name>", "data": {{structured data (TypedDict)}}}}\n\n'
        f"When synthesizing responses, interpret the TypedDicts and create a readable answer for the user.\n\n"
        f"RULES:\n"
        f"1. Identify which agents are needed for the question\n"
        f"2. Call ONE agent at a time\n"
        f"3. For each agent, write in the 'task' field ONLY the part of the question that concerns it\n"
        f"4. IMPORTANT: If the question mentions a time period (e.g., 'last 20 days', 'last month', 'from X to Y'), "
        f"YOU MUST include it in the agent's task\n"
        f"5. Do NOT repeat agents already called\n"
        f"6. Go to FINISH only when ALL necessary agents have responded\n\n"
        f"7. A task is COMPLETED when it has 'completed' associated\n"
        f"EXAMPLE:\n"
        f"Question: 'How did subject 1 sleep and cook in the last month?'\n"
        f"- First step: next='sleep_node', task='Analyze how subject 1 slept in the last month'\n"
        f"- Second step: next='kitchen_node', task='Analyze how subject 1 cooked in the last month'\n"
    )

    def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:

        messages = [{"role": "system", "content": system_prompt}] + state["messages"]
        response = llm.with_structured_output(SupervisorRouter).invoke(messages)
        goto = response["next"]
        task_description = response.get("task", "")

        print(f"DEBUG - Supervisor decision: goto={goto}, task={task_description}")

        if goto == "FINISH":
            original_question = state["messages"][0].content if state["messages"] else ""
            synthesis_prompt = (
                f"Original question: {original_question}\n\n"
                f"Structured data received from agents:\n{state.get('structured_responses', [])}\n\n"
                f"INSTRUCTIONS:\n"
                f"1. Interpret the TypedDicts received from each agent\n"
                f"2. Interpret numbers and metrics in an understandable way\n"
                f"3. Provide a complete, clear, and readable answer that addresses the original question\n"
                f"4. Highlight trends or changes if any\n"
                f"5. Use natural and accessible language"
            )

            synthesis_messages = [
                {"role": "system", "content": "You are an assistant receiving structured data from various agents and synthesizing it into an answer for the user."},
                {"role": "user", "content": synthesis_prompt}
            ]
            final_response = llm.invoke(synthesis_messages)
            final_content = final_response.content

            return Command(
                goto=END,
                update={
                    "messages": [AIMessage(content=final_content, name="supervisor")],
                    "next": "FINISH"
                }
            )
            goto = END

        # Pass the task to the selected agent
        return Command(
            goto=goto,
            update={
                "messages": [HumanMessage(content=f"[TASK]: {task_description}", name="supervisor_instruction")],
                "next": goto
            }
        )

    return supervisor_node
