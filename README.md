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

## Validate

```
make validate
```
