
from bpy.types import PropertyGroup
from bpy.props import FloatProperty, IntProperty


def input_variable_data_sample_index(sample: 'RBFDriverInputVariableDataSample') -> int:
    return sample.get("index", 0)


def input_variable_data_sample_value(sample: 'RBFDriverInputVariableDataSample') -> float:
    return sample.get("value", 0.0)


def input_variable_data_sample_value_normalized(sample: 'RBFDriverInputVariableDataSample') -> float:
    return sample.get("value_normalized", 0.0)


class RBFDriverInputVariableDataSample(PropertyGroup):

    angle: FloatProperty(
        name="Value",
        description="The variable data sample value",
        subtype='ANGLE',
        get=input_variable_data_sample_value,
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
