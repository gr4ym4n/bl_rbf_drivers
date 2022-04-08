
from typing import TYPE_CHECKING, Optional
from bpy.types import PropertyGroup
from bpy.props import FloatProperty, IntProperty
from ..app.events import dataclass, dispatch_event, Event
from ..app.utils import owner_resolve
if TYPE_CHECKING:
    from .input_variable import RBFDriverInputVariable


@dataclass(frozen=True)
class InputVariableDataSampleUpdateEvent(Event):
    sample: 'RBFDriverInputVariableDataSample'
    value: Optional[float]


def input_variable_data_sample_index(sample: 'RBFDriverInputVariableDataSample') -> int:
    return sample.get("index", 0)


def input_variable_data_sample_value(sample: 'RBFDriverInputVariableDataSample') -> float:
    return sample.get("value", 0.0)


def input_variable_data_sample_value_normalized(sample: 'RBFDriverInputVariableDataSample') -> float:
    return sample.get("value_normalized", 0.0)


class RBFDriverInputVariableDataSample(PropertyGroup):

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

    def update(self, value: Optional[float]=None, propagate: Optional[bool]=True) -> None:
        """
        Updates the variable data sample value
        """

        if value is None:
            value = owner_resolve(self, ".data.").value

        elif not isinstance(value, float):
            raise TypeError((f'{self.__class__.__name__}.update(value): '
                             f'Expected value to be float, not {value.__class__.__name__}'))

        if propagate:
            dispatch_event(InputVariableDataSampleUpdateEvent(self, value))
