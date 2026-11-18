import unittest

from hedging.latency import MIN_SAMPLES, LatencyTracker

FALLBACK = 0.5


class LatencyTrackerTest(unittest.TestCase):
    def test_uses_fallback_until_enough_samples(self):
        tracker = LatencyTracker(FALLBACK)
        for _ in range(MIN_SAMPLES - 1):
            tracker.record(0.1)
        self.assertEqual(tracker.hedge_delay(), FALLBACK)

    def test_returns_percentile_of_window(self):
        tracker = LatencyTracker(FALLBACK, percentile=0.9)
        for i in range(1, 101):
            tracker.record(i / 100)
        self.assertEqual(tracker.hedge_delay(), 0.9)

    def test_window_drops_old_samples(self):
        tracker = LatencyTracker(FALLBACK, window=MIN_SAMPLES)
        for _ in range(MIN_SAMPLES):
            tracker.record(5.0)
        for _ in range(MIN_SAMPLES):
            tracker.record(0.1)
        self.assertEqual(tracker.hedge_delay(), 0.1)

    def test_rejects_bad_percentile(self):
        with self.assertRaisesRegex(ValueError, "1.5"):
            LatencyTracker(FALLBACK, percentile=1.5)


if __name__ == "__main__":
    unittest.main()
