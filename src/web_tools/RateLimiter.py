import datetime

CALL_COUNT_DICT_LABEL = "call_count"
TIMESTAMP_DICT_LABEL = "timestamp"

class RateLimiter:

    def __init__(self, max_calls : int, period: float):
        self._max_calls = max_calls
        self._period = period
        self._call_pool = {}

    async def is_allowed(self, call_id : str) -> bool:
        if call_id in self._call_pool:
            self._call_pool[call_id][CALL_COUNT_DICT_LABEL] +=1
        else:
            self._call_pool.update({call_id : {CALL_COUNT_DICT_LABEL:1, TIMESTAMP_DICT_LABEL:datetime.datetime.now()}})

        threshold_exceeded = self._call_pool[call_id][CALL_COUNT_DICT_LABEL] < self._max_calls
        rate_expiration = self._call_pool[call_id][TIMESTAMP_DICT_LABEL] + datetime.timedelta(milliseconds=self._period)

        if datetime.datetime.now() > rate_expiration:
            self._call_pool[call_id][CALL_COUNT_DICT_LABEL] = 1
            return True

        return threshold_exceeded
