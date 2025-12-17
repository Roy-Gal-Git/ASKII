"""CLI progress rendering helpers (spinner only).

This module is intentionally lightweight. It renders a single yaspin spinner and
updates its text based on the currently executing graph node.
"""

from dataclasses import dataclass

from yaspin import yaspin
from yaspin.core import Yaspin


def format_action(*, node_id: str, node_actions: dict[str, str]) -> str:
    """Return the spinner text for a node."""

    return node_actions.get(node_id) or f"Running {node_id}"


@dataclass
class SpinnerUI:
    """Manage a single yaspin spinner."""

    node_actions: dict[str, str]
    _spinner: Yaspin
    _stopped: bool = False

    @classmethod
    def start(cls, *, node_actions: dict[str, str], text: str = "Thinking") -> "SpinnerUI":
        sp = yaspin(text=text)
        sp.start()
        return cls(node_actions=node_actions, _spinner=sp)

    def set_node(self, *, node_id: str) -> None:
        if self._stopped:
            return
        self._spinner.text = format_action(node_id=node_id, node_actions=self.node_actions)

    def stop(self) -> None:
        if self._stopped:
            return
        self._spinner.stop()
        self._stopped = True


