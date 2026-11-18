"""Rolling latency window that suggests a hedge delay from a percentile."""

import math
from collections import deque

DEFAULT_WINDOW = 200
DEFAULT_PERCENTILE = 0.95
MIN_SAMPLES = 20


class LatencyTracker:
    def __init__(
        self,
        fallback_delay: float,
        window: int = DEFAULT_WINDOW,
        percentile: float = DEFAULT_PERCENTILE,
    ) -> None:
        if not 0 < percentile < 1:
            raise ValueError(f"percentile must be in (0, 1), got {percentile}")
        if window < 1:
            raise ValueError(f"window must be >= 1, got {window}")
        self._fallback = fallback_delay
        self._percentile = percentile
        self._samples: deque[float] = deque(maxlen=window)

    def record(self, seconds: float) -> None:
        self._samples.append(seconds)

    def hedge_delay(self) -> float:
        # Too few samples make the percentile noise; use the static delay.
        if len(self._samples) < MIN_SAMPLES:
            return self._fallback
        ordered = sorted(self._samples)
        rank = math.ceil(self._percentile * len(ordered)) - 1
        return ordered[rank]
