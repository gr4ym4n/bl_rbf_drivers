
from bpy.types import PropertyGroup, UILayout
from bpy.props import BoolProperty, CollectionProperty
from .mixins import LayerCollection
from .output import RBFDriverOutput, output_mute, OUTPUT_TYPE_INDEX
from ..app.events import dataclass, dispatch_event, Event


@dataclass(frozen=True)
class OutputNewEvent(Event):
    output: RBFDriverOutput


@dataclass(frozen=True)
class OutputDisposableEvent(Event):
    output: RBFDriverOutput


@dataclass(frozen=True)
class OutputRemovedEvent(Event):
    outputs: 'RBFDriverOutputs'
    index: int


@dataclass(frozen=True)
class OutputMoveEvent(Event):
    output: RBFDriverOutput
    from_index: int
    to_index: int


def outputs_mute(outputs: 'RBFDriverOutputs') -> bool:
    return any(map(output_mute, outputs))


def outputs_mute_set(outputs: 'RBFDriverOutputs', value: bool) -> None:
    for output in outputs:
        output.mute = value


class RBFDriverOutputs(LayerCollection[RBFDriverOutput], PropertyGroup):

    collection__internal__: CollectionProperty(
        type=RBFDriverOutput,
        options={'HIDDEN'}
        )

    mute: BoolProperty(
        name="Mute",
        description="Un(mute) output drivers",
        get=outputs_mute,
        set=outputs_mute_set,
        options=set()
        )

    def index(self, output: RBFDriverOutput) -> int:
        if not isinstance(output, RBFDriverOutput):
            raise TypeError((f'{self.__class__.__name__}.index(output): '
                             f'Expected input to be RBFDriverOutput, not {output.__class__.__name__}'))
        return super().index(output)

    def move(self, from_index: int, to_index: int) -> None:
        if super.move(from_index, to_index):
            dispatch_event(OutputMoveEvent(self[to_index], from_index, to_index))

    def new(self, type: str) -> RBFDriverOutput:

        if not isinstance(type, str):
            raise TypeError((f'{self.__class__.__name__}.new(type): '
                             f'Expected type to be str, not {type.__class__.__name__}'))

        if type not in OUTPUT_TYPE_INDEX:
            raise ValueError((f'{self.__class__.__name__}.new(type): '
                              f'type {type} not found in {", ".join(OUTPUT_TYPE_INDEX)}'))

        output: RBFDriverOutput = self.collection__internal__.add()
        output["type"] = OUTPUT_TYPE_INDEX[type]
        output.name = UILayout.enum_item_name(output, "type", type)

        dispatch_event(OutputNewEvent(output))

        self.active_index = len(self) - 1
        return output

    def remove(self, output: RBFDriverOutput) -> None:

        if not isinstance(output, RBFDriverOutput):
            raise TypeError((f'{self.__class__.__name__}.remove(output): '
                             f'Expected input to be {RBFDriverOutput.__name__}, '
                             f'not {output.__class__.__name__}'))

        index = next((index for item, index in enumerate(self) if item == output), -1)

        if index == -1:
            raise ValueError((f'{self.__class__.__name__}.remove(output): '
                             f'Output {output} not found in collection {self}'))

        dispatch_event(OutputDisposableEvent(output))
        self.collection__internal__.remove(index)
        dispatch_event(OutputRemovedEvent(output, index))
