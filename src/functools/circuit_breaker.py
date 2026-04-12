import enum
from typing import Callable
from uuid import uuid4
from datetime import datetime, timedelta

class NotValidWatcher(Exception):
    def __init__(self, message : str):
        self.message = message

class CircuitOpenException(Exception):
    def __init__(self, message : str):
        self.message = message

class CircuitStatus(str, enum.Enum):
    STATUS_OK = 'OK'
    STATUS_KO = 'KO'

class CircuitBreaker:

    def __init__(self):
        self._watchers = []

    def register_watcher(self, watcher : Watcher):
        self._watchers.append(watcher)

    def unregister(self, watcher):
        self._watchers.remove(watcher)

    def wire_circuit(self, func : Callable, watcher_name : str = None):
        local_watcher: Watcher | None = None
        if watcher_name is None:
            local_watcher = Watcher(str(uuid4()))
            self._watchers.append(local_watcher)
        elif watcher_name not in self._watchers:
            raise NotValidWatcher(f"Cannot find watcher name: {watcher_name}")
        else:
            for el in self._watchers:
                if el.name == watcher_name:
                    local_watcher = el
                    break
        if local_watcher is None:
            raise NotValidWatcher(f"I'm not supposed to be here!")

        def wrapper(*args, **kwargs):
            if local_watcher.status == CircuitStatus.STATUS_OK:
                try:
                    result = func(*args, **kwargs)
                except Exception as e:
                    local_watcher.add_failure(e)
                    raise
                finally:
                    local_watcher.refresh_status()
                return result
            else:
                raise CircuitOpenException(f"Sorry, the circuit is now open. Try again in {local_watcher.get_numeric_cooldown()} seconds.")
        return wrapper

class Watcher:
    def __init__(self, name : str, max_attempts : int = 10, sec_cooldown : float = 120.0):
        self._status = CircuitStatus.STATUS_OK
        self._changedAt : datetime = datetime.now()
        self._cooldown : timedelta = timedelta(seconds=sec_cooldown)
        self._max_attempts = max_attempts
        self._name = name
        self._failure_dict = {}

    @property
    def status(self):
        return self._status

    @property
    def name(self):
        return self._name

    def refresh_status(self):
        if self._status == CircuitStatus.STATUS_KO:
            now = datetime.now()
            if now - self._changedAt > self._cooldown:
                self._failure_dict = {}
                self._status = CircuitStatus.STATUS_OK
        elif self._status == CircuitStatus.STATUS_OK:
            if self._failure_dict.get("attempts",0) >= self._max_attempts:
                self.set_status(CircuitStatus.STATUS_KO)
        return self.status

    def set_status(self, status : CircuitStatus):
        self._changedAt = datetime.now()
        self._status = status

    def add_failure(self,e : Exception):
        if not self._failure_dict:
            self._failure_dict = {"attempts" : 1,"stacktraces" : [str(e)]}
        elif self._failure_dict is not None:
            self._failure_dict["attempts"] +=1
            self._failure_dict["stacktraces"].append(str(e))

    def get_numeric_cooldown(self):
        return self._cooldown.total_seconds()

    def __eq__(self, other):
        if isinstance(other, Watcher):
            return self._name == other.name
        elif isinstance(other, str):
            return self._name == other
        else:
            return False