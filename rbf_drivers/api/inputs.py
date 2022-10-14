
from typing import Optional
from .mixins import Collection, Reorderable, Searchable
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, IntProperty
from ..app.events import dataclass, dispatch_event, Event
from .input import INPUT_TYPE_TABLE, Input, INPUT_TYPE_INDEX


@dataclass(frozen=True)
class InputNewEvent(Event):
    input: Input


@dataclass(frozen=True)
class InputDisposableEvent(Event):
    input: Input


@dataclass(frozen=True)
class InputRemovedEvent(Event):
    inputs: 'Inputs'
    index: int


@dataclass(frozen=True)
class InputMoveEvent(Event):
    input: Input
    from_index: int
    to_index: int


class Inputs(Reorderable, Searchable[Input], Collection[Input], PropertyGroup):

    active_index: IntProperty(
        name="Input",
        description="An RBF driver input",
        min=0,
        default=0,
        options=set()
        )

    @property
    def active(self) -> Optional[Input]:
        index = self.active_index
        return self[index] if index < len(self) else None

    internal__: CollectionProperty(
        type=Input,
        options={'HIDDEN'}
        )

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'

    def move(self, from_index: int, to_index: int) -> None:
        super().move(from_index, to_index)
        dispatch_event(InputMoveEvent(self, from_index, to_index))

    def new(self, type: str) -> Input:

        if not isinstance(type, str):
            raise TypeError((f'{self.__class__.__name__}.new(type): '
                             f'Expected type to be str, not {type.__class__.__name__}'))

        if type not in INPUT_TYPE_INDEX:
            raise ValueError((f'{self.__class__.__name__}.new(type): '
                              f'type {type} not found in {", ".join(INPUT_TYPE_INDEX)}'))

        input: Input = self.internal__.add()
        input["type"] = INPUT_TYPE_TABLE[type]

        dispatch_event(InputNewEvent(input))

        self.active_index = len(self) - 1
        return input

    def remove(self, input: Input) -> None:

        if not isinstance(input, Input):
            raise TypeError((f'{self.__class__.__name__}.remove(input): '
                             f'Expected input to be {Input.__name__}, '
                             f'not {input.__class__.__name__}'))

        index = next((index for index, item in enumerate(self) if item == input), -1)
        if index == -1:
            raise ValueError((f'{self.__class__.__name__}.remove(input): '
                             f'Input {input} not found in collection {self}'))

        dispatch_event(InputDisposableEvent(input))

        self.internal__.remove(index)
        self.active_index = min(self.active_index, len(self)-1)

        dispatch_event(InputRemovedEvent(self, index))