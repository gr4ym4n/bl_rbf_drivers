
from typing import TYPE_CHECKING
from bpy.types import Object, PropertyGroup
from bpy.props import BoolProperty, EnumProperty, PointerProperty, StringProperty
from .mixins import Symmetrical
from .input_variables import RBFDriverInputVariables
from ..app.events import dataclass, dispatch_event, event_handler, Event
from ..lib.transform_utils import TRANSFORM_SPACE_INDEX, TRANSFORM_SPACE_ITEMS
if TYPE_CHECKING:
    from bpy.types import Context

INPUT_DATA_TYPE_ITEMS = [
    ('FLOAT'     , "Float"     , "Floating point value"),
    ('ANGLE'     , "Angle"     , "Euler Angles"        ),
    ('QUATERNION', "Quaternion", "Quaternion rotation" ),
    ]

INPUT_DATA_TYPE_INDEX = [
    item[0] for item in INPUT_DATA_TYPE_ITEMS
    ]

INPUT_DATA_TYPE_TABLE = {
    item[0]: index for index, item in enumerate(INPUT_DATA_TYPE_ITEMS)
    }

INPUT_ROTATION_AXIS_ITEMS = [
    ('X', "X", "X axis"),
    ('Y', "Y", "Y axis"),
    ('Z', "Z", "Z axis"),
    ]

INPUT_ROTATION_AXIS_INDEX = [
    item[0] for item in INPUT_ROTATION_AXIS_ITEMS
    ]

INPUT_ROTATION_MODE_ITEMS = [
    ('EULER'     , "Euler"     , "Euler angles"       ),
    ('QUATERNION', "Quaternion", "Quaternion rotation"),
    ('SWING'     , "Swing"     , "Swing rotation"     ),
    ('TWIST'     , "Twist"     , "Twist rotation"     ),
    ]

INPUT_ROTATION_MODE_INDEX = [
    item[0] for item in INPUT_ROTATION_MODE_ITEMS
    ]

INPUT_ROTATION_MODE_TABLE = {
    item[0]: index for index, item in enumerate(INPUT_ROTATION_MODE_ITEMS)
    }

INPUT_ROTATION_ORDER_ITEMS = [
    ('AUTO', "Auto", "Euler using the rotation order of the target."),
    ('XYZ' , "XYZ" , "Euler using the XYZ rotation order."          ),
    ('XZY' , "XZY" , "Euler using the XZY rotation order."          ),
    ('YXZ' , "YXZ" , "Euler using the YXZ rotation order."          ),
    ('YZX' , "YZX" , "Euler using the YZX rotation order."          ),
    ('ZXY' , "ZXY" , "Euler using the ZXY rotation order."          ),
    ('ZYX' , "ZYX" , "Euler using the ZYX rotation order."          ),
    ]

INPUT_TYPE_ITEMS = [
    ('LOCATION', "Location", "Location transform channels", 'CON_LOCLIMIT' , 0),
    ('ROTATION', "Rotation", "Rotation transform channels", 'CON_ROTLIMIT' , 1),
    ('SCALE'   , "Scale"   , "Scale transform channels"   , 'CON_SIZELIMIT', 2),
    None,
    ('ROTATION_DIFF', "Rotational Difference", "Angle between two bones or objects."   , 'DRIVER_ROTATIONAL_DIFFERENCE', 3),
    ('LOC_DIFF'     , "Distance"             , "Distance between two bones or objects.", 'DRIVER_DISTANCE'             , 4),
    None,
    ('SHAPE_KEY', "Shape Keys"  , "Shape key values"               , 'SHAPEKEY_DATA', 5),
    ('USER_DEF' , "User-defined", "Fully configurable input values", 'RNA'          , 6),
    ]

INPUT_TYPE_INDEX = [
    item[0] for item in INPUT_TYPE_ITEMS if item is not None
    ]

INPUT_TYPE_TABLE = {
    item[0]: item[4] for item in INPUT_TYPE_ITEMS if item is not None
    }

INPUT_TYPE_ICONS = {
    item[0]: item[3] for item in INPUT_TYPE_ITEMS if item is not None
    }


@dataclass(frozen=True)
class InputBoneTargetUpdateEvent(Event):
    input: 'RBFDriverInput'
    value: str


@dataclass(frozen=True)
class InputDataTypeUpdateEvent(Event):
    input: 'RBFDriverInput'
    value: str


@dataclass(frozen=True)
class InputNameUpdateEvent(Event):
    input: 'RBFDriverInput'
    value: str


@dataclass(frozen=True)
class InputObjectUpdateEvent(Event):
    input: 'RBFDriverInput'
    value: Object


@dataclass(frozen=True)
class InputRotationAxisUpdateEvent(Event):
    input: 'RBFDriverInput'
    value: str


@dataclass(frozen=True)
class InputRotationModeChangeEvent(Event):
    input: 'RBFDriverInput'
    value: str
    previous_value: str


@dataclass(frozen=True)
class InputTransformSpaceChangeEvent(Event):
    input: 'RBFDriverInput'
    value: str
    previous_value: str


@dataclass(frozen=True)
class InputTypeUpdateEvent(Event):
    input: 'RBFDriverInput'
    value: str
    previous_value: str


@dataclass(frozen=True)
class InputUseSwingUpdateEvent(Event):
    input: 'RBFDriverInput'
    value: bool


def input_bone_target_update_handler(input: 'RBFDriverInput', _: 'Context') -> None:
    dispatch_event(InputBoneTargetUpdateEvent(input, input.bone_target))


def input_data_type_update_handler(input: 'RBFDriverInput', _: 'Context') -> None:
    dispatch_event(InputDataTypeUpdateEvent(input, input.data_type))


def input_is_valid(input: 'RBFDriverInput') -> bool:
    for variable in input.variables:
        if variable.is_enabled and not variable.is_valid:
            return False
    return True


def input_name_update_handler(input: 'RBFDriverInput', _: 'Context') -> None:
    dispatch_event(InputNameUpdateEvent(input, input.name))


def input_name_is_user_defined(input: 'RBFDriverInput') -> bool:
    return input.get("name_is_user_defined")


def input_object_validate(input: 'RBFDriverInput', object: Object) -> None:
    return input.type != 'SHAPE_KEY' or object.type in {'MESH', 'LATTICE', 'CURVE'}


def input_object_update_handler(input: 'RBFDriverInput', _: 'Context') -> None:
    dispatch_event(InputObjectUpdateEvent(input, input.object))


def input_rotation_axis_update_handler(input: 'RBFDriverInput', _: 'Context') -> None:
    dispatch_event(InputRotationAxisUpdateEvent(input, input.rotation_axis))


def input_rotation_mode(input: 'RBFDriverInput') -> int:
    return input.get("rotation_mode", 0)


def input_rotation_mode_set(input, value: int) -> None:
    cache = input_rotation_mode(input)
    input["rotation_mode"] = value
    dispatch_event(InputRotationModeChangeEvent(input,
                                                INPUT_ROTATION_MODE_INDEX[value],
                                                INPUT_ROTATION_MODE_INDEX[cache]))


def input_transform_space(input: 'RBFDriverInput') -> int:
    return input.get("transform_space", 0)


def input_transform_space_set(input: 'RBFDriverInput', value: int) -> None:
    cache = input_transform_space(input)
    input["transform_space"] = value
    dispatch_event(InputTransformSpaceChangeEvent(input,
                                                  TRANSFORM_SPACE_INDEX[cache],
                                                  TRANSFORM_SPACE_INDEX[value]))


def input_type(input) -> int:
    return input.get("type", 0)


def input_type_set(input: 'RBFDriverInput', value: int) -> None:
    cache = input_type(input)
    input["type"] = value
    dispatch_event(InputTypeUpdateEvent(input,
                                        INPUT_TYPE_TABLE[value],
                                        INPUT_TYPE_TABLE[cache]))


def input_use_swing_update_handler(input: 'RBFDriverInput', _: 'Context') -> None:
    dispatch_event(InputUseSwingUpdateEvent(input, input.use_swing))


class RBFDriverInput(Symmetrical, PropertyGroup):

    bone_target: StringProperty(
        name="Bone",
        description="Name of pose bone to read input values from",
        default="",
        options=set(),
        update=input_bone_target_update_handler,
        )

    data_type: EnumProperty(
        name="Type",
        description="Data type",
        items=INPUT_DATA_TYPE_ITEMS,
        default=INPUT_DATA_TYPE_ITEMS[0][0],
        update=input_data_type_update_handler,
        options=set()
        )

    is_valid: BoolProperty(
        name="Valid",
        description="Whether the input has a valid target or not (read-only)",
        get=input_is_valid,
        options=set()
        )

    name: StringProperty(
        name="Name",
        description="Input name",
        update=input_name_update_handler,
        options=set()
        )

    name_is_user_defined: BoolProperty(
        name="User Defined Name",
        description="Name is user-defined (internal use)",
        get=input_name_is_user_defined,
        options=set()
        )

    object: PointerProperty(
        name="Object",
        description="The target object",
        type=Object,
        poll=input_object_validate,
        options=set(),
        update=input_object_update_handler
        )

    rotation_axis: EnumProperty(
        name="Axis",
        description="The axis of rotation",
        items=[
            ('X', "X", "X axis rotation"),
            ('Y', "Y", "Y axis rotation"),
            ('Z', "Z", "Z axis rotation"),
            ],
        default='Y',
        options=set(),
        update=input_rotation_axis_update_handler
        )

    rotation_mode: EnumProperty(
        name="Mode",
        description="Rotation mode",
        items=INPUT_ROTATION_MODE_ITEMS,
        get=input_rotation_mode,
        set=input_rotation_mode_set,
        options=set(),
        )

    rotation_order: EnumProperty(
        name="Order",
        description="Rotation order",
        items=INPUT_ROTATION_ORDER_ITEMS,
        default=INPUT_ROTATION_ORDER_ITEMS[0][0],
        options=set()
        )

    transform_space: EnumProperty(
        name="Space",
        description="The space for transform channels",
        items=TRANSFORM_SPACE_ITEMS,
        get=input_transform_space,
        set=input_transform_space_set,
        options=set(),
        )

    type: EnumProperty(
        name="Type",
        items=INPUT_TYPE_ITEMS,
        get=input_type,
        options=set(),
        )

    use_swing: BoolProperty(
        name="Swing",
        description="Extract swing values from quaternion rotation",
        update=input_use_swing_update_handler,
        options=set()
        )

    ui_show_pose: BoolProperty(
        name="Show",
        description="Show/Hide pose values in the UI",
        default=False,
        options=set()
        )

    variables: PointerProperty(
        name="Variables",
        type=RBFDriverInputVariables,
        options=set()
        )
