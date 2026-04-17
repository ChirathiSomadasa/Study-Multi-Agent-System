"""
graph.py — Builds and compiles the LangGraph StateGraph for the Study MAS.
"""

from typing import Optional
from langgraph.graph import StateGraph, END

from state import StudyState
from agents.coordinator import coordinator_node
from agents.content_analyst import content_analyst_node
from agents.quiz_generator import quiz_generator_node
from agents.evaluator import evaluator_node
from logger import AgentLogger

def build_graph(model: str = "gemma3:1b", logger: Optional[AgentLogger] = None) -> StateGraph:
    """
    Construct and compile the multi-agent LangGraph pipeline.
    """
    graph = StateGraph(StudyState)

    # Register nodes 
    graph.add_node(
        "coordinator",
        lambda state: coordinator_node(state, model=model, logger=logger),
    )
    graph.add_node(
        "content_analyst",
        lambda state: content_analyst_node(state, model=model, logger=logger),
    )
    graph.add_node(
        "quiz_generator",
        lambda state: quiz_generator_node(state, model=model, logger=logger),
    )
    graph.add_node(
        "evaluator",
        lambda state: evaluator_node(state, model=model, logger=logger),
    )

    # Wire edges (sequential pipeline)
    graph.set_entry_point("coordinator")
    graph.add_edge("coordinator", "content_analyst")
    graph.add_edge("content_analyst", "quiz_generator")
    graph.add_edge("quiz_generator", "evaluator")
    graph.add_edge("evaluator", END)

    return graph.compile()