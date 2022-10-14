
from typing import TYPE_CHECKING, Callable, Dict, Optional
from functools import partial
import numpy as np
from .events import dataclass, dispatch_event, event_handler, Event
from .utils import (
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
from ..api.interfaces import ICollection
from ..api.input_data import InputSampleUpdateEvent
from ..api.input_targets import (
    INPUT_TARGET_ID_TYPE_TABLE,
    INPUT_TARGET_ROTATION_MODE_TABLE,
    INPUT_TARGET_TRANSFORM_SPACE_TABLE,
    INPUT_TARGET_TRANSFORM_TYPE_TABLE,
    InputTargetBoneTargetUpdateEvent,
    InputTargetDataPathUpdateEvent,
    InputTargetIDTypeUpdateEvent,
    InputTargetObjectUpdateEvent,
    InputTargetRotationModeUpdateEvent,
    InputTargetTransformSpaceUpdateEvent,
    InputTargetTransformTypeUpdateEvent,
    )
from ..api.input_variables import (
    INPUT_VARIABLE_TYPE_TABLE,
    InputVariableTypeUpdateEvent,
    InputVariableIsEnabledUpdateEvent,
    InputVariableNameUpdateEvent,
    InputVariableNewEvent,
    InputVariableRemovedEvent,
    )
from ..api.input import (
    InputBoneTargetUpdateEvent,
    InputObjectUpdateEvent,
    InputRotationAxisUpdateEvent,
    InputRotationModeUpdateEvent,
    InputTransformSpaceUpdateEvent,
    )
from ..api.inputs import InputNewEvent
from ..api.poses import PoseNewEvent, PoseRemovedEvent
if TYPE_CHECKING:
    from ..api.input_data import InputSample
    from ..api.input_targets import InputTargetPropertyUpdateEvent
    from ..api.input_variables import InputVariablePropertyUpdateEvent, InputVariable
    from ..api.input import InputPropertyUpdateEvent, Input

ROTATION_CONVERSION_LUT: Dict[str, Dict[str, Optional[Callable]]] = {
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


@dataclass(frozen=True)
class InputInitializedEvent(Event):
    input: 'Input'


@dataclass(frozen=True)
class InputSamplesUpdatedEvent(Event):
    input: 'Input'


@dataclass(frozen=True)
class InputSourcesUpdatedEvent(Event):
    input: 'Input'


def input_variable_data_init(variable: 'InputVariable', pose_count: int) -> None:
    default: float = variable.default_value
    samples: ICollection['InputSample'] = variable.data.internal__
    for _ in range(pose_count):
        samples.add()["value"] = default


def input_init_location(input_: 'Input') -> None:
    pose_count = len(input_.driver.poses)
    input_["transform_space"] = INPUT_TARGET_TRANSFORM_SPACE_TABLE['LOCAL_SPACE']
    
    for axis in "XYZ":
        variable = input_.variables.internal__.add()
        variable["type"] = INPUT_VARIABLE_TYPE_TABLE['TRANSFORMS']
        variable["name"] = axis

        target = variable.targets.internal__.add()
        target["transform_space"] = INPUT_TARGET_TRANSFORM_SPACE_TABLE['LOCAL_SPACE']
        target["transform_type"] = INPUT_TARGET_TRANSFORM_TYPE_TABLE[f'LOC_{axis}']

        input_variable_data_init(variable, pose_count)


def input_init_rotation(input_: 'Input') -> None:
    pose_count = len(input_.driver.poses)
    input_["transform_space"] = INPUT_TARGET_TRANSFORM_SPACE_TABLE['LOCAL_SPACE']

    for axis, value in zip("WXYZ", (1.0, 0.0, 0.0, 0.0)):
        variable = input_.variables.internal__.add()
        variable["type"] = INPUT_VARIABLE_TYPE_TABLE['TRANSFORMS']
        variable["name"] = axis
        variable["default_value"] = value

        target = variable.targets.internal__.add()
        target["transform_space"] = INPUT_TARGET_TRANSFORM_SPACE_TABLE['LOCAL_SPACE']
        target["transform_type"] = INPUT_TARGET_TRANSFORM_TYPE_TABLE[f'ROT_{axis}']
        target["rotation_mode"] = INPUT_TARGET_ROTATION_MODE_TABLE['QUATERNION']

        input_variable_data_init(variable, pose_count)


def input_init_scale(input_: 'Input') -> None:
    pose_count = len(input_.driver.poses)
    input_["transform_space"] = INPUT_TARGET_TRANSFORM_SPACE_TABLE['LOCAL_SPACE']

    for axis in "XYZ":
        variable = input_.variables.internal__.add()
        variable["type"] = INPUT_VARIABLE_TYPE_TABLE['TRANSFORMS']
        variable["name"] = axis
        variable["default_value"] = 1.0
        
        target = variable.targets.internal__.add()
        target["transform_space"] = INPUT_TARGET_TRANSFORM_SPACE_TABLE['LOCAL_SPACE']
        target["transform_type"] = INPUT_TARGET_TRANSFORM_TYPE_TABLE[f'SCALE_{axis}']

        input_variable_data_init(variable, pose_count)


def input_init_distance(input_) -> None:
    pose_count = len(input_.driver.poses)

    variable = input_.variables.internal__.add()
    variable["type"] = INPUT_VARIABLE_TYPE_TABLE['LOC_DIFF']
    variable["name"] = "var"

    variable.targets.internal__.add()
    variable.targets.internal__.add()

    input_variable_data_init(variable, pose_count)


def input_init_rotational_difference(input_) -> None:
    pose_count = len(input_.driver.poses)

    variable = input_.variables.internal__.add()
    variable["type"] = INPUT_VARIABLE_TYPE_TABLE['ROTATION_DIFF']
    variable["name"] = "var"

    variable.targets.internal__.add()
    variable.targets.internal__.add()

    input_variable_data_init(variable, pose_count)


def input_init_shape_key(input_) -> None:
    pose_count = len(input_.driver.poses)

    variable = input_.variables.internal__.add()
    variable["type"] = INPUT_VARIABLE_TYPE_TABLE["SINGLE_PROP"]
    variable["name"] = ""

    target = variable.targets.internal__.add()
    target["id_type"] = INPUT_TARGET_ID_TYPE_TABLE['KEY']

    input_variable_data_init(variable, pose_count)


def input_init_user_defined(input_: 'Input') -> None:
    pose_count = len(input_.driver.poses)

    variable = input_.variables.internal__.add()
    variable["type"] = INPUT_VARIABLE_TYPE_TABLE["SINGLE_PROP"]
    variable["name"] = "var"
    variable.targets.internal__.add()

    input_variable_data_init(variable, pose_count)


INIT_FUNCTION_TABLE: Dict[str, Callable[['Input'], None]] = {
    'LOC_DIFF': input_init_distance,
    'LOCATION': input_init_location,
    'ROTATION': input_init_rotation,
    'ROTATION_DIFF': input_init_rotational_difference,
    'SHAPE_KEY': input_init_shape_key,
    'USER_DEF': input_init_user_defined
}


def input_rotation_vars_update(input_: 'Input', mode: str, axis: str) -> None:
    variables = input_.variables

    if mode == 'EULER':
        variables[0]["is_enabled"] = False
    elif mode == 'TWIST':
        variables[0]["is_enabled"] = False
        variables[1]["is_enabled"] = axis == 'X'
        variables[2]["is_enabled"] = axis == 'Y'
        variables[3]["is_enabled"] = axis == 'Z'
    else:
        for variable in variables:
            variable["is_enabled"] = True

    if   mode == 'SWING' : mode = 'QUATERNION'
    elif mode == 'TWIST' : mode = f'SWING_TWIST_{axis}'
    elif mode == 'EULER' : mode = input_.rotation_order

    mode = INPUT_TARGET_ROTATION_MODE_TABLE[mode]
    for variable in variables:
        variable.targets[0]["rotation_mode"] = mode


def input_rotation_data_update(input_: 'Input',
                               oldmode: str,
                               oldaxis: str,
                               newmode: str,
                               newaxis: str) -> None:
    mode = f'TWIST_{newaxis}' if newmode == 'TWIST' else newmode
    prev = f'TWIST_{oldaxis}' if oldmode == 'TWIST' else oldmode
    convert = ROTATION_CONVERSION_LUT[prev][mode]
    if convert:
        variables = input_.variables
        matrix = np.array([tuple(v.data.values() for v in variables)], dtype=float)
        for vector, column in zip(matrix.T if prev != 'EULER' else matrix[1:].T,
                                matrix.T if mode != 'EULER' else matrix[1:].T):
            column[:] = convert(vector)
        if mode == 'EULER':
            matrix[0] = 0.0
        for variable, data in zip(variables, matrix):
            samples: ICollection['InputSample'] = variable.data.internal__
            samples.foreach_set("value", data)


@event_handler(InputSampleUpdateEvent)
def on_input_sample_update(event: InputSampleUpdateEvent) -> None:
    dispatch_event(InputSamplesUpdatedEvent(event.sample.input))


@event_handler(InputTargetBoneTargetUpdateEvent,
               InputTargetDataPathUpdateEvent,
               InputTargetIDTypeUpdateEvent,
               InputTargetObjectUpdateEvent,
               InputTargetRotationModeUpdateEvent,
               InputTargetTransformSpaceUpdateEvent,
               InputTargetTransformTypeUpdateEvent)
def on_input_target_property_update(event: InputTargetPropertyUpdateEvent) -> None:
    dispatch_event(InputSourcesUpdatedEvent(event.target.input))


@event_handler(InputVariableTypeUpdateEvent, InputVariableIsEnabledUpdateEvent)
def on_input_variable_property_update(event: 'InputVariablePropertyUpdateEvent') -> None:
    variable = event.variable
    if variable.type.endswith('DIFF'):
        if len(variable.targets) < 2:
            variable.targets.internal__.add()
    else:
        while len(variable.targets) > 1:
            variable.targets.internal__.remove(-1)
    dispatch_event(InputSourcesUpdatedEvent(variable.input))


@event_handler(InputVariableNameUpdateEvent)
def on_input_variable_name_update(event: InputVariableNameUpdateEvent) -> None:
    input_ = event.variable.input
    if input_.type == 'SHAPE_KEY':
        event.variable.targets[0]["data_path"] = f'key_blocks["{event.value}"].value'
        dispatch_event(InputSourcesUpdatedEvent(input_))


@event_handler(InputVariableNewEvent)
def on_input_variable_new(event: InputVariableNewEvent) -> None:
    variable = event.variable
    input_ = variable.input
    if input_.type == 'SHAPE_KEY':
        object = input_.object
        compat = {'MESH', 'LATTICE', 'CURVE'}
        target = variable.targets[0]
        target["id_type"] = INPUT_TARGET_ID_TYPE_TABLE['KEY']
        target["id"] = object.data.shape_keys if object and object.type in compat else None
        target["data_path"] = f'key_blocks["{variable.name}"].value'
    input_variable_data_init(variable, len(input_.driver.poses))
    dispatch_event(InputSamplesUpdatedEvent(input_))
    dispatch_event(InputSourcesUpdatedEvent(input_))


@event_handler(InputVariableRemovedEvent)
def on_input_variable_removed(event: InputVariableRemovedEvent) -> None:
    input_ = event.variables.input
    dispatch_event(InputSamplesUpdatedEvent(input_))
    dispatch_event(InputSourcesUpdatedEvent(input_))


@event_handler(InputBoneTargetUpdateEvent)
def on_input_bone_target_update(event: InputBoneTargetUpdateEvent) -> None:
    input_ = event.input
    if input_.type in {'LOCATION', 'ROTATION', 'SCALE'}:
        for variable in input_.variables:
            variable.targets[0]["bone_target"] = event.value
        dispatch_event(InputSourcesUpdatedEvent(input_))


@event_handler(InputObjectUpdateEvent)
def on_input_object_update(event: InputObjectUpdateEvent) -> None:
    input_ = event.input
    if input_.type in {'LOCATION', 'ROTATION', 'SCALE', 'SHAPE_KEY'}:
        for variable in input_.variables:
            variable.targets[0]["object"] = event.value
        dispatch_event(InputSourcesUpdatedEvent(input_))


def input_rotation_property_update_handler(input_: 'Input',
                                           oldmode: str,
                                           oldaxis: str,
                                           newmode: str,
                                           newaxis: str) -> None:
    input_rotation_vars_update(input_, newmode, newaxis)
    input_rotation_data_update(input_, oldmode, oldaxis, newmode, newaxis)
    dispatch_event(InputSamplesUpdatedEvent(input_))
    dispatch_event(InputSourcesUpdatedEvent(input_))


@event_handler(InputRotationAxisUpdateEvent)
def on_input_rotation_axis_update(event: InputRotationAxisUpdateEvent) -> None:
    input_ = event.input
    if input_.type == 'ROTATION':
        input_rotation_property_update_handler(input_,
                                               input_.rotation_mode,
                                               event.previous_value,
                                               input_.rotation_mode,
                                               event.value)


@event_handler(InputRotationModeUpdateEvent)
def on_input_rotation_mode_update(event: InputRotationModeUpdateEvent) -> None:
    input_ = event.input
    if input_.type == 'ROTATION':
        input_rotation_property_update_handler(input_,
                                               event.previous_value,
                                               input_.rotation_axis,
                                               event.value,
                                               input_.rotation_axis)


@event_handler(InputTransformSpaceUpdateEvent)
def on_input_transform_space_update(event: InputTransformSpaceUpdateEvent) -> None:
    input_ = event.input
    if input_.type in {'LOCATION', 'ROTATION', 'SCALE'}:
        value = INPUT_TARGET_TRANSFORM_SPACE_TABLE[event.value]
        for variable in input_.variables:
            variable.targets[0]["transform_space"] = value
        dispatch_event(InputSourcesUpdatedEvent(input_))


@event_handler(InputNewEvent)
def on_input_new(event: InputNewEvent) -> None:
    input_ = event.input
    INIT_FUNCTION_TABLE[input_.type](input_)
    dispatch_event(InputInitializedEvent(input_))


@event_handler(PoseNewEvent)
def on_pose_new(event: PoseNewEvent) -> None:
    for input_ in event.pose.driver.inputs:
        for variable in input_.variables:
            variable.data.internal__.add()["value"] = variable.value
        dispatch_event(InputSamplesUpdatedEvent(input_), immediate=True)


@event_handler(PoseRemovedEvent)
def on_pose_removed(event: PoseRemovedEvent) -> None:
    index = event.index
    for input_ in event.poses.driver.inputs:
        for variable in input_.variables:
            variable.data.internal__.remove(index)
        dispatch_event(InputSamplesUpdatedEvent(input_), immediate=True)
