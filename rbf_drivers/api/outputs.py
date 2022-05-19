
from typing import Optional
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, CollectionProperty, IntProperty
from .mixins import Collection, Reorderable, Searchable
from .output import OUTPUT_TYPE_INDEX, RBFDriverOutput, output_mute, OUTPUT_TYPE_TABLE
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
    return all(map(output_mute, outputs))


def outputs_mute_set(outputs: 'RBFDriverOutputs', value: bool) -> None:
    for output in outputs:
        output.mute = value


class RBFDriverOutputs(Reorderable,
                       Searchable[RBFDriverOutput],
                       Collection[RBFDriverOutput],
                       PropertyGroup):

    active_index: IntProperty(
        name="Output",
        description="An RBF driver output",
        min=0,
        default=0,
        options=set()
        )

    @property
    def active(self) -> Optional[RBFDriverOutput]:
        index = self.active_index
        return self[index] if index < len(self) else None

    collection__internal__: CollectionProperty(
        type=RBFDriverOutput,
        options={'HIDDEN'}
        )

    mute: BoolProperty(
        name="Mute",
        description="Mute/Unmute output drivers",
        get=outputs_mute,
        set=outputs_mute_set,
        options=set()
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(active_index={self.active_index})'

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".collection__internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'

    def move(self, from_index: int, to_index: int) -> None:
        super().move(from_index, to_index)
        dispatch_event(OutputMoveEvent(self, from_index, to_index))

    def new(self, type: str) -> RBFDriverOutput:

        if not isinstance(type, str):
            raise TypeError((f'{self.__class__.__name__}.new(type): '
                             f'Expected type to be str, not {type.__class__.__name__}'))

        if type not in OUTPUT_TYPE_INDEX:
            raise ValueError((f'{self.__class__.__name__}.new(type): '
                              f'type {type} not found in {", ".join(OUTPUT_TYPE_INDEX)}'))

        output: RBFDriverOutput = self.collection__internal__.add()
        output["type"] = OUTPUT_TYPE_TABLE[type]

        dispatch_event(OutputNewEvent(output))

        self.active_index = len(self) - 1
        return output

    def remove(self, output: RBFDriverOutput) -> None:

        if not isinstance(output, RBFDriverOutput):
            raise TypeError((f'{self.__class__.__name__}.remove(output): '
                             f'Expected input to be {RBFDriverOutput.__name__}, '
                             f'not {output.__class__.__name__}'))

        index = next((index for index, item in enumerate(self) if item == output), -1)

        if index == -1:
            raise ValueError((f'{self.__class__.__name__}.remove(output): '
                              f'{output} not found in {self}'))

        dispatch_event(OutputDisposableEvent(output))
        self.collection__internal__.remove(index)
        dispatch_event(OutputRemovedEvent(output, index))
