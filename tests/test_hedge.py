import asyncio
import unittest

from hedging import (
    AttemptsExhausted,
    DeadlineExceeded,
    FakeProvider,
    FatalError,
    HedgePolicy,
    Request,
    Step,
    hedged_complete,
)

REQUEST = Request(prompt="ping")
FAST = 0.01
SLOW = 0.4
HEDGE_DELAY = 0.05


def run(provider, policy):
    return asyncio.run(hedged_complete(provider, REQUEST, policy))


class HedgeTest(unittest.TestCase):
    def test_fast_primary_never_hedges(self):
        provider = FakeProvider([Step(FAST)])
        result = run(provider, HedgePolicy(hedge_delay=HEDGE_DELAY))
        self.assertEqual(result.attempts_started, 1)
        self.assertEqual(result.winner, 0)
        self.assertEqual(provider.calls, 1)

    def test_slow_primary_loses_to_hedge_and_is_cancelled(self):
        provider = FakeProvider([Step(SLOW), Step(FAST)])
        result = run(provider, HedgePolicy(hedge_delay=HEDGE_DELAY))
        self.assertEqual(result.winner, 1)
        self.assertEqual(result.response.text, "answer-1")
        self.assertEqual(provider.cancelled, 1)

    def test_failed_primary_retries_without_waiting_for_delay(self):
        provider = FakeProvider([Step(FAST, fail=True), Step(FAST)])
        result = run(provider, HedgePolicy(hedge_delay=10.0, deadline=5.0))
        self.assertEqual(result.winner, 1)

    def test_attempts_are_capped(self):
        provider = FakeProvider([Step(FAST, fail=True)])
        with self.assertRaises(AttemptsExhausted) as ctx:
            run(provider, HedgePolicy(hedge_delay=HEDGE_DELAY, max_attempts=3))
        self.assertEqual(provider.calls, 3)
        self.assertIn("3 attempt(s)", str(ctx.exception))

    def test_deadline_cancels_everything(self):
        provider = FakeProvider([Step(SLOW)])
        with self.assertRaises(DeadlineExceeded) as ctx:
            run(provider, HedgePolicy(hedge_delay=HEDGE_DELAY, deadline=0.12))
        self.assertIn("0.12s", str(ctx.exception))
        self.assertEqual(provider.cancelled, provider.calls)

    def test_fatal_error_is_not_retried(self):
        class Rejecting:
            calls = 0

            async def complete(self, request):
                self.calls += 1
                raise FatalError("400 bad request")

        provider = Rejecting()
        with self.assertRaises(FatalError):
            run(provider, HedgePolicy(hedge_delay=HEDGE_DELAY))
        self.assertEqual(provider.calls, 1)

    def test_policy_rejects_bad_values(self):
        for kwargs in (
            {"hedge_delay": -1},
            {"hedge_delay": 0.1, "max_attempts": 0},
            {"hedge_delay": 0.1, "deadline": 0},
        ):
            with self.assertRaises(ValueError, msg=str(kwargs)):
                HedgePolicy(**kwargs)


if __name__ == "__main__":
    unittest.main()
