"""
Nodo per la generazione di grafici cross-domain basato su LLM Intent Detection.
Questo nodo viene chiamato quando execution_plan.cross_domain = True.
"""

from typing import Literal
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pydantic import BaseModel, Field
from langgraph.types import Command
from langchain_core.messages import HumanMessage

from backend.models.state import State, GraphData



