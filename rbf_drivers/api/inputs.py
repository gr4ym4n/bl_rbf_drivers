
from typing import Any, Iterator, List, Optional, Union
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, IntProperty
from .input import RBFDriverInput

class RBFDriverInputs(PropertyGroup):

    active_index: IntProperty(
        name="Shape Key",
        min=0,
        default=0,
        options=set()
        )

    @property
    def active(self) -> Optional[RBFDriverInput]:
        index = self.active_index
        return self[index] if index < len(self) else None

    collection__internal__: CollectionProperty(
        type=RBFDriverInput,
        options={'HIDDEN'}
        )

    def __len__(self) -> int:
        return len(self.collection__internal__)

    def __iter__(self) -> Iterator[RBFDriverInput]:
        return iter(self.collection__internal__)

    def __getitem__(self, key: Union[int, slice]) -> Union[RBFDriverInput, List[RBFDriverInput]]:
        return self.collection__internal__[key]

    def __contains__(self, value: Any) -> bool:
        return any([item == value for item in self])

    def find(self, name: str) -> int:
        return next((index for index, input_ in enumerate(self) if input_.name == name), -1)

    def get(self, name: str, default: object) -> Any:
        return next((item for item in self if item.name == name), default)

    def search(self, identifier: str) -> Optional[RBFDriverInput]:
        return next((input_ for input_ in self if input_.identifier == identifier), None)
