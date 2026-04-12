import datetime
import time

from src.web_tools.RateLimiter import RateLimiter
import pytest

@pytest.mark.asyncio
async def test_allowed():
    rl = RateLimiter(max_calls=3, period=1000)
    assert await rl.is_allowed("user1") == True

@pytest.mark.asyncio
async def test_blocked():
    rl = RateLimiter(max_calls=3, period=100000)
    await rl.is_allowed("user1")
    await rl.is_allowed("user1")
    await rl.is_allowed("user1")
    result = await rl.is_allowed("user1")
    assert result == False


