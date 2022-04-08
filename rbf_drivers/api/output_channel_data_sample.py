
from typing import Optional, TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import FloatProperty, IntProperty
from ..app.events import dataclass, dispatch_event, Event
from ..app.utils import owner_resolve
if TYPE_CHECKING:
    from .output_channel import RBFDriverOutputChannel


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
        description="The variable data sample value",
        subtype='ANGLE',
        get=output_channel_data_sample_value,
        set=output_channel_data_sample_value_set,
        options=set()
        )

    easing: FloatProperty(
        name="Value",
        description="The variable data sample value",
        soft_min=0.0,
        soft_max=5.0,
        get=output_channel_data_sample_value,
        set=output_channel_data_sample_value_set,
        options=set()
        )

    index: IntProperty(
        name="Index",
        description="The index of the variable data sample",
        get=output_channel_data_sample_index,
        options=set()
        )

    value: FloatProperty(
        name="Value",
        description="The variable data sample value",
        get=output_channel_data_sample_value,
        set=output_channel_data_sample_value_set,
        options=set()
        )

    def __init__(self, index: int, value: float) -> None:
        self["index"] = index
        self["value"] = value

    def update(self, value: Optional[float]=None, propagate: Optional[bool]=True) -> None:
        """
        Updates the channel data sample value from the current channel value
        """
        if value is None:
            channel: 'RBFDriverOutputChannel' = owner_resolve(self, ".data.")
            value = channel.value

        elif not isinstance(value, float):
            raise TypeError((f'{self.__class__.__name__}.update(value): '
                             f'Expected value to be float, not {value.__class__.__name__}'))

        self["value"] = value
        if propagate:
            dispatch_event(OutputChannelDataSampleUpdateEvent(self, self.value))