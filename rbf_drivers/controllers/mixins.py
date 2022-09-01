
from sys import modules
from logging import getLogger
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Tuple, Union
from uuid import uuid4
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, PointerProperty, StringProperty

log = getLogger(__name__)


class Tags(PropertyGroup):

    internal__: CollectionProperty(
        type=PropertyGroup,
        options={'HIDDEN'}
        )

    def __init__(self, tags: Set[str]) -> None:
        for tag in tags:
            self.internal__.add().name = tag

    def __contains__(self, tag: str) -> bool:
        return tag in self.internal__

    def __iter__(self) -> Iterator[str]:
        return self.internal__.keys()

    def __len__(self) -> int:
        return len(self.internal__)

    def add(self, tag: str) -> None:
        if tag not in self:
            self.internal__.add().name = tag

    def remove(self, tag: str) -> None:
        index = self.internal__.find(tag)
        if index >= 0:
            self.internal__.remove(index)


class Observer(PropertyGroup):

    module: StringProperty(
        name="Module",
        description="The event callback's module name (read-only)",
        get=lambda self: self.get("module", ""),
        options={'HIDDEN'}
        )

    name: StringProperty(
        name="Name",
        description="The event callback's name (read-only)",
        get=lambda self: self.get("name", ""),
        options={'HIDDEN'}
        )

    tags: PointerProperty(
        name="Tags",
        description="Event tags",
        type=Tags,
        options=set()
        )

    def __init__(self, callback: Callable, tags: Optional[Set[str]]) -> None:
        self["module"] = callback.__module__
        self["name"] = callback.__name__
        if tags:
            self.tags.__init__(tags)

    def __eq__(self, callback: Callable) -> bool:
        return self.name == callback.__name__ and self.module == callback.__module__

    def __call__(self, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:
        module = modules.get(self.module)
        if module:
            callback = module.get(self.name)
            if callable(callback):
                try:
                    callback(*args, **kwargs)
                except Exception as error:
                    log.exception(error)


class Observers(PropertyGroup):

    internal__: CollectionProperty(
        type=Observer,
        options={'HIDDEN'}
        )

    name: StringProperty(
        name="Name",
        get=lambda self: super().get("name", ""),
        set=lambda self: log.error(f'{type(self).__name__}.name is read-only'),
        options=set()
        )

    def __init__(self, name: str) -> None:
        self["name"] = name

    def __contains__(self, callback: Callable) -> bool:
        return any(observer == callback for observer in self.internal__)

    def __iter__(self) -> Iterator[Observer]:
        return iter(self.internal__)

    def __len__(self) -> int:
        return len(self.internal__)

    def __getitem__(self, key: Union[str, int, slice]) -> Union[Observer, List[Observer]]:
        return self.internal__[key]

    def add(self, callback: Callable, tags: Optional[Set[str]]) -> None:
        if callback not in self:
            self.internal__.add().__init__(callback, tags)

    def remove(self, callback: Callable) -> None:
        index = next((i for i, x in enumerate(self) if x == callback), -1)
        if index != -1:
            self.internal__.remove(index)

    def get(self, name: str) -> Optional[Observer]:
        return self.internal__.get(name)

    def keys(self) -> Iterator[str]:
        return self.internal__.keys()

    def items(self) -> Iterator[Tuple[str, Observer]]:
        return self.internal__.items()


class Observable:

    observers__: CollectionProperty(
        type=Observers,
        options={'HIDDEN'}
        )

    def add_observer(self, name: str, callback: Callable, tags: Optional[Set[str]]=None) -> None:
        observers = self.observers__.get(name)
        if observers is None:
            observers = self.observers__.add()
            observers.__init__(name)
        observers.add(callback, tags)

    def remove_observer(self, name_or_tag: str, callback: Optional[Callable]=None) -> None:
        if callback:
            observers = self.observers__.get(name_or_tag)
            if observers:
                observers.remove(callback)
        else:
            for observers in self.observers__:
                for index, observer in reversed(list(enumerate(observers))):
                    if name_or_tag in observer.tags:
                        observers.internal__.remove(index)

    def notify_observers(self, name: str, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> None:
        observers = self.observers__.get(name)
        if observers:
            for observer in observers:
                observer(self, *args, **kwargs)


def identifier_get(struct: 'Identifiable') -> str:
    if struct.is_property_set("identifier"):
        value = struct["identifier"]
    else:
        value = f'rbf_{uuid4().hex}'
        struct["identifier"] = value
    return value


class Identifiable:

    identifier: StringProperty(
        name="Identifier",
        get=identifier_get,
        options={'HIDDEN'}
        )
