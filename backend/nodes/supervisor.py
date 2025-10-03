from typing import Literal
from langgraph.types import Command
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
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
        f"5. Check which tasks are already completed before assigning new ones\n"
        f"6. Go to FINISH only when ALL necessary tasks have been completed\n\n"
        f"EXAMPLE:\n"
        f"Question: 'How did subject 1 sleep and cook in the last month?'\n"
        f"- First step: next='sleep_node', task='Analyze how subject 1 slept in the last month'\n"
        f"- Second step: next='kitchen_node', task='Analyze how subject 1 cooked in the last month'\n"
        f"- Third step: next='FINISH' (all tasks completed)\n"
    )

    def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:
        # Estrai tutti i task completati
        completed_tasks = set()
        structured_responses = state.get("structured_responses", [])

        for response in structured_responses:
            task = response.get("task", "").strip()
            if task:
                completed_tasks.add(task)

        print(f"DEBUG - Tasks already completed: {completed_tasks}")

        # Costruisci i messaggi
        messages = [SystemMessage(content=system_prompt)]

        for msg in state["messages"]:
            messages.append(msg)

        # Informa il supervisore sui task completati
        if completed_tasks:
            completion_info = "COMPLETED TASKS:\n" + "\n".join([f"- {task}" for task in completed_tasks])
            completion_info += "\n\nDo NOT assign these exact tasks again. If all required tasks are done, go to FINISH."
            messages.append(HumanMessage(content=completion_info))

        response = llm.with_structured_output(SupervisorRouter).invoke(messages)
        goto = response["next"]
        task_description = response.get("task", "").strip()

        print(f"DEBUG - Supervisor decision: goto={goto}, task={task_description}")

        # Verifica se il task è già stato completato
        if task_description in completed_tasks:
            print(f"WARNING - Task '{task_description}' already completed, going to FINISH")
            goto = "FINISH"

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
                SystemMessage(
                    content="You are an assistant receiving structured data from various agents and synthesizing it into an answer for the user."),
                HumanMessage(content=synthesis_prompt)
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

        # Assegna il task all'agente selezionato
        return Command(
            goto=goto,
            update={
                "messages": [HumanMessage(content=f"[TASK]: {task_description}", name="supervisor_instruction")],
                "next": goto
            }
        )

    return supervisor_node