import datetime
import time

from src.web_tools.rate_limiter import RateLimiter
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

@pytest.mark.asyncio
async def test_blocked_sliding():
    rl = RateLimiter(max_calls=3, period=1000, sliding_window_mode=True)
    rl._now = lambda: datetime.datetime(year=2021, month=1, day=1, hour=1, minute=1, second=1, microsecond=0)
    await rl.is_allowed("user1")
    rl._now = lambda: datetime.datetime(year=2021, month=1, day=1, hour=1, minute=1, second=1, microsecond=500)
    await rl.is_allowed("user1")
    await rl.is_allowed("user1")
    rl._now = lambda: datetime.datetime(year=2021, month=1, day=1, hour=1, minute=1, second=2, microsecond=0)
    result = await rl.is_allowed("user1")
    assert result == False


