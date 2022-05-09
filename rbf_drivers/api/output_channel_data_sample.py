
from bpy.types import PropertyGroup
from bpy.props import FloatProperty, IntProperty
from ..app.events import dataclass, dispatch_event, Event


@dataclass(frozen=True)
class OutputChannelDataSampleUpdateEvent(Event):
    sample: 'RBFDriverOutputChannelDataSample'
    value: float


def output_channel_data_sample_index(sample: 'RBFDriverOutputChannelDataSample') -> int:
    return sample.get("index", 0)


def output_channel_data_sample_value(sample: 'RBFDriverOutputChannelDataSample') -> float:
    return sample.get("value", 0.0)


def output_channel_data_sample_value_set(sample: 'RBFDriverOutputChannelDataSample', value: float) -> None:
    sample["value"] = value
    dispatch_event(OutputChannelDataSampleUpdateEvent(sample, value))


class RBFDriverOutputChannelDataSample(PropertyGroup):

    angle: FloatProperty(
        name="Value",
        description="The output channel data sample value",
        subtype='ANGLE',
        get=output_channel_data_sample_value,
        set=output_channel_data_sample_value_set,
        options=set()
        )

    index: IntProperty(
        name="Index",
        description="The index of the output channel data sample",
        get=output_channel_data_sample_index,
        options=set()
        )

    value: FloatProperty(
        name="Value",
        description="The output channel data sample value",
        get=output_channel_data_sample_value,
        set=output_channel_data_sample_value_set,
        options=set()
        )

    def __init__(self, index: int, value: float) -> None:
        self["index"] = index
        self["value"] = value
