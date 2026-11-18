# llm-request-hedging

Tail-latency control for LLM calls: start a second (hedged) request when the
first one is slow, take whichever answers first, and cancel the other.

Slow completions are rare but expensive for the caller. Waiting for a stuck
request is worse than paying for one extra call, as long as the extra calls are
bounded. This repo keeps that trade-off explicit and testable offline.

Pure Python 3.12 standard library, no dependencies, no network, no API key.

## Layout

```
hedging/
  provider.py   Request / Response types, provider interface, scripted fake
  errors.py     retryable vs. fatal provider errors
  hedge.py      hedged_complete(): delay, attempt cap, deadline, cancellation
tests/          unittest suite
```

## Usage

```python
import asyncio
from hedging import HedgePolicy, Request, hedged_complete

result = asyncio.run(
    hedged_complete(provider, Request(prompt="hi"), HedgePolicy(hedge_delay=0.4))
)
print(result.response.text, result.attempts_started)
```

## Choosing a delay

`hedging.latency.LatencyTracker` keeps a rolling window of observed latencies
and suggests a delay at a chosen percentile (p95 by default), falling back to a
static value until it has enough samples. Hedging at roughly p95 keeps the
extra-call rate near 5%.

## Simulated results

`scripts/simulate.py` draws 10,000 synthetic latencies (seed 7): a lognormal
body with an 0.8 s median plus a 3% chance of an 8 s spike. These are model
numbers, not measurements of a real provider.

```
 hedge delay     p50     p95     p99  extra calls
        none    0.81    1.31    8.00        0.0%
        0.8s    0.81    1.31    1.69       52.0%
        1.2s    0.81    1.31    2.08        8.0%
        1.6s    0.81    1.31    2.48        3.0%
        2.4s    0.81    1.31    3.28        2.8%
```

A delay just above the body of the distribution removes the spike from p99 for
a few percent of extra calls. Hedging at the median doubles the traffic and
buys little more.

Retryable failures start the next attempt immediately instead of waiting for the
delay. Fatal errors (non-429 4xx) are raised at once and never hedged.

## Validate

```
make validate
```
