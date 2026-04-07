import datetime

from more_itertools.recipes import sliding_window

CALL_COUNT_DICT_LABEL = "call_count"
TIMESTAMP_DICT_LABEL = "timestamp"

class RateLimiter:

    def __init__(self, max_calls : int, period: float, sliding_window_mode : bool = False):
        self._max_calls = max_calls
        self._period = period
        self._call_pool = {}
        self._sliding_window_mode = sliding_window_mode

    async def is_allowed(self, call_id : str) -> bool:
        if self._sliding_window_mode:
            return await self.sliding_window_limiter_check(call_id)
        else:
            return await self.default_limiter_check(call_id)

    async def sliding_window_limiter_check(self, call_id : str) -> bool:

        if call_id in self._call_pool:
            self._call_pool.get(call_id).append(datetime.datetime.now())
        else:
            self._call_pool.update({call_id: [datetime.datetime.now()]})

        window_count = 0

        for ts in self._call_pool.get(call_id):
            if datetime.datetime.now() < ts + datetime.timedelta(milliseconds=self._period):
                window_count += 1

        return window_count < self._max_calls


    async def default_limiter_check(self, call_id : str) -> bool:
        if call_id in self._call_pool:
            self._call_pool.get(call_id)[CALL_COUNT_DICT_LABEL] += 1
        else:
            self._call_pool.update({call_id: {CALL_COUNT_DICT_LABEL: 1, TIMESTAMP_DICT_LABEL: datetime.datetime.now()}})

        threshold_exceeded = self._call_pool.get(call_id)[CALL_COUNT_DICT_LABEL] < self._max_calls
        rate_expiration = self._call_pool.get(call_id)[TIMESTAMP_DICT_LABEL] + datetime.timedelta(
            milliseconds=self._period)

        if datetime.datetime.now() > rate_expiration:
            self._call_pool.get(call_id)[CALL_COUNT_DICT_LABEL] = 1
            return True

        return threshold_exceeded