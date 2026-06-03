"""
Message Bus — Chapter 7: Multi-Agent Systems and Orchestration

In-process message passing between agents. Each agent gets a dedicated queue.
Swap for Redis pub/sub or SQS when agents run in separate processes.

Design principle: coordination protocols should be boring.
Message passing through a typed queue handles 90% of real coordination requirements.
"""
import queue
import time
import uuid
from dataclasses import dataclass, field
from typing import Literal, Optional


MessageType = Literal["task", "result", "error", "request", "ack"]


@dataclass
class AgentMessage:
    sender:       str
    recipient:    str
    message_type: MessageType
    content:      dict
    message_id:   str   = field(default_factory=lambda: str(uuid.uuid4())[:8])
    timestamp:    float = field(default_factory=time.time)
    reply_to:     Optional[str] = None   # message_id this is replying to


class MessageBus:
    """
    In-process message bus for multi-agent coordination.
    Thread-safe: uses queue.Queue per agent (blocking get with timeout).

    Production swap: replace _queues with Redis pub/sub channels or SQS queues.
    """

    def __init__(self):
        self._queues:     dict[str, queue.Queue] = {}
        self._message_log: list[AgentMessage]    = []

    # ── Agent registration ────────────────────────────────────────────────────

    def register_agent(self, agent_id: str) -> None:
        """Create a dedicated inbound queue for an agent."""
        if agent_id not in self._queues:
            self._queues[agent_id] = queue.Queue()

    def deregister_agent(self, agent_id: str) -> None:
        self._queues.pop(agent_id, None)

    def registered_agents(self) -> list[str]:
        return list(self._queues.keys())

    # ── Messaging ────────────────────────────────────────────────────────────

    def send(self, message: AgentMessage) -> None:
        """Route message to the recipient's queue. Raises if recipient not registered."""
        if message.recipient not in self._queues:
            raise ValueError(
                f"Recipient '{message.recipient}' not registered. "
                f"Registered agents: {self.registered_agents()}"
            )
        self._queues[message.recipient].put(message)
        self._message_log.append(message)

    def receive(self, agent_id: str, timeout: float = 5.0) -> Optional[AgentMessage]:
        """
        Blocking receive with timeout. Returns None if no message arrives within timeout.
        Raises if agent_id not registered.
        """
        if agent_id not in self._queues:
            raise ValueError(f"Agent '{agent_id}' not registered")
        try:
            return self._queues[agent_id].get(timeout=timeout)
        except queue.Empty:
            return None

    def receive_nowait(self, agent_id: str) -> Optional[AgentMessage]:
        """Non-blocking receive. Returns None immediately if queue is empty."""
        if agent_id not in self._queues:
            raise ValueError(f"Agent '{agent_id}' not registered")
        try:
            return self._queues[agent_id].get_nowait()
        except queue.Empty:
            return None

    def pending_count(self, agent_id: str) -> int:
        """Number of messages waiting for an agent."""
        return self._queues.get(agent_id, queue.Queue()).qsize()

    # ── Convenience builders ──────────────────────────────────────────────────

    @staticmethod
    def task_message(sender: str, recipient: str, task: dict) -> AgentMessage:
        return AgentMessage(sender=sender, recipient=recipient,
                            message_type="task", content=task)

    @staticmethod
    def result_message(sender: str, recipient: str, result: dict,
                       reply_to: Optional[str] = None) -> AgentMessage:
        return AgentMessage(sender=sender, recipient=recipient,
                            message_type="result", content=result, reply_to=reply_to)

    @staticmethod
    def error_message(sender: str, recipient: str, error: str,
                      reply_to: Optional[str] = None) -> AgentMessage:
        return AgentMessage(sender=sender, recipient=recipient,
                            message_type="error", content={"error": error}, reply_to=reply_to)

    # ── Diagnostics ──────────────────────────────────────────────────────────

    def message_log(self) -> list[AgentMessage]:
        return list(self._message_log)

    def stats(self) -> dict:
        return {
            "registered_agents": self.registered_agents(),
            "total_messages":    len(self._message_log),
            "pending_by_agent":  {aid: self.pending_count(aid) for aid in self._queues},
        }


# ── Quick smoke test ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    bus = MessageBus()
    bus.register_agent("orchestrator")
    bus.register_agent("researcher")
    bus.register_agent("writer")

    # Orchestrator sends task to researcher
    task = MessageBus.task_message("orchestrator", "researcher",
                                    {"goal": "Research AI agent reliability patterns"})
    bus.send(task)

    # Researcher receives and replies
    msg = bus.receive("researcher", timeout=1.0)
    print(f"Researcher received: [{msg.message_type}] {msg.content}")

    result = MessageBus.result_message("researcher", "orchestrator",
                                        {"findings": "Reliability requires boundary design"},
                                        reply_to=msg.message_id)
    bus.send(result)

    # Orchestrator receives result
    reply = bus.receive("orchestrator", timeout=1.0)
    print(f"Orchestrator received: [{reply.message_type}] {reply.content}")
    print(f"Stats: {bus.stats()}")
