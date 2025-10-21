from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.prebuilt import ToolNode

from backend.models.state import State


def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }


def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )


def _print_event(event: dict, _printed: set, max_length=1500):
    current_state = event.get("dialog_state")
    if current_state:
        print("Currently in: ", current_state[-1])
    message = event.get("messages")
    if message:
        if isinstance(message, list):
            message = message[-1]
        if message.id not in _printed:
            msg_repr = message.pretty_repr(html=True)
            if len(msg_repr) > max_length:
                msg_repr = msg_repr[:max_length] + " ... (truncated)"
            print(msg_repr)
            _printed.add(message.id)

# Questa classe Assistant implementa un wrapper intelligente per un Runnable
# con logica di retry automatico in caso di risposte vuote.
class Assistant:
  #costruttore, salva l'oggetto Runnable (LLM) da wrappare
  def __init__(self, runnable:Runnable):
    self.runnable = runnable

  #logica principale
  #
  def __call__(self, state:State, config:RunnableConfig):
      while True:
        #Estrae la configurazione
        configuration= config.get("configurable", {})
        #Recupera l'ID del passeggero dalla config
        user_id= config.get("user_id", None)
        #Aggiunge passenger_id allo stato come user_info
        state = {**state, "user_info": user_id}
        #Chiama il LLM/runnable con lo stato aggiornato.
        result = self.runnable.invoke(state)
        #if the LLM happens to return an empty response, we will re-prompt it
        #for an actual response
        #Validazione della risposta (logica di retry)
        #La risposta viene considerata invalida se:
        #Non ci sono tool_calls il contenut è vuoto oppure il contenuto è una list vuota o senza testo
        if not result.tool_calls and (
            not result.content
            or isinstance(result.content, list)
            and not result.content[0].get("text")
        ):
          messages = state["messages"] + [("user", "respond with a real output")]
          state = {**state, "messages": messages}
        else:
          break
      return {"messages": result}