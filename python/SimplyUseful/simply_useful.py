# -*- coding: utf-8 -*-
import asyncio
import logging
import subprocess
import sys
import time
import tracemalloc
import types
from functools import lru_cache
from os import system
from typing import List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom Exceptions
class SimplyUsefulError(Exception):
    """Base exception for simply_useful module."""
    pass

class MissingDependencyError(SimplyUsefulError):
    """Raised when a required dependency is missing."""
    pass

class ExternallyManagedEnvironmentError(SimplyUsefulError):
    """Raised when attempting to install packages in an externally-managed environment."""
    pass

# Module Docstring
"""
simply_useful: A collection of reusable utility functions, classes, and decorators.

This module provides general-purpose helpers for:
- Dependency management
- Terminal operations
- Formatting utilities
- Decorators for logging, retries, caching, and memory measurement

Python Compatibility: Python 3.6+
Dependencies: None (except Python's standard library)

Usage:
    import simply_useful as SU

    # Example:
    SU.clear_term()
"""

__all__ = [
    "async_retry",
    "cache_results",
    "clear_term",
    "dependency_checker",
    "format_bytes",
    "format_number",
    "format_uptime",
    "handle_interrupt",
    "measure_memory",
    "retry",
    "timeit"
]

# Classes
class dependency_checker:
    """
    Checks for, and can install, missing modules required by the parent script.

    Usage:
        from simply_useful import dependency_checker

        REQUIRED = ['boto3', 'botocore']
        checker = dependency_checker(REQUIRED)

        # Check and install missing dependencies
        checker.check_dependencies()

        # Get a status report
        status = checker.get_status()
        print(f"Installed: {status['exist']}")
        print(f"Missing: {status['missing']}")

    Note:
        - This function will attempt to install missing dependencies using pip.
        - For environments managed externally (e.g., Debian-based systems), manual installation may be required.
    """
    def __init__(self, required: List[str]):
        self.required = required
        self.exist = []
        self.missing = []

    def check_dependencies(self):
        for mod in self.required:
            try:
                self.exist.append(__import__(mod))
            except ImportError:
                self.missing.append(mod)

        if not self.missing:
            logger.info("All required modules are installed.")
            return

        self._check_install()

        if self.missing:
            logger.error(
                f"The following dependencies could not be installed: {', '.join(self.missing)}"
            )

    def _install_required(self):
        for mod in self.missing:
            try:
                if self._is_externally_managed():
                    raise ExternallyManagedEnvironmentError(
                        "This environment is externally managed. "
                        "Please use a virtual environment or pipx to install Python packages."
                    )

                process = subprocess.run(
                    ["python3", "-m", "pip", "install", "--user", mod],
                    check=True,
                    capture_output=True,
                    text=True
                )
                logger.info(process.stdout)
                self.missing.remove(mod)
            except subprocess.CalledProcessError as e:
                if "externally-managed-environment" in e.stderr:
                    logger.error(e.stderr.strip())
                    break  # Stop further installation attempts
                else:
                    logger.error(f"Could not install {mod}: {e.stderr.strip()}")

    def _check_install(self):
        self._install_required()

    def get_status(self) -> dict:
        return {"exist": self.exist, "missing": self.missing}

    @staticmethod
    def _is_externally_managed() -> bool:
        try:
            import sysconfig
            return sysconfig.get_config_var("EXTERNALLY_MANAGED") == "1"
        except ImportError:
            return False

# Functions
def clear_term():
    """
    Clears the terminal screen.

    Usage:
        import simply_useful
        simply_useful.clear_term()

    Note:
        This function uses the `clear` command, which works on Unix-based systems.
        On Windows, this may not behave as expected unless `clear` is available in the environment.
    """
    system('clear')

def format_bytes(bytes: float) -> str:
    """
    Converts bytes into a human-readable string.

    Parameters:
        bytes (float): The number of bytes to format.

    Returns:
        str: A human-readable string (e.g., "1.00 KB").

    Usage:
        import simply_useful
        result = simply_useful.format_bytes(1024)

    Edge Cases:
        - Returns "0.00 B" for bytes <= 0.
    """
    if bytes <= 0:
        return "0.00 B"
    sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    index = 0
    while bytes >= 1024 and index < len(sizes) - 1:
        bytes /= 1024
        index += 1
    return f"{bytes:.2f} {sizes[index]}"

def format_uptime(uptime: int, concise: bool = False) -> str:
    """
    Formats uptime in seconds into a readable string.

    Parameters:
        uptime (int): The uptime in seconds.
        concise (bool): Whether to use a concise format.

    Returns:
        str: A formatted uptime string.

    Usage:
        import simply_useful
        result = simply_useful.format_uptime(123456)
    """
    days = uptime // (24 * 3600)
    hours = (uptime % (24 * 3600)) // 3600
    minutes = (uptime % 3600) // 60
    seconds = uptime % 60
    if concise:
        return f"{days}d {hours}h {minutes}m {seconds}s"
    return f"{days} days, {hours} hours, {minutes} minutes, {seconds} seconds"

def handle_interrupt(signum, frame, action):
    """
    Handles interrupt signals (e.g., Ctrl+C) and performs an action before exiting.

    Parameters:
        signum (int): The signal number.
        frame: The current stack frame (unused).
        action (callable or str): The action to perform.

    Usage:
        import signal
        from simply_useful import handle_interrupt

        signal.signal(signal.SIGINT, lambda s, f: handle_interrupt(s, f, my_exit_function()))
    """
    logger.info(f"Received interrupt signal {signum}")
    if isinstance(action, types.FunctionType):
        action()
    else:
        eval(action)
    sys.exit(0)

def format_number(number: float) -> str:
    """
    Formats large numbers into a human-readable string.

    Parameters:
        number (float): The number to format.

    Returns:
        str: A human-readable string (e.g., "1.0K").

    Usage:
        import simply_useful
        result = simply_useful.format_number(1000000)
    """
    for unit in ['', 'K', 'M', 'B', 'T']:
        if abs(number) < 1000:
            return f"{number:.1f}{unit}"
        number /= 1000
    return f"{number:.1f}P"

# Decorators
def timeit(func):
    """
    Logs the execution time of the decorated function.

    Note:
        - Uses the `logging` module to log the execution time.
        - Ensure that the logging level is set to `INFO` or lower for the logs to appear.

    Usage:
        @timeit
        def process_data():
            ...
    """
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        logger.info(f"{func.__name__} took {end - start:.2f} seconds")
        return result
    return wrapper

def retry(max_retries: int = 3, backoff: float = 1.0):
    """
    Retries a function up to `max_retries` times with exponential backoff.

    Parameters:
        max_retries (int): Maximum number of retries before giving up.
        backoff (float): Multiplier for exponential delay between retries.

    Usage:
        @retry(max_retries=5, backoff=2.0)
        def fetch_data():
            # Simulate a transient error
            if random.random() < 0.8:
                raise ValueError("Temporary failure")
            return "Data retrieved successfully"

        try:
            result = fetch_data()
            print(result)
        except ValueError:
            print("Failed after multiple attempts")
    """
    if max_retries <= 0 or backoff <= 0:
        raise ValueError("max_retries and backoff must be greater than 0")

    def decorator(func):
        def wrapper(*args, **kwargs):
            attempts = 0
            delay = backoff
            while attempts < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    logger.warning(f"Attempt {attempts}/{max_retries} failed. Error: {e}")
                    if attempts < max_retries:
                        time.sleep(delay)
                        delay *= backoff
                    else:
                        raise
        return wrapper
    return decorator

def cache_results(maxsize: int = 128):
    """
    Caches the results of the function to avoid recomputation.

    Parameters:
        maxsize (int): The maximum number of results to cache.

    Note:
        - This decorator is not thread-safe. For concurrent use, consider using `functools.cache` or other thread-safe mechanisms.

    Usage:
        @cache_results(maxsize=256)
        def expensive_computation():
            ...
    """
    def decorator(func):
        return lru_cache(maxsize=maxsize)(func)
    return decorator

def measure_memory(func):
    """
    Measures the peak memory usage during function execution.

    Usage:
        @measure_memory
        def process_data():
            ...
    """
    def wrapper(*args, **kwargs):
        tracemalloc.start()
        result = func(*args, **kwargs)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        logger.info(f"{func.__name__} used {peak / 1024:.2f} KB of memory at peak")
        return result
    return wrapper

def async_retry(max_retries: int = 3, backoff: float = 1.0):
    """
    Retries an async function up to `max_retries` times with exponential backoff.

    Parameters:
        max_retries (int): Maximum number of retries before giving up.
        backoff (float): Multiplier for exponential delay between retries.

    Usage:
        @async_retry(max_retries=5, backoff=2.0)
        async def fetch_data():
            ...

    Note:
        - This decorator is designed for asynchronous functions.
        - Ensure the function is properly awaited.
    """
    if max_retries <= 0 or backoff <= 0:
        raise ValueError("max_retries and backoff must be greater than 0")

    def decorator(func):
        async def wrapper(*args, **kwargs):
            attempts = 0
            delay = backoff
            while attempts < max_retries:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    logger.warning(f"Attempt {attempts}/{max_retries} failed. Error: {e}")
                    if attempts < max_retries:
                        await asyncio.sleep(delay)
                        delay *= backoff
                    else:
                        raise
        return wrapper
    return decorator

