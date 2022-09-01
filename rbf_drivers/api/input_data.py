
from typing import Any, Dict, Iterable, Iterator, TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, FloatProperty
from ..app.events import dataclass, throttle_event, Event
from .mixins import BPYPropCollectionInterface, Collection
if TYPE_CHECKING:
    from .input_variables import InputVariable
    from .inputs import Input

#region InputSample
#--------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class InputSampleUpdateEvent(Event):
    sample: 'InputSample'
    value: float


def input_sample_value(sample: 'InputSample') -> float:
    return sample.get("value", 0.0)


def input_sample_value_set(sample: 'InputSample', value: float) -> None:
    sample["value"] = value
    throttle_event(InputSampleUpdateEvent(sample, value), timespan=0.2)


class InputSample(PropertyGroup):

    angle: FloatProperty(
        name="Value",
        description="Input sample value (angle)",
        subtype='ANGLE',
        get=input_sample_value,
        set=input_sample_value_set,
        options=set()
        )

    @property
    def input(self) -> 'Input':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".variables")[0])

    value: FloatProperty(
        name="Value",
        description="Input sample value",
        get=input_sample_value,
        set=input_sample_value_set,
        options=set()
        )

    @property
    def variable(self) -> 'InputVariable':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".data")[0])

    def __init__(self, **properties: Dict[str, Any]) -> None:
        for key, value in properties.items():
            self[key] = value

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'

#endregion

#region InputData
#--------------------------------------------------------------------------------------------------


class InputData(Collection[InputSample], PropertyGroup):

    internal__: CollectionProperty(
        type=InputSample,
        options={'HIDDEN'}
        )

    @property
    def input(self) -> 'Input':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".variables")[0])

    @property
    def variable(self) -> 'InputVariable':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])

    def __init__(self, data: Iterable[float]) -> None:
        samples: BPYPropCollectionInterface[InputSample] = self.internal__
        samples.clear()
        for value in data:
            samples.add().__init__(value=value)

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'

    def values(self) -> Iterator[float]:
        for item in self:
            yield item.value

#endregion
