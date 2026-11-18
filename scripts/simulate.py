"""Compare tail latency with and without hedging on seeded synthetic latencies.

Latencies are drawn, not measured: a lognormal body plus an occasional slow
spike. The numbers describe this model, not any real provider.
"""

import math
import random
import sys

SEED = 7
REQUESTS = 10_000
BODY_MEDIAN_S = 0.8
BODY_SIGMA = 0.25
SPIKE_RATE = 0.03
SPIKE_S = 8.0
HEDGE_DELAYS_S = (0.8, 1.2, 1.6, 2.4)


def draw(rng: random.Random) -> float:
    if rng.random() < SPIKE_RATE:
        return SPIKE_S
    return rng.lognormvariate(math.log(BODY_MEDIAN_S), BODY_SIGMA)


def percentile(ordered: list[float], q: float) -> float:
    return ordered[math.ceil(q * len(ordered)) - 1]


def simulate(delay: float | None) -> tuple[list[float], float]:
    rng = random.Random(SEED)
    latencies: list[float] = []
    hedged = 0
    for _ in range(REQUESTS):
        primary = draw(rng)
        backup = draw(rng)
        if delay is not None and primary > delay:
            hedged += 1
            latencies.append(min(primary, delay + backup))
        else:
            latencies.append(primary)
    return sorted(latencies), hedged / REQUESTS


def main() -> int:
    print(f"synthetic latencies, seed={SEED}, n={REQUESTS}, spike rate={SPIKE_RATE}")
    print(f"{'hedge delay':>12} {'p50':>7} {'p95':>7} {'p99':>7} {'extra calls':>12}")
    rows = [("none", *simulate(None))] + [
        (f"{d:.1f}s", *simulate(d)) for d in HEDGE_DELAYS_S
    ]
    for label, ordered, extra in rows:
        print(
            f"{label:>12} {percentile(ordered, 0.5):7.2f} "
            f"{percentile(ordered, 0.95):7.2f} {percentile(ordered, 0.99):7.2f} "
            f"{extra:11.1%}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
