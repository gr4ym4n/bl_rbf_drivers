
from bpy.types import PropertyGroup, UILayout
from bpy.props import CollectionProperty
from .mixins import LayerCollection
from .input import INPUT_TYPE_INDEX, RBFDriverInput
from ..app.events import dataclass, dispatch_event, Event


@dataclass(frozen=True)
class InputNewEvent(Event):
    input: RBFDriverInput


@dataclass(frozen=True)
class InputDisposableEvent(Event):
    input: RBFDriverInput


@dataclass(frozen=True)
class InputRemovedEvent(Event):
    inputs: 'RBFDriverInputs'
    index: int


@dataclass(frozen=True)
class InputMoveEvent(Event):
    input: RBFDriverInput
    from_index: int
    to_index: int


class RBFDriverInputs(LayerCollection[RBFDriverInput], PropertyGroup):

    collection__internal__: CollectionProperty(
        type=RBFDriverInput,
        options={'HIDDEN'}
        )

    def index(self, input: RBFDriverInput) -> int:
        if not isinstance(input, RBFDriverInput):
            raise TypeError((f'{self.__class__.__name__}.index(input): '
                             f'Expected input to be RBFDriverInput, not {input.__class__.__name__}'))
        return super().index(input)

    def move(self, from_index: int, to_index: int) -> None:
        if super().move(from_index, to_index):
            dispatch_event(InputMoveEvent(self[to_index], from_index, to_index))

    def new(self, type: str) -> RBFDriverInput:

        if not isinstance(type, str):
            raise TypeError((f'{self.__class__.__name__}.new(type): '
                             f'Expected type to be str, not {type.__class__.__name__}'))

        if type not in INPUT_TYPE_INDEX:
            raise ValueError((f'{self.__class__.__name__}.new(type): '
                              f'type {type} not found in {", ".join(INPUT_TYPE_INDEX)}'))

        input: RBFDriverInput = self.collection__internal__.add()
        input["type"] = INPUT_TYPE_INDEX[type]
        input.name = UILayout.enum_item_name(input, "type", type)

        dispatch_event(InputNewEvent(input))

        self.active_index = len(self) - 1
        return input

    def remove(self, input: RBFDriverInput) -> None:

        if not isinstance(input, RBFDriverInput):
            raise TypeError((f'{self.__class__.__name__}.remove(input): '
                             f'Expected input to be {RBFDriverInput.__name__}, '
                             f'not {input.__class__.__name__}'))

        index = next((index for item, index in enumerate(self) if item == input), -1)

        if index == -1:
            raise ValueError((f'{self.__class__.__name__}.remove(input): '
                             f'Input {input} not found in collection {self}'))

        dispatch_event(InputDisposableEvent(input))
        self.collection__internal__.remove(index)
        dispatch_event(InputRemovedEvent(input, index))
