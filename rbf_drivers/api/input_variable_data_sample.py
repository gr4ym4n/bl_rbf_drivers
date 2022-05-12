
from bpy.types import PropertyGroup
from bpy.props import FloatProperty, IntProperty
from ..app.events import dataclass, dispatch_event, Event


@dataclass(frozen=True)
class InputVariableDataSampleUpdateEvent(Event):
    sample: 'RBFDriverInputVariableDataSample'
    value: float


def input_variable_data_sample_index(sample: 'RBFDriverInputVariableDataSample') -> int:
    return sample.get("index", 0)


def input_variable_data_sample_value(sample: 'RBFDriverInputVariableDataSample') -> float:
    return sample.get("value", 0.0)


def input_variable_data_sample_value_set(sample: 'RBFDriverInputVariableDataSample', value: float) -> None:
    sample["value"] = value
    dispatch_event(InputVariableDataSampleUpdateEvent(sample, value))


def input_variable_data_sample_value_normalized(sample: 'RBFDriverInputVariableDataSample') -> float:
    return sample.get("value_normalized", input_variable_data_sample_value(sample))


class RBFDriverInputVariableDataSample(PropertyGroup):

    angle: FloatProperty(
        name="Value",
        description="The variable data sample value",
        subtype='ANGLE',
        get=input_variable_data_sample_value,
        set=input_variable_data_sample_value_set,
        options=set()
        )

    index: IntProperty(
        name="Index",
        description="The index of the variable data sample",
        get=input_variable_data_sample_index,
        options=set()
        )

    value: FloatProperty(
        name="Value",
        description="The variable data sample value",
        get=input_variable_data_sample_value,
        set=input_variable_data_sample_value_set,
        options=set()
        )

    value_normalized: FloatProperty(
        name="Normalized Value",
        description="The normalized variable data sample value",
        get=input_variable_data_sample_value_normalized,
        options=set()
        )

    def __init__(self, index: int, value: float) -> None:
        self["index"] = index
        self["value"] = value

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(index={self.index}, value={self.value})'

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".data__internal__", "")
        path = path.replace(".collection__internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'
