"""LangGraph assembly with conditional routing and a bounded retry loop."""
from langgraph.graph import END, START, StateGraph

from .nodes import build_nodes
from .state import AgentState

_STOP = ("chitchat", "iteration_limit", "tool_failed", "insufficient_evidence")


def build_graph(services):
    n = build_nodes(services)
    g = StateGraph(AgentState)
    for name, fn in n.items():
        g.add_node(name, fn)

    def stop_or(nxt):
        return lambda st: "format" if st.get("status") in _STOP else nxt

    g.add_edge(START, "classify")
    g.add_conditional_edges("classify", stop_or("select_tool"), {"format": "format", "select_tool": "select_tool"})
    g.add_conditional_edges("select_tool", stop_or("plan"), {"format": "format", "plan": "plan"})
    g.add_edge("plan", "retrieve")
    g.add_edge("retrieve", "validate")
    g.add_conditional_edges("validate", stop_or("generate"), {"format": "format", "generate": "generate"})

    def after_generate(st):
        if st.get("status") in ("iteration_limit", "answered"):
            return "format"
        return "generate" if st.get("error") and st.get("attempts", 0) < 2 else "format"

    g.add_conditional_edges("generate", after_generate, {"generate": "generate", "format": "format"})
    g.add_edge("format", END)
    return g.compile()


def run_agent(services, **inputs):
    if not hasattr(services, "_graph"):
        services._graph = build_graph(services)
    state = {"warnings": [], "trace": [], "steps": 0, "attempts": 0, "history": [], "doc_ids": [], **inputs}
    return services._graph.invoke(state, config={"recursion_limit": services.settings.agent_max_steps * 2 + 10})
