
from typing import TYPE_CHECKING, Optional
from functools import partial
from numpy import array
from bpy.types import Object, PropertyGroup
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    IntProperty,
    PointerProperty,
    StringProperty
    )
from .mixins import BPYPropCollectionInterface, Collection, Reorderable, Searchable, Symmetrical
from .input_targets import (
    INPUT_TARGET_ID_TYPE_TABLE,
    INPUT_TARGET_TRANSFORM_SPACE_ITEMS,
    INPUT_TARGET_TRANSFORM_SPACE_TABLE,
    INPUT_TARGET_TRANSFORM_TYPE_TABLE,
    INPUT_TARGET_ROTATION_MODE_TABLE,
    InputTargetBoneTargetUpdateEvent,
    InputTargetObjectUpdateEvent,
    )
from .input_variables import (
    INPUT_VARIABLE_TYPE_TABLE,
    input_variable_is_enabled,
    input_variable_is_valid,
    InputVariables
    )
from ..app.events import dataclass, dispatch_event, Event, event_handler
from ..app.utils import (
    name_unique,
    euler_to_quaternion,
    euler_to_swing_twist_x,
    euler_to_swing_twist_y,
    euler_to_swing_twist_z,
    quaternion_to_euler,
    quaternion_to_swing_twist_x,
    quaternion_to_swing_twist_y,
    quaternion_to_swing_twist_z,
    swing_twist_x_to_euler,
    swing_twist_y_to_euler,
    swing_twist_z_to_euler,
    swing_twist_x_to_quaternion,
    swing_twist_y_to_quaternion,
    swing_twist_z_to_quaternion,
    swing_twist_x_to_swing_twist_y,
    swing_twist_x_to_swing_twist_z,
    swing_twist_y_to_swing_twist_x,
    swing_twist_y_to_swing_twist_z,
    swing_twist_z_to_swing_twist_x,
    swing_twist_z_to_swing_twist_y,
    )
if TYPE_CHECKING:
    from bpy.types import Context
    from .input_targets import InputTarget, InputTargetPropertyUpdateEvent
    from .input_data import InputSample
    from .poses import Poses
    from .driver import RBFDriver

ROTATION_CONVERSION_LUT = {
    'EULER': {
        'EULER'     : None,
        'SWING'     : euler_to_quaternion,
        'TWIST_X'   : partial(euler_to_swing_twist_x, quaternion=True),
        'TWIST_Y'   : partial(euler_to_swing_twist_y, quaternion=True),
        'TWIST_Z'   : partial(euler_to_swing_twist_z, quaternion=True),
        'QUATERNION': euler_to_quaternion,
        },
    'SWING': {
        'EULER'     : quaternion_to_euler,
        'SWING'     : None,
        'TWIST_X'   : partial(quaternion_to_swing_twist_x, quaternion=True),
        'TWIST_Y'   : partial(quaternion_to_swing_twist_y, quaternion=True),
        'TWIST_Z'   : partial(quaternion_to_swing_twist_z, quaternion=True),
        'QUATERNION': None,
        },
    'TWIST_X': {
        'EULER'     : swing_twist_x_to_euler,
        'SWING'     : swing_twist_x_to_quaternion,
        'TWIST_X'   : None,
        'TWIST_Y'   : swing_twist_x_to_swing_twist_y,
        'TWIST_Z'   : swing_twist_x_to_swing_twist_z,
        'QUATERNION': swing_twist_x_to_quaternion,
        },
    'TWIST_Y': {
        'EULER'     : swing_twist_y_to_euler,
        'SWING'     : swing_twist_y_to_quaternion,
        'TWIST_X'   : swing_twist_y_to_swing_twist_x,
        'TWIST_Y'   : None,
        'TWIST_Z'   : swing_twist_y_to_swing_twist_z,
        'QUATERNION': swing_twist_y_to_quaternion,
        },
    'TWIST_Z': {
        'EULER'     : swing_twist_z_to_euler,
        'SWING'     : swing_twist_z_to_quaternion,
        'TWIST_X'   : swing_twist_z_to_swing_twist_x,
        'TWIST_Y'   : swing_twist_z_to_swing_twist_y,
        'TWIST_Z'   : None,
        'QUATERNION': swing_twist_z_to_quaternion,
        },
    'QUATERNION': {
        'EULER'     : quaternion_to_euler,
        'SWING'     : None,
        'TWIST_X'   : partial(quaternion_to_swing_twist_x, quaternion=True),
        'TWIST_Y'   : partial(quaternion_to_swing_twist_y, quaternion=True),
        'TWIST_Z'   : partial(quaternion_to_swing_twist_z, quaternion=True),
        'QUATERNION': None,
        }
    }

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

INPUT_DISTANCE_METRIC_ITEMS = [
    ('EUCLIDEAN', "Euclidean", "Euclidean distance"),
    ('ANGLE', "Agnel", "Anglular difference"),
    ('QUATERNION', "Quaternion", "Quaternion distance"),
    ('DIRECTION', "Direction", "Aim vector difference"),
    ]

INPUT_DISTANCE_METRIC_INDEX = [
    item[0] for item in INPUT_DISTANCE_METRIC_ITEMS
    ]

INPUT_DISTANCE_METRIC_TABLE = {
    _item[0]: _index for _index, _item in enumerate(INPUT_DISTANCE_METRIC_ITEMS)
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
class InputPropertyUpdateEvent(Event):
    input: 'Input'


@dataclass(frozen=True)
class InputBoneTargetUpdateEvent(InputPropertyUpdateEvent):
    value: str


@dataclass(frozen=True)
class InputDataTypeUpdateEvent(InputPropertyUpdateEvent):
    value: str


@dataclass(frozen=True)
class InputNameUpdateEvent(InputPropertyUpdateEvent):
    value: str


@dataclass(frozen=True)
class InputObjectUpdateEvent(InputPropertyUpdateEvent):
    value: Object


@dataclass(frozen=True)
class InputRotationAxisUpdateEvent(InputPropertyUpdateEvent):
    value: str


@dataclass(frozen=True)
class InputRotationModeUpdateEvent(InputPropertyUpdateEvent):
    value: str
    previous_value: str


@dataclass(frozen=True)
class InputTransformSpaceUpdateEvent(InputPropertyUpdateEvent):
    value: str


@dataclass(frozen=True)
class InputUseMirrorXUpdateEvent(InputPropertyUpdateEvent):
    value: bool


@dataclass(frozen=True)
class InputUseSwingUpdateEvent(InputPropertyUpdateEvent):
    value: bool


def input_bone_target_update_handler(input: 'Input', _: 'Context') -> None:
    if input.type not in {'USER_DEF', 'SHAPE_KEY'} and input.name_is_user_defined:
        input["name"] = input_name_generate(input)

    if input.type in {'LOCATION', 'ROTATION', 'SCALE'}:
        value = input.bone_target
        for variable in input.variables:
            variable.targets[0]["bone_target"] = value

        dispatch_event(InputBoneTargetUpdateEvent(input, input.bone_target))


def input_data_type_update_handler(input: 'Input', _: 'Context') -> None:
    dispatch_event(InputDataTypeUpdateEvent(input, input.data_type))


def input_is_enabled(input: 'Input') -> bool:
    return any(input_variable_is_enabled(variable) for variable in input.variables)


def input_is_valid(input: 'Input') -> bool:
    variables = tuple(filter(input_variable_is_enabled, input.variables))
    return bool(len(variables)) and all(map(input_variable_is_valid, variables))


def input_name_update_handler(input: 'Input', _: 'Context') -> None:
    value = input.name
    if value:
        driver = input.driver
        input["name_is_user_defined"] = True
        input["name"] = name_unique(value, [i.name for i in driver.inputs if i != input])
    else:
        input["name_is_user_defined"] = False
        input["name"] = input_name_generate(input)
    dispatch_event(InputNameUpdateEvent(input, input.name))


def input_name_is_user_defined(input: 'Input') -> bool:
    return input.get("name_is_user_defined", False)


def input_object_validate(input: 'Input', object: Object) -> None:
    return input.type != 'SHAPE_KEY' or object.type in {'MESH', 'LATTICE', 'CURVE'}


def input_object_update_handler(input: 'Input', _: 'Context') -> None:
    if input.type in {'LOCATION', 'ROTATION', 'SCALE', 'SHAPE_KEY'}:
        if not input.name_is_user_defined:
            input["name"] = input_name_generate(input)

        value = input.object
        for variable in input.variables:
            variable.targets[0]["object"] = value

        dispatch_event(InputObjectUpdateEvent(input, input.object))


def input_rotation_axis_update_handler(input: 'Input', _: 'Context') -> None:
    if input.type == 'ROTATION':
        mode = input.rotation_mode
        if mode in {'SWING', 'TWIST'}:
            value = input.rotation_axis
            if mode == 'TWIST':
                mode = INPUT_TARGET_ROTATION_MODE_TABLE[f'SWING_TWIST_{value}']
                for variable in input.variables:
                    variable.targets[0]["rotation_mode"] = mode
            dispatch_event(InputRotationAxisUpdateEvent(input, value))


def input_rotation_mode(input: 'Input') -> int:
    return input.get("rotation_mode", 0)


def input_rotation_mode_set(input: 'Input', value: int) -> None:
    cache = input.rotation_mode
    input["rotation_mode"] = value
    if input.type == 'ROTATION':
        variables = input.variables
        value = input.rotation_mode

        if value == 'EULER':
            variables[0]["is_enabled"] = False
        elif value == 'TWIST':
            axis = input.rotation_axis
            variables[0]["is_enabled"] = False
            variables[1]["is_enabled"] = axis == 'X'
            variables[2]["is_enabled"] = axis == 'Y'
            variables[3]["is_enabled"] = axis == 'Z'
        else:
            for variable in variables:
                variable["is_enabled"] = True

        if   value == 'SWING' : value = 'QUATERNION'
        elif value == 'TWIST' : value = f'SWING_TWIST_{input.rotation_axis}'
        elif value == 'EULER' : value = input.rotation_order

        value = INPUT_TARGET_ROTATION_MODE_TABLE[value]
        for variable in variables:
            variable.targets[0]["rotation_mode"] = value

        mode = input.rotation_mode
        if mode == 'TWIST':
            mode = f'TWIST_{input.rotation_axis}'

        prev = cache
        if prev == 'TWIST':
            prev = f'TWIST_{input.rotation_axis}'

        convert = ROTATION_CONVERSION_LUT[prev][mode]
        if convert:
            matrix = array([tuple(v.data.values() for v in variables)], dtype=float)
            
            for vector, column in zip(
                    matrix.T if prev != 'EULER' else matrix[1:].T,
                    matrix.T if mode != 'EULER' else matrix[1:].T
                    ):
                column[:] = convert(vector)

            if mode == 'EULER':
                matrix[0] = 0.0

            for variable, data in zip(variables, matrix):
                samples: BPYPropCollectionInterface['InputSample'] = variable.data.internal__
                samples.foreach_set("value", data)


        dispatch_event(InputRotationModeUpdateEvent(input, input.rotation_mode, cache))


def input_transform_space_update_handler(input: 'Input', value: int) -> None:
    if input.type in {'LOCATION', 'ROTATION', 'SCALE'}:
        value = INPUT_TARGET_TRANSFORM_SPACE_TABLE[input.transform_space]
        for variable in input.variables:
            variable.targets[0]["transform_space"] = value
        dispatch_event(InputTransformSpaceUpdateEvent(input, input.transform_space))


def input_type(input) -> int:
    return input.get("type", 0)


def input_use_mirror_x_update_handler(input: 'Input', _: 'Context') -> None:
    dispatch_event(InputUseMirrorXUpdateEvent(input, input.use_mirror_x))


class Input(Symmetrical, PropertyGroup):

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

    @property
    def driver(self) -> 'RBFDriver':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".inputs")[0])

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
        items=INPUT_TARGET_TRANSFORM_SPACE_ITEMS,
        update=input_transform_space_update_handler,
        options=set(),
        )

    type: EnumProperty(
        name="Type",
        items=INPUT_TYPE_ITEMS,
        get=input_type,
        options=set(),
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
        type=InputVariables,
        options=set()
        )

    def __init__(self, type: str) -> None:
        self["type"] = INPUT_TYPE_TABLE[type]

        if type == 'LOCATION':
            self["transform_space"] = INPUT_TARGET_TRANSFORM_SPACE_TABLE['LOCAL_SPACE']

            for axis in "XYZ":
                variable = self.variables.internal__.add()
                variable["type"] = INPUT_VARIABLE_TYPE_TABLE['TRANSFORMS']
                variable["name"] = axis
                
                target = variable.targets.internal__.add()
                target["transform_space"] = INPUT_TARGET_TRANSFORM_SPACE_TABLE['LOCAL_SPACE']
                target["transform_type"] = INPUT_TARGET_TRANSFORM_TYPE_TABLE[f'LOC_{axis}']

        elif type == 'ROTATION':
            self["transform_space"] = INPUT_TARGET_TRANSFORM_SPACE_TABLE['LOCAL_SPACE']

            for axis, value in zip("WXYZ", (1.0, 0.0, 0.0, 0.0)):
                variable = self.variables.internal__.add()
                variable["type"] = INPUT_VARIABLE_TYPE_TABLE['TRANSFORMS']
                variable["name"] = axis
                variable["default_value"] = value

                target = variable.targets.internal__.add()
                target["transform_space"] = INPUT_TARGET_TRANSFORM_SPACE_TABLE['LOCAL_SPACE']
                target["transform_type"] = INPUT_TARGET_TRANSFORM_TYPE_TABLE[f'ROT_{axis}']
                target["rotation_mode"] = INPUT_TARGET_ROTATION_MODE_TABLE['QUATERNION']

        elif type == 'SCALE':
            self["transform_space"] = INPUT_TARGET_TRANSFORM_SPACE_TABLE['LOCAL_SPACE']

            for axis in "XYZ":
                variable = self.variables.internal__.add()
                variable["type"] = INPUT_VARIABLE_TYPE_TABLE['TRANSFORMS']
                variable["name"] = axis
                variable["default_value"] = 1.0
                
                target = variable.targets.internal__.add()
                target["transform_space"] = INPUT_TARGET_TRANSFORM_SPACE_TABLE['LOCAL_SPACE']
                target["transform_type"] = INPUT_TARGET_TRANSFORM_TYPE_TABLE[f'SCALE_{axis}']
        
        elif type.endswith('DIFF'):
            variable = self.variables.internal__.add()
            variable["type"] = INPUT_VARIABLE_TYPE_TABLE[type]
            variable["name"] = "var"
            
            variable.targets.internal__.add()
            variable.targets.internal__.add()

        elif type == 'SHAPE_KEY':
            variable = self.variables.internal__.add()
            variable["type"] = INPUT_VARIABLE_TYPE_TABLE["SINGLE_PROP"]
            variable["name"] = ""

            target = variable.targets.internal__.add()
            target["id_type"] = INPUT_TARGET_ID_TYPE_TABLE['KEY']

        else: # type == USER_DEF:
            variable = self.variables.internal__.add()
            variable["type"] = INPUT_VARIABLE_TYPE_TABLE["SINGLE_PROP"]
            variable["name"] = "var"
            variable.targets.internal__.add()
            variable.data["is_normalized"] = True

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'


@dataclass(frozen=True)
class InputNewEvent(Event):
    input: Input


@dataclass(frozen=True)
class InputDisposableEvent(Event):
    input: Input


@dataclass(frozen=True)
class InputRemovedEvent(Event):
    inputs: 'Inputs'
    index: int


@dataclass(frozen=True)
class InputMoveEvent(Event):
    input: Input
    from_index: int
    to_index: int


class Inputs(Reorderable, Searchable[Input], Collection[Input], PropertyGroup):

    active_index: IntProperty(
        name="Input",
        description="An RBF driver input",
        min=0,
        default=0,
        options=set()
        )

    @property
    def active(self) -> Optional[Input]:
        index = self.active_index
        return self[index] if index < len(self) else None

    internal__: CollectionProperty(
        type=Input,
        options={'HIDDEN'}
        )

    def __repr__(self) -> str:
        return self.__class__.__name__

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'

    def move(self, from_index: int, to_index: int) -> None:
        super().move(from_index, to_index)
        dispatch_event(InputMoveEvent(self, from_index, to_index))

    def new(self, type: str) -> Input:

        if not isinstance(type, str):
            raise TypeError((f'{self.__class__.__name__}.new(type): '
                             f'Expected type to be str, not {type.__class__.__name__}'))

        if type not in INPUT_TYPE_INDEX:
            raise ValueError((f'{self.__class__.__name__}.new(type): '
                              f'type {type} not found in {", ".join(INPUT_TYPE_INDEX)}'))

        input: Input = self.internal__.add()
        input.__init__(type)

        poses: 'Poses' = input.poses
        for variable in input.variables:
            default: float = variable.default_value
            samples: BPYPropCollectionInterface['InputSample'] = variable.data.internal__
            for pose in poses:
                samples.add().__init__(value=default)

        dispatch_event(InputNewEvent(input))
        self.active_index = len(self) - 1
        return input

    def remove(self, input: Input) -> None:

        if not isinstance(input, Input):
            raise TypeError((f'{self.__class__.__name__}.remove(input): '
                             f'Expected input to be {Input.__name__}, '
                             f'not {input.__class__.__name__}'))

        index = next((index for index, item in enumerate(self) if item == input), -1)
        if index == -1:
            raise ValueError((f'{self.__class__.__name__}.remove(input): '
                             f'Input {input} not found in collection {self}'))

        dispatch_event(InputDisposableEvent(input))

        self.internal__.remove(index)
        self.active_index = min(self.active_index, len(self)-1)

        dispatch_event(InputRemovedEvent(self, index))

#region Event Handlers
#--------------------------------------------------------------------------------------------------

@event_handler(InputTargetObjectUpdateEvent, InputTargetBoneTargetUpdateEvent)
def on_input_target_object_update(event: 'InputTargetPropertyUpdateEvent') -> None:
    input = event.target.input
    if input.type.endswith('DIFF') and not input.name_is_user_defined:
        input["name"] = input_name_generate(input)

#endregion

#region Utilities
#--------------------------------------------------------------------------------------------------

def input_target_token(target: 'InputTarget') -> str:
    object = target.object
    if object is None:
        return "?"
    if object.type == 'ARMATURE' and target.bone_target:
        return target.bone_target
    return object.name


def input_name_generate(input: 'Input') -> str:
    type = input.type

    if type in {'LOCATION', 'ROTATION', 'SCALE'}:
        result = type.title()
        object = input.object
        target = input.bone_target
        if object:
            suffix = target if target and object and object.type == "ARMATURE" else object.name
            result = f'{result} ({suffix})'

    elif type.endswith('DIFF'):
        result = "Distance" if type == 'LOC_DIFF' else "Rotational Difference"
        origin = input_target_token(input.variables[0].targets[0])
        target = input_target_token(input.variables[0].targets[1])
        result = f'{result} ({origin} - {target})'

    elif type == 'SHAPE_KEY':
        result = "Shape Keys"
        object = input.object
        if object:
            result = f'{result} ({object.name})'

    else:
        driver = input.driver
        result = name_unique("Input", [i.name for i in driver.inputs if i != input])

    return result

#endregion