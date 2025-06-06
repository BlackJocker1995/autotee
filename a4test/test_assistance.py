import time
from functools import wraps
from loguru import logger


def timing_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        logger.debug(f"Execution time for {func.__name__}: {execution_time:.4f} seconds")
        return result

    return wrapper