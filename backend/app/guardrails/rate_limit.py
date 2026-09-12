"""
Phase 10 — Security Guardrails In-Memory Sliding Window Rate Limiter

Tracks request rates per client IP / identifier. Enforces HTTP 429 when the configured
request threshold is exceeded. Cleanly purges stale window entries to prevent memory leaks.
"""

import time
import logging
from typing import Dict, List, Tuple
from app.guardrails.policy import security_policy
from app.guardrails.schemas import GuardrailResult, GuardrailViolation, ViolationCodeEnum, SecuritySeverityEnum

logger = logging.getLogger(__name__)


class SlidingWindowRateLimiter:
    """
    In-Memory Sliding Window Rate Limiter.
    Suitable for single-instance demo & portfolio deployments.
    """

    def __init__(self, max_requests: int = None, window_seconds: int = None):
        self.max_requests = max_requests or security_policy.rate_limit_requests
        self.window_seconds = window_seconds or security_policy.rate_limit_window_seconds
        self._requests: Dict[str, List[float]] = {}

    def is_rate_limited(self, client_id: str) -> Tuple[bool, GuardrailResult]:
        """
        Evaluates whether client_id has exceeded rate limits in the current sliding window.
        Returns: (is_limited: bool, GuardrailResult)
        """
        now = time.time()
        window_start = now - self.window_seconds

        # Get or create timestamp list for client
        timestamps = self._requests.get(client_id, [])
        # Purge stale timestamps outside window
        valid_timestamps = [t for t in timestamps if t > window_start]
        self._requests[client_id] = valid_timestamps

        if len(valid_timestamps) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for client '{client_id}': {len(valid_timestamps)} requests in {self.window_seconds}s")
            violation = GuardrailViolation(
                code=ViolationCodeEnum.RATE_LIMIT_EXCEEDED,
                message=f"Rate limit of {self.max_requests} requests per {self.window_seconds}s exceeded.",
                severity=SecuritySeverityEnum.MEDIUM,
                details={"client_id": client_id, "current_count": len(valid_timestamps), "max_limit": self.max_requests}
            )
            return True, GuardrailResult(
                allowed=False,
                risk_level=SecuritySeverityEnum.MEDIUM,
                violations=[violation]
            )

        # Record new request timestamp
        valid_timestamps.append(now)
        self._requests[client_id] = valid_timestamps

        # Housekeeping: purge empty/stale clients if dict grows large (> 1000 clients)
        if len(self._requests) > 1000:
            self._cleanup_stale_clients(now)

        return False, GuardrailResult(allowed=True, risk_level=SecuritySeverityEnum.LOW)

    def _cleanup_stale_clients(self, now: float):
        window_start = now - self.window_seconds
        stale_keys = [
            cid for cid, ts_list in self._requests.items()
            if not ts_list or max(ts_list) <= window_start
        ]
        for key in stale_keys:
            del self._requests[key]


# Global Rate Limiter Instance
rate_limiter = SlidingWindowRateLimiter()
