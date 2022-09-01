
from collections import deque
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple, Type
from logging import getLogger
from dataclasses import dataclass
import time
from bpy.app import timers

log = getLogger(__name__)


@dataclass(frozen=True)
class Event:pass


EventHandler = Callable[[Event], None]
_handlers: Dict[Type[Event], List[EventHandler]] = {}
_queue: Deque[Event] = deque()
_throttled: Dict[Type[Event], Tuple[float, float, Event]] = {}
_processing_queue = False


def _throttle() -> Optional[float]:
    currtime = time.time()
    for key, (calltime, timespan, event) in tuple(_throttled.items()):
        if currtime - calltime > timespan:
            del _throttled[key]
            dispatch_event(event)
    if _throttled:
        return 0.1


def _process_event(event: Event) -> None:
    handlers = _handlers.get(event.__class__)
    if handlers:
        for handler in handlers:
            try:
                handler(event)
            except Exception as error:
                log.exception(str(error))


def _process_queue() -> None:
    global _processing_queue
    _processing_queue = True
    while len(_queue):
        _process_event(_queue.popleft())
    _processing_queue = False


def throttle_event(event: Event, timespan: Optional[float]=0.1) -> None:
    _throttled[event.__class__] = (time.time(), timespan, event)
    if not timers.is_registered(_throttle):
        timers.register(_throttle, first_interval=0.1)


def dispatch_event(event: Event) -> None:
    _queue.append(event)
    if not _processing_queue:
        _process_queue()


def event_handler(*types: Tuple[Type[Event]]) -> Callable[[EventHandler], EventHandler]:
    def add_event_handlers(handler: EventHandler) -> EventHandler:
        for type in types:
            _handlers.setdefault(type, []).append(handler)
        return handler
    return add_event_handlers
