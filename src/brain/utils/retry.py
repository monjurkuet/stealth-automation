import logging
import asyncio
from typing import Callable, Any

logger = logging.getLogger(__name__)


async def with_retry(
    coro: Callable[[], Any],
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    exceptions: tuple = (Exception,),
) -> Any:
    """
    Execute coroutine with exponential backoff retry.

    Args:
        coro: Coroutine to execute
        max_retries: Maximum retry attempts
        backoff_factor: Base delay multiplier
        exceptions: Exception types to catch and retry

    Returns:
        Result from coroutine
    """
    last_exception = Exception("Unknown error")

    for attempt in range(max_retries):
        try:
            return await coro()
        except exceptions as e:
            last_exception = e
            if attempt == max_retries - 1:
                logger.error(f"Retry failed after {max_retries} attempts: {e}")
                raise last_exception

            delay = backoff_factor * (2**attempt)
            logger.warning(f"Retry {attempt + 1}/{max_retries} after {delay}s: {e}")
            await asyncio.sleep(delay)

    raise last_exception
