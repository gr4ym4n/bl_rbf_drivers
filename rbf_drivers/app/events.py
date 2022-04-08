
from typing import Callable, Dict, List, Optional, Tuple, Type
from dataclasses import dataclass

@dataclass(frozen=True)
class Event:pass

_handlers: Dict[Type[Event], List[Callable[[Event], None]]] = {}

def dispatch_event(event: Event) -> None:
    handlers = _handlers.get(event.__class__)
    if handlers:
        for handler in handlers:
            handler(event)


def debounce_event(event: Event, delay: Optional[float]=0.0) -> None:
    pass


def event_handler(*types: Tuple[Type[Event]]) -> Callable[[Callable[[Event], None]], Callable[[Event], None]]:

    def add_event_handlers(handler: Callable[[Event], None]) -> Callable[[Event], None]:
        for type in types:
            _handlers.setdefault(type, []).append(handler)
        return handler

    return add_event_handlers
