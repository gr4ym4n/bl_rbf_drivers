
from typing import Any, Iterable, List, Optional, Protocol, Sequence, TypeVar, Union

class IPropertyGroup:
    name: str
    def __getitem__(self, name: str) -> Any: pass
    def __setitem__(self, name: str, value: Any): pass
    def is_property_set(self, name: str) -> bool: pass
    def unset_property(self, name: str) -> None: pass


TPropertyGroup = TypeVar('TPropertyGroup', bound=IPropertyGroup)


class ICollection(Protocol[TPropertyGroup]):
    def __len__(self) -> int: pass
    def __iter__(self) -> Iterable[TPropertyGroup]: pass
    def __getitem__(self, key: Union[int, str, slice]) -> Union[TPropertyGroup, List[TPropertyGroup]]: pass
    def add(self) -> TPropertyGroup: pass
    def find(self, name: str) -> int: pass
    def clear(self) -> None: pass
    def foreach_get(self, key: str, data: Sequence[Any]) -> None: pass
    def foreach_set(self, key: str, data: Sequence[Any]) -> None: pass
    def get(self, name: str) -> Optional[TPropertyGroup]: pass
    def keys(self) -> Iterable[str]: pass
    def items(self) -> Iterable[TPropertyGroup]: pass
    def move(self, from_index: int, to_index: int) -> None: pass
    def remove(self, index: int) -> None: pass
    def values(self) -> Iterable[TPropertyGroup]: pass
