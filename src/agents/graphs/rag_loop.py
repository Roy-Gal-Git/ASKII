"""RAG loop graph (Retriever → Synthesizer, else Explorer → Indexer → Retriever).

This is the primary ASKII orchestration flow.
"""

from typing import Any, Callable

from strands.multiagent import GraphBuilder

from src.agents.factories import Explorer, Synthesizer
from src.agents.nodes import IndexerNode, RetrieverNode
from src.agents.nodes.explorer_select import ExplorerSelectNode
from src.agents.nodes.synth_input import SynthInputNode

MAX_NODE_EXECUTIONS = 20
EXECUTION_TIMEOUT_S = 300


def _approved_from_graph_state(state: Any) -> bool:
    """Read the Retriever node's approval decision from GraphState."""

    try:
        retriever_result = state.results.get("retriever")
        if not retriever_result:
            return False

        multi_result = retriever_result.result
        inner_agent_result = multi_result.results["retriever"].result
        return bool(getattr(inner_agent_result, "state", {}).get("approved", False))
    except Exception:
        return False


def build_rag_loop_graph(
    *,
    repo_path: str,
) -> Any:
    """Build the primary ASKII query graph (cyclic feedback loop).

    Execution:
    - Retriever queries Chroma
    - If strong enough (or loop cap reached), SynthInput formats the evidence and Synthesizer answers
    - Otherwise Explorer selects files → Indexer indexes them → loop back to Retriever

    Args:
        repo_path: Absolute path to the repository root (used to configure Explorer).

    Returns:
        Built Strands graph instance.
    """

    explorer_agent = Explorer(repo_path=repo_path).create()
    synthesizer_agent = Synthesizer().create()

    retriever = RetrieverNode()
    explorer = ExplorerSelectNode(agent=explorer_agent)
    indexer = IndexerNode()
    synth_input = SynthInputNode()

    builder = GraphBuilder()

    # Nodes
    builder.add_node(retriever, RetrieverNode.id)
    builder.add_node(explorer, ExplorerSelectNode.id)
    builder.add_node(indexer, IndexerNode.id)
    builder.add_node(synth_input, SynthInputNode.id)
    builder.add_node(synthesizer_agent, synthesizer_agent.name)

    # Conditional branch on Retriever approval
    is_approved: Callable[[Any], bool] = _approved_from_graph_state
    builder.add_edge(RetrieverNode.id, SynthInputNode.id, condition=is_approved)
    builder.add_edge(RetrieverNode.id, ExplorerSelectNode.id, condition=lambda s: not is_approved(s))

    # Loop path
    builder.add_edge(ExplorerSelectNode.id, IndexerNode.id)
    builder.add_edge(IndexerNode.id, RetrieverNode.id)

    # Answer path
    builder.add_edge(SynthInputNode.id, synthesizer_agent.name)

    builder.set_entry_point(RetrieverNode.id)
    builder.set_max_node_executions(MAX_NODE_EXECUTIONS)
    builder.set_execution_timeout(EXECUTION_TIMEOUT_S)
    builder.reset_on_revisit(True)

    return builder.build()


def get_node_actions() -> dict[str, str]:
    """Return a mapping of graph node_id -> human-friendly action label."""

    return {
        RetrieverNode.id: RetrieverNode.ACTION,
        ExplorerSelectNode.id: ExplorerSelectNode.ACTION,
        IndexerNode.id: IndexerNode.ACTION,
        SynthInputNode.id: SynthInputNode.ACTION,
        Synthesizer.NAME: Synthesizer.ACTION,
    }

