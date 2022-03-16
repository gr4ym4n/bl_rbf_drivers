
from typing import Any, Iterator, List, Optional, Union
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, IntProperty
from .input_variable import RBFDriverInputVariable

class RBFDriverInputVariables(PropertyGroup):

    collection__internal__: CollectionProperty(
        type=RBFDriverInputVariable,
        options={'HIDDEN'}
        )

    active_index: IntProperty(
        name="Shape Key",
        min=0,
        default=0,
        options=set()
        )

    @property
    def active(self) -> Optional[RBFDriverInputVariable]:
        index = self.active_index
        return self[index] if index < len(self) else None

    def __len__(self) -> int:
        return len(self.collection__internal__)

    def __iter__(self) -> Iterator[RBFDriverInputVariable]:
        return iter(self.collection__internal__)

    def __getitem__(self, key: Union[str, int, slice]) -> Union[RBFDriverInputVariable, List[RBFDriverInputVariable]]:

        if isinstance(key, str):
            variable = next((var for var in self if var.name == key), None)
            if variable is None:
                raise KeyError(f'{self.__class__.__name__}[key]: "{key}" not found.')
            return variable

        if isinstance(key, int):
            if 0 > key >= len(self):
                raise IndexError((f'{self.__class__.__name__}[key]: '
                                  f'Index {key} out of range 0-{len(self)}.'))

            return self.collection__internal__[key]

        if isinstance(key, slice):
            return self.collection__internal__[key]

        raise TypeError((f'{self.__class__.__name__}[key]: '
                         f'Expected key to be str, int or slice, not {key.__class__.__name__}.'))

    def find(self, name: str) -> int:
        return next((index for index, variable in enumerate(self) if variable.name == name), -1)

    def get(self, name: str, default: Optional[object]=None) -> Any:
        return self.collection__internal__.get(name, default)

    def search(self, identifier: str) -> Optional[RBFDriverInputVariable]:
        return next((variable for variable in self if variable.identifier == identifier), None)
