
from typing import Any, Iterator, List, Optional, Union, TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, IntProperty
from .mixins import Collection, Searchable
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


class RBFDriverInputVariables(Searchable, Collection[RBFDriverInputVariable], PropertyGroup):

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

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}'

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".collection__internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'

    def new(self, name: Optional[str]="") -> RBFDriverInputVariable:
        input: 'RBFDriverInput' = owner_resolve(self, ".")

        if input.type not in {'USER_DEF', 'SHAPE_KEY'}:
            raise RuntimeError((f'{self.__class__.__name__}.new(): '
                                f'Variables are not mutable for inputs of type {input.type}'))

        if len(self) >= 16:
            raise RuntimeError((f'{self.__class__.__name__}.new(): '
                                f'Maximum number of variables per input exceeded'))

        variable: RBFDriverInputVariable = self.collection__internal__.add()
        variable["name"] = name

        dispatch_event(InputVariableNewEvent(variable))
        return variable

    def remove(self, variable: RBFDriverInputVariable) -> None:
        input: 'RBFDriverInput' = owner_resolve(self, ".")

        if input.type not in {'USER_DEF', 'SHAPE_KEY'}:
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

        if len(self) == 1:
            raise RuntimeError((f'{self.__class__.__name__}.remove(variable): '
                                f'Inputs must have at least one variable to remain operational'))

        dispatch_event(InputVariableDisposableEvent(variable))
        self.collection__internal__.remove(index)
