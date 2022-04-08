
from bpy.types import Context, PropertyGroup
from bpy.props import BoolProperty, EnumProperty, PointerProperty, StringProperty
from .mixins import Layer
from .input_variable import input_variable_is_enabled, input_variable_is_valid
from .input_variables import RBFDriverInputVariables
from ..lib.transform_utils import ROTATION_MODE_ITEMS
from ..app.events import dataclass, dispatch_event, Event


INPUT_ROTATION_MODE_ITEMS = ROTATION_MODE_ITEMS[0:-3] + [
    ('SWING_X', "X Swing", "Swing rotation to aim the X axis", 'NONE', 8 ),
    ('SWING_Y', "Y Swing", "Swing rotation to aim the Y axis", 'NONE', 9 ),
    ('SWING_Z', "Z Swing", "Swing rotation to aim the Z axis", 'NONE', 10),
    ('TWIST_X', "X Twist", "Twist around the X axis"         , 'NONE', 11),
    ('TWIST_Y', "Y Twist", "Twist around the Y axis"         , 'NONE', 12),
    ('TWIST_Z', "Z Twist", "Twist around the Z axis"         , 'NONE', 13),
    ]

INPUT_ROTATION_MODE_INDEX = {
    item[0]: item[4] for item in INPUT_ROTATION_MODE_ITEMS
    }

INPUT_ROTATION_MODE_TABLE = {
    item[4]: item[0] for item in INPUT_ROTATION_MODE_ITEMS
    }

INPUT_TYPE_ITEMS = [
    ('NONE'     , "Single Property" , "RNA property value"         , 'NONE', 0),
    ('LOCATION' , "Location"        , "Location transform channels", 'NONE', 1),
    ('ROTATION' , "Rotation"        , "Rotation transform channels", 'NONE', 2),
    ('SCALE'    , "Scale"           , "Scale transform channels"   , 'NONE', 3),
    ('BBONE'    , "BBone Properties", "BBone property values"      , 'NONE', 4),
    ('SHAPE_KEY', "Shape Key(s)"    , "Shape key values"           , 'NONE', 5),
    ]

INPUT_TYPE_INDEX = {
    item[0]: item[4] for item in INPUT_TYPE_ITEMS
    }


@dataclass(frozen=True)
class InputNameUpdateEvent(Event):
    input: 'RBFDriverInput'
    value: str


@dataclass(frozen=True)
class InputRotationModeChangeEvent(Event):
    input: 'RBFDriverInput'
    value: str
    previous_value: str


def input_is_valid(input: 'RBFDriverInput') -> bool:
    for variable in input.variables:
        if variable.is_enabled and not variable.is_valid:
            return False
    return True


def input_name_update_handler(input: 'RBFDriverInput', _: Context) -> None:
    dispatch_event(InputNameUpdateEvent(input, input.name))


def input_rotation_mode(input: 'RBFDriverInput') -> int:
    return input.get("rotation_mode", 0)


def input_rotation_mode_set(input, value: int) -> None:
    cache = input_rotation_mode(input)
    input["rotation_mode"] = value
    dispatch_event(InputRotationModeChangeEvent(input,
                                                INPUT_ROTATION_MODE_TABLE[value],
                                                INPUT_ROTATION_MODE_TABLE[cache]))


def input_type(input) -> int:
    return input.get("type", 0)


class RBFDriverInput(Layer, PropertyGroup):

    kind = 'INPUT'

    @property
    def is_valid(self) -> bool:
        return input_is_valid(self)

    name: StringProperty(
        name="Name",
        options=set(),
        update=input_name_update_handler
        )

    rotation_mode: EnumProperty(
        name="Mode",
        description="Rotation mode",
        items=INPUT_ROTATION_MODE_ITEMS,
        get=input_rotation_mode,
        set=input_rotation_mode_set,
        options=set(),
        )

    type: EnumProperty(
        name="Type",
        items=INPUT_TYPE_ITEMS,
        get=input_type,
        options=set(),
        )

    variables: PointerProperty(
        name="Variables",
        type=RBFDriverInputVariables,
        options=set()
        )
