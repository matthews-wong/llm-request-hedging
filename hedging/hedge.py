"""Hedged completion: start another attempt when the current ones are slow."""

import asyncio
import time
from dataclasses import dataclass

from .errors import AttemptsExhausted, DeadlineExceeded, FatalError, RetryableError
from .provider import Provider, Request, Response

DEFAULT_MAX_ATTEMPTS = 2
DEFAULT_DEADLINE_S = 30.0


@dataclass(frozen=True)
class HedgePolicy:
    hedge_delay: float
    max_attempts: int = DEFAULT_MAX_ATTEMPTS
    deadline: float = DEFAULT_DEADLINE_S

    def __post_init__(self) -> None:
        if self.hedge_delay < 0:
            raise ValueError(f"hedge_delay must be >= 0, got {self.hedge_delay}")
        if self.max_attempts < 1:
            raise ValueError(f"max_attempts must be >= 1, got {self.max_attempts}")
        if self.deadline <= 0:
            raise ValueError(f"deadline must be > 0, got {self.deadline}")


@dataclass(frozen=True)
class HedgeResult:
    response: Response
    winner: int  # zero-based index of the attempt that answered first
    attempts_started: int


async def hedged_complete(
    provider: Provider, request: Request, policy: HedgePolicy
) -> HedgeResult:
    start = time.monotonic()
    pending: dict[asyncio.Task[Response], int] = {}
    started = 0
    last_error: RetryableError | None = None

    def launch() -> None:
        nonlocal started
        task = asyncio.ensure_future(provider.complete(request))
        pending[task] = started
        started += 1

    try:
        launch()
        while pending:
            remaining = policy.deadline - (time.monotonic() - start)
            if remaining <= 0:
                raise DeadlineExceeded(
                    f"no answer within {policy.deadline}s after {started} attempt(s)"
                )
            can_hedge = started < policy.max_attempts
            wait_for = min(policy.hedge_delay, remaining) if can_hedge else remaining
            done, _ = await asyncio.wait(
                pending, timeout=wait_for, return_when=asyncio.FIRST_COMPLETED
            )
            if not done:
                if can_hedge and wait_for < remaining:
                    launch()
                continue
            for task in done:
                index = pending.pop(task)
                error = task.exception()
                if error is None:
                    return HedgeResult(task.result(), index, started)
                if isinstance(error, RetryableError):
                    last_error = error
                    continue
                raise error
            if not pending and started < policy.max_attempts:
                launch()
        raise AttemptsExhausted(
            f"{started} attempt(s) failed, last error: {last_error}"
        ) from last_error
    finally:
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
