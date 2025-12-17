import asyncio


def test_build_rag_loop_graph_smoke(monkeypatch, tmp_path):
    """Graph should build without invoking network/tooling."""

    # Factories require an API key at construction time.
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    from src.agents.graphs import build_rag_loop_graph

    graph = build_rag_loop_graph(repo_path=str(tmp_path))

    assert graph is not None
    assert callable(graph)

    from src.agents.factories import Synthesizer
    from src.agents.graphs import get_node_actions
    from src.agents.nodes import ExplorerSelectNode, IndexerNode, RetrieverNode, SynthInputNode

    actions = get_node_actions()
    assert isinstance(actions, dict)
    assert set(actions.keys()) == {
        RetrieverNode.id,
        ExplorerSelectNode.id,
        IndexerNode.id,
        SynthInputNode.id,
        Synthesizer.NAME,
    }


def test_explorer_select_node_writes_invocation_state():
    from strands.agent.agent_result import AgentResult
    from strands.types.content import Message

    from src.agents.nodes.explorer_select import ExplorerSelectNode

    class FakeStructuredOutput:
        def __init__(self, files):
            self.files = files

    class FakeAgent:
        async def invoke_async(self, task, invocation_state=None, **kwargs):
            message: Message = {"role": "assistant", "content": [{"text": "ok"}]}  # type: ignore[typeddict-item]
            return AgentResult(
                stop_reason="end_turn",
                message=message,
                metrics=None,
                state={},
                interrupts=None,
                structured_output=FakeStructuredOutput(
                    files=[
                        "/abs/repo/a.py",
                        "/abs/repo/b.py",
                    ]
                ),
            )

    async def run():
        node = ExplorerSelectNode(agent=FakeAgent())  # type: ignore[arg-type]
        invocation_state = {"question": "q", "already_indexed": set()}
        result = await node.invoke_async("q", invocation_state=invocation_state)
        return invocation_state, result

    invocation_state, result = asyncio.run(run())

    assert result is not None
    assert invocation_state["explorer_files_abs"] == ["/abs/repo/a.py", "/abs/repo/b.py"]


