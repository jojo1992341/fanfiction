"""Service for handling translation retries and rate limiting."""
import logging
import time
from typing import Optional, Callable, TypeVar, Any
from functools import wraps
import random

logger = logging.getLogger(__name__)

T = TypeVar('T')

class TranslationRetryHandler:
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 10.0,
        backoff_factor: float = 2.0
    ):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self._request_times: list[float] = []
        self._min_request_interval = 1.0  # Minimum time between requests

    def with_retry(self, func: Callable[..., T]) -> Callable[..., Optional[T]]:
        """Decorator for retrying translation operations with exponential backoff."""
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Optional[T]:
            retry_count = 0
            last_error = None

            while retry_count <= self.max_retries:
                try:
                    self._apply_rate_limit()
                    result = func(*args, **kwargs)
                    self._record_request_time()
                    return result

                except Exception as e:
                    last_error = e
                    retry_count += 1
                    if retry_count <= self.max_retries:
                        delay = self._calculate_delay(retry_count)
                        logger.warning(
                            f"Translation attempt {retry_count} failed: {str(e)}. "
                            f"Retrying in {delay:.2f} seconds..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"Translation failed after {self.max_retries} retries: {str(e)}"
                        )

            return None

        return wrapper

    def _calculate_delay(self, retry_count: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        delay = min(
            self.base_delay * (self.backoff_factor ** (retry_count - 1)),
            self.max_delay
        )
        # Add random jitter (±25%)
        jitter = delay * 0.25
        return delay + random.uniform(-jitter, jitter)

    def _record_request_time(self) -> None:
        """Record the time of a successful request."""
        current_time = time.time()
        self._request_times.append(current_time)
        # Keep only the last minute of requests
        cutoff_time = current_time - 60
        self._request_times = [t for t in self._request_times if t > cutoff_time]

    def _apply_rate_limit(self) -> None:
        """Apply rate limiting if necessary."""
        if not self._request_times:
            return

        current_time = time.time()
        last_request_time = self._request_times[-1]
        time_since_last_request = current_time - last_request_time

        if time_since_last_request < self._min_request_interval:
            sleep_time = self._min_request_interval - time_since_last_request
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        # Check for too many requests in the last minute
        requests_last_minute = len(self._request_times)
        if requests_last_minute >= 60:  # More than 60 requests per minute
            sleep_time = random.uniform(1.0, 3.0)  # Random delay between 1-3 seconds
            logger.warning(f"Too many requests, backing off for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
