"""Failure classes a hedging layer needs to tell apart."""


class ProviderError(Exception):
    """Base class for provider failures."""


class RetryableError(ProviderError):
    """429, 5xx or a network failure: another attempt may succeed."""


class FatalError(ProviderError):
    """4xx other than 429: repeating the request cannot help."""


class DeadlineExceeded(ProviderError):
    """No attempt produced an answer before the overall deadline."""


class AttemptsExhausted(ProviderError):
    """Every allowed attempt failed with a retryable error."""
