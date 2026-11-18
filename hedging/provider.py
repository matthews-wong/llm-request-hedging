"""Provider seam plus a deterministic fake that needs no network."""

import asyncio
from dataclasses import dataclass
from typing import Protocol, Sequence

from .errors import RetryableError


@dataclass(frozen=True)
class Request:
    prompt: str


@dataclass(frozen=True)
class Response:
    text: str


class Provider(Protocol):
    async def complete(self, request: Request) -> Response: ...


@dataclass(frozen=True)
class Step:
    """One scripted call: sleep `latency` seconds, then answer or fail."""

    latency: float
    fail: bool = False


class FakeProvider:
    """Plays `steps` in call order; the last step repeats once exhausted."""

    def __init__(self, steps: Sequence[Step]) -> None:
        if not steps:
            raise ValueError("FakeProvider needs at least one step")
        self._steps = list(steps)
        self.calls = 0
        self.cancelled = 0

    async def complete(self, request: Request) -> Response:
        step = self._steps[min(self.calls, len(self._steps) - 1)]
        index = self.calls
        self.calls += 1
        try:
            await asyncio.sleep(step.latency)
        except asyncio.CancelledError:
            self.cancelled += 1
            raise
        if step.fail:
            raise RetryableError(f"scripted failure on call {index}")
        return Response(text=f"answer-{index}")
