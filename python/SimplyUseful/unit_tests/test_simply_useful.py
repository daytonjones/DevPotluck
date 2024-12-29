#!/usr/bin/env python3
import sys
import os
import pytest
import signal
import time
import logging

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simply_useful import (
    async_retry,
    clear_term,
    format_uptime,
    handle_interrupt,
    format_number,
    timeit,
    cache_results,
    measure_memory,
    retry,
)

# Test `clear_term`
def test_clear_term(capsys):
    clear_term()
    captured = capsys.readouterr()
    assert captured.out == ""


# Test `format_uptime`
@pytest.mark.parametrize(
    "uptime, concise, expected",
    [
        (123456, False, "1 days, 10 hours, 17 minutes, 36 seconds"),
        (123456, True, "1d 10h 17m 36s"),
        (3600, False, "0 days, 1 hours, 0 minutes, 0 seconds"),
    ],
)
def test_format_uptime(uptime, concise, expected):
    assert format_uptime(uptime, concise) == expected


# Test `handle_interrupt`
def test_handle_interrupt():
    def dummy_action():
        print("Action performed")

    with pytest.raises(SystemExit):
        signal.signal(
            signal.SIGINT,
            lambda signum, frame: handle_interrupt(signum, frame, dummy_action),
        )
        os.kill(os.getpid(), signal.SIGINT)


# Test `format_number`
@pytest.mark.parametrize(
    "number, expected",
    [
        (1000, "1.0K"),
        (1000000, "1.0M"),
        (123, "123.0"),
        (1000000000, "1.0B"),
    ],
)
def test_format_number(number, expected):
    assert format_number(number) == expected


# Test `timeit`
def test_timeit(caplog):
    @timeit
    def dummy_function():
        time.sleep(0.1)
        return "done"

    with caplog.at_level(logging.INFO):
        result = dummy_function()
        assert result == "done"
        assert "dummy_function took" in caplog.text


# Test `cache_results`
def test_cache_results():
    calls = {"count": 0}

    @cache_results(maxsize=2)
    def expensive_function(x):
        calls["count"] += 1
        return x * x

    assert expensive_function(2) == 4
    assert expensive_function(2) == 4
    assert calls["count"] == 1  # Cached result used


# Test `measure_memory`
def test_measure_memory(caplog):
    @measure_memory
    def memory_function():
        x = [0] * 1000000  # Allocate a large list
        return len(x)

    with caplog.at_level(logging.INFO):
        result = memory_function()
        assert result == 1000000
        assert "memory_function used" in caplog.text


# Test `async_retry`
@pytest.mark.asyncio
async def test_async_retry_success():
    @async_retry(max_retries=3, backoff=1)
    async def async_function():
        return "success"

    result = await async_function()
    assert result == "success"


@pytest.mark.asyncio
async def test_async_retry_failure():
    @async_retry(max_retries=3, backoff=1)
    async def async_function():
        raise ValueError("Failure")

    with pytest.raises(ValueError, match="Failure"):
        await async_function()

