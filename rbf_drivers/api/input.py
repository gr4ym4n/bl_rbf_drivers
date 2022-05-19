
from cmath import isnan
from typing import TYPE_CHECKING, Optional, Union
from bpy.types import Object, PropertyGroup
from bpy.props import BoolProperty, EnumProperty, PointerProperty, StringProperty
from rbf_drivers.api.input_variable import input_variable_is_enabled, input_variable_is_valid
from .mixins import Symmetrical
from .input_variables import RBFDriverInputVariables
from ..app.events import dataclass, dispatch_event, Event
from ..lib.transform_utils import TRANSFORM_SPACE_INDEX, TRANSFORM_SPACE_ITEMS, TRANSFORM_SPACE_TABLE
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

INPUT_ROTATION_AXIS_TABLE = {
    item[0]: index for index, item in enumerate(INPUT_ROTATION_AXIS_ITEMS)
    }

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

INPUT_ROTATION_ORDER_INDEX = [
    item[0] for item in INPUT_ROTATION_ORDER_ITEMS
    ]

INPUT_ROTATION_ORDER_TABLE = {
    item[0]: index for index, item in enumerate(INPUT_ROTATION_ORDER_ITEMS)
    }

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
class InputUseMirrorXUpdateEvent(Event):
    input: 'RBFDriverInput'
    value: bool


@dataclass(frozen=True)
class InputUseSwingUpdateEvent(Event):
    input: 'RBFDriverInput'
    value: bool


def input_bone_target_update_handler(input: 'RBFDriverInput', _: 'Context') -> None:
    dispatch_event(InputBoneTargetUpdateEvent(input, input.bone_target))


def input_data_type_update_handler(input: 'RBFDriverInput', _: 'Context') -> None:
    dispatch_event(InputDataTypeUpdateEvent(input, input.data_type))


def input_is_enabled(input: 'RBFDriverInput') -> bool:
    return any(input_variable_is_enabled(variable) for variable in input.variables)


def input_is_valid(input: 'RBFDriverInput') -> bool:
    variables = tuple(filter(input_variable_is_enabled, input.variables))
    return bool(len(variables)) and all(map(input_variable_is_valid, variables))


def input_name_update_handler(input: 'RBFDriverInput', _: 'Context') -> None:
    dispatch_event(InputNameUpdateEvent(input, input.name))


def input_name_is_user_defined(input: 'RBFDriverInput') -> bool:
    return input.get("name_is_user_defined", False)


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
                                                  TRANSFORM_SPACE_INDEX[value],
                                                  TRANSFORM_SPACE_INDEX[cache]))


def input_type(input) -> int:
    return input.get("type", 0)


def input_type_set(input: 'RBFDriverInput', value: int) -> None:
    cache = input_type(input)
    input["type"] = value
    dispatch_event(InputTypeUpdateEvent(input,
                                        INPUT_TYPE_TABLE[value],
                                        INPUT_TYPE_TABLE[cache]))


def input_use_mirror_x_update_handler(input: 'RBFDriverInput', _: 'Context') -> None:
    dispatch_event(InputUseMirrorXUpdateEvent(input, input.use_mirror_x))


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

    is_enabled: BoolProperty(
        name="Enabled",
        description="Whether the input has at least one enabled variable",
        get=input_is_enabled,
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

    use_mirror_x: BoolProperty(
        name="X-Mirror",
        description="Mirror transform values along X-axis",
        default=True,
        options=set(),
        update=input_use_mirror_x_update_handler
        )

    variables: PointerProperty(
        name="Variables",
        type=RBFDriverInputVariables,
        options=set()
        )

    def __init__(self, type: Union[int, str],
                       name: Optional[str]=None,
                       object: Optional[Object]=None,
                       bone_target: Optional[str]=None,
                       data_path: Optional[str]=None,
                       data_type: Optional[Union[int, str]]=None,
                       rotation_mode: Optional[Union[int, str]]=None,
                       rotation_axis: Optional[Union[int, str]]=None,
                       rotation_order: Optional[Union[int, str]]=None,
                       transform_space: Optional[Union[int, str]]=None,
                       use_mirror_x: Optional[bool]=None,
                       use_swing: Optional[bool]=None) -> None:
        
        assert (isinstance(type, int) and 0 <= type < len(INPUT_TYPE_INDEX)
                or isinstance(type, str) and type in INPUT_TYPE_TABLE)
        
        if isinstance(type, str):
            type = INPUT_TYPE_TABLE[type]

        assert name is None or isinstance(name, str)

        if object is not None:
            assert isinstance(object, Object)
            # Prevent Input from keeping hold of an Object pointer that will never be used
            assert type in {'LOCATION', 'ROTATION', 'SCALE', 'SHAPE_KEY'}

        assert bone_target is None or isinstance(bone_target, str)
        assert data_path is None or isinstance(data_path, str)

        assert (data_type is None
                or (isinstance(data_type, int) and 0 <= data_type < len(INPUT_DATA_TYPE_INDEX))
                or (isinstance(data_type, str) and data_type in INPUT_DATA_TYPE_TABLE))

        assert (rotation_mode is None
                or (isinstance(rotation_mode, int) and 0 <= rotation_mode < len(INPUT_ROTATION_MODE_INDEX))
                or (isinstance(rotation_mode, str) and rotation_mode in INPUT_ROTATION_MODE_TABLE))

        assert (rotation_axis is None
                or (isinstance(rotation_axis, int) and 0 <= rotation_axis < len(INPUT_ROTATION_AXIS_INDEX))
                or (isinstance(rotation_axis, str) and rotation_axis in INPUT_ROTATION_AXIS_TABLE))

        assert (rotation_order is None
                or (isinstance(rotation_order, int) and 0 <= rotation_order < len(INPUT_ROTATION_ORDER_INDEX))
                or (isinstance(rotation_order, str) and rotation_order in INPUT_ROTATION_ORDER_TABLE))

        assert (transform_space is None
                or (isinstance(transform_space, int) and 0 <= transform_space < len(TRANSFORM_SPACE_INDEX))
                or (isinstance(transform_space, str) and transform_space in TRANSFORM_SPACE_TABLE))

        assert use_mirror_x is None or isinstance(use_mirror_x, bool)
        assert use_swing is None or isinstance(use_swing, bool)

        self["type"] = type

        if name:
            self["name"] = name

        if object is not None:
            self["object"] = object

        if bone_target is not None:
            self["bone_target"] = bone_target

        if data_path is not None:
            self["data_path"] = data_path

        if data_type is not None:
            self["data_type"] = data_type if isinstance(data_type, int) else INPUT_DATA_TYPE_TABLE[data_type]

        if rotation_mode is not None:
            self["rotation_mode"] = rotation_mode if isinstance(rotation_mode, int) else INPUT_ROTATION_MODE_TABLE[rotation_mode]

        if rotation_axis is not None:
            self["rotation_axis"] = rotation_axis if isinstance(rotation_axis, int) else INPUT_ROTATION_AXIS_TABLE[rotation_axis]

        if rotation_order is not None:
            self["rotation_order"] = rotation_order if isinstance(rotation_order, int) else INPUT_ROTATION_ORDER_TABLE[rotation_order]

        if transform_space is not None:
            self["transform_space"] = transform_space if isinstance(transform_space, int) else TRANSFORM_SPACE_TABLE[transform_space]

        if use_mirror_x is not None:
            self["use_mirror_x"] = use_mirror_x

        if use_swing is not None:
            self["use_swing"] = use_swing

    def __repr__(self) -> str:
        result = f'{self.__class__.__name__}('

        type = self.type
        result += f'type={type}, name={self.name}'

        if not type.endswith('DIFF'):
            object = self.object
            if object is None:
                result += f', object=None'
            else:
                result += f', object={repr(object)}'

                if (type in {'LOCATION', 'ROTATION', 'SCALE'}
                    and object.type == 'ARMATURE'
                    and self.bone_target
                    ):
                    result += f', bone_target="{self.bone_target}"'

        if type in {'LOCATION', 'ROTATION', 'SCALE'}:
            result += f', transform_space="{self.transform_space}"'

        if type == 'ROTATION':
            result += f', rotation_mode="{self.rotation_mode}"'
            
            if self.rotation_mode == 'EULER':
                result += f', rotation_order="{self.rotation_order}"'
            elif type != 'QUATERNION':
                result += f', rotation_axis="{self.rotation_axis}"'

        if type in {'LOCATION', 'ROTATION', 'SCALE', 'SHAPE_KEY'}:
            result += f', use_mirror_x="{self.use_mirror_x}"'

        if type == 'USER_DEF' and self.data_type == 'QUATERNION':
            result += f', use_swing={self.use_swing}'

        result += ")"
        return result

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".collection__internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'
