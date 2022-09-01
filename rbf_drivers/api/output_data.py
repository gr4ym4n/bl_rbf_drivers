
from typing import Any, Dict, Iterable, Iterator, Tuple, Union, TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, FloatProperty, StringProperty
from ..app.events import dataclass, dispatch_event, Event
from .mixins import BPYPropCollectionInterface, Collection
if TYPE_CHECKING:
    from .outputs import Output

#region OutputSample
#--------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class OutputSampleUpdateEvent(Event):
    sample: 'OutputSample'
    value: float


def output_sample_name(sample: 'OutputSample') -> str:
    return sample.get("name", "")


def output_sample_name_set(sample: 'OutputSample', _) -> None:
    raise AttributeError("OutputSample.name is read-only")


def output_sample_value(sample: 'OutputSample') -> float:
    return sample.get("value", 0.0)


def output_sample_value_set(sample: 'OutputSample', value: float) -> None:
    sample["value"] = value
    dispatch_event(OutputSampleUpdateEvent(sample, value))


class OutputSample(PropertyGroup):

    angle: FloatProperty(
        name="Value",
        description="The output channel data sample value",
        subtype='ANGLE',
        get=output_sample_value,
        set=output_sample_value_set,
        options=set()
        )

    name: StringProperty(
        name="Name",
        description="Input sample pose name (read-only)",
        get=output_sample_name,
        set=output_sample_name_set,
        options=set()
        )

    @property
    def output(self) -> 'Output':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".channels")[0])

    value: FloatProperty(
        name="Value",
        description="The output channel data sample value",
        get=output_sample_value,
        set=output_sample_value_set,
        options=set()
        )

    def __init__(self, **properties: Dict[str, Any]) -> None:
        for key, value in properties.items():
            self[key] = value

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(name={self.name}, value={self.value})'

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'

#endregion

#region

class OutputData(Collection[OutputSample], PropertyGroup):

    internal__: CollectionProperty(
        type=OutputSample,
        options=set()
        )

    def __init__(self, items: Iterable[Tuple[str, float]]) -> None:
        samples: BPYPropCollectionInterface = self.internal__
        samples.clear()
        for name, value in items:
            samples.add().__init__(name=name, value=value)

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'

    def value(self, key: Union[str, int]) -> float:
        # TODO error checking
        return self[key].value

    def values(self) -> Iterator[float]:
        for item in self:
            yield item.value

#endregion