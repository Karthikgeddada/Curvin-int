import time
from collections import deque

class RateLimiter:
    """Implements a Token Bucket/Sliding Window Rate Limiter for API calls."""
    def __init__(self, max_requests: int, time_window_seconds: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window_seconds
        self.requests = deque()

    def wait_if_needed(self):
        """Standard blocking wait to adhere to rate limits (iterative)."""
        while True:
            now = time.time()
            # Remove timestamps outside the sliding window
            while self.requests and self.requests[0] < now - self.time_window:
                self.requests.popleft()

            if len(self.requests) < self.max_requests:
                self.requests.append(time.time())
                return

            # Wait until the oldest request in the window expires, then re-check
            sleep_time = self.requests[0] + self.time_window - now
            if sleep_time > 0:
                time.sleep(sleep_time)

class KeyRotator:
    """Manages rotation, fallback, and rate limiting across multiple API keys."""
    def __init__(self, keys: list[str], requests_per_minute: int = 30):
        self.keys = keys
        self.current_index = 0
        self.limiters = [RateLimiter(requests_per_minute) for _ in keys]

    def get_next_key_info(self) -> tuple[str, RateLimiter]:
        """Provides the next available key and its associated rate limiter."""
        key = self.keys[self.current_index]
        limiter = self.limiters[self.current_index]
        
        # Advance for next call (automatic rotation)
        self.current_index = (self.current_index + 1) % len(self.keys)
        return key, limiter

    def mark_key_failed(self, failing_key: str):
        """Logic to handle key failures or persistent rate limits could go here."""
        # Simple implementation: move current index away from this key if caught elsewhere
        pass
