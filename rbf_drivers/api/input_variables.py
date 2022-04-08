
from typing import Any, Iterator, List, Optional, Union, TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, IntProperty
from .input_variable import RBFDriverInputVariable
from ..app.events import dataclass, dispatch_event, Event
from ..app.utils import owner_resolve
if TYPE_CHECKING:
    from .input import RBFDriverInput


@dataclass(frozen=True)
class InputVariableNewEvent(Event):
    variable: RBFDriverInputVariable


@dataclass(frozen=True)
class InputVariableDisposableEvent(Event):
    variable: RBFDriverInputVariable


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

    def index(self, variable: RBFDriverInputVariable) -> int:
        return next(index for index, item in enumerate(self) if variable == item)

    def new(self) -> RBFDriverInputVariable:
        input: 'RBFDriverInput' = owner_resolve(self, ".")

        if input.type != 'NONE':
            raise RuntimeError((f'{self.__class__.__name__}.new(): '
                                f'Variables are not mutable for inputs of type {input.type}'))

        variable: RBFDriverInputVariable = self.collection__internal__.add()
        dispatch_event(InputVariableNewEvent(variable))
        return variable

    def remove(self, variable: RBFDriverInputVariable) -> None:
        input: 'RBFDriverInput' = owner_resolve(self, ".")

        if input.type != 'NONE':
            raise RuntimeError((f'{self.__class__.__name__}.remove(variable): '
                                f'Variables are not mutable for inputs of type {input.type}'))

        if not isinstance(variable, RBFDriverInputVariable):
            raise TypeError((f'{self.__class__.__name__}.remove(variable): '
                             f'Expected variable to be {RBFDriverInputVariable.__class__.__name__}, '
                             f'not {variable.__class__.__name__}'))

        index = next((index for index, item in enumerate(self) if item == variable), -1)

        if index == -1:
            raise ValueError((f'{self.__class__.__name__}.remove(variable): '
                              f'{variable} is not a member of this collection'))

        dispatch_event(InputVariableDisposableEvent(variable))
        self.collection__internal__.remove(index)

    def search(self, identifier: str) -> Optional[RBFDriverInputVariable]:
        return next((variable for variable in self if variable.identifier == identifier), None)
