'''
The input manager ensures that input data and settings are updated when input
component property values change.
'''
from typing import TYPE_CHECKING
from functools import partial
import numpy as np
from .events import event_handler
from .utils import owner_resolve
from ..lib.transform_utils import ROTATION_MODE_INDEX, TRANSFORM_TYPE_INDEX, TRANSFORM_SPACE_INDEX
from ..lib.rotation_utils import (noop,
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
                                  swing_twist_x_to_quaternion,
                                  swing_twist_y_to_quaternion,
                                  swing_twist_z_to_quaternion,
                                  swing_twist_x_to_swing_twist_y,
                                  swing_twist_x_to_swing_twist_z,
                                  swing_twist_y_to_swing_twist_x,
                                  swing_twist_y_to_swing_twist_z,
                                  swing_twist_z_to_swing_twist_x,
                                  swing_twist_z_to_swing_twist_y)
from ..api.mixins import ArrayContainer
from ..api.input_target import (INPUT_TARGET_ID_TYPE_INDEX,
                                InputTargetBoneTargetUpdateEvent,
                                InputTargetObjectUpdateEvent,
                                InputTargetRotationModeUpdateEvent,
                                InputTargetTransformSpaceUpdateEvent)
from ..api.input_variable_data_sample import InputVariableDataSampleUpdateEvent
from ..api.input_variable_data import InputVariableDataUpdateEvent
from ..api.input_variable import (InputVariableIsEnabledUpdateEvent,
                                  InputVariableNameUpdateEvent,
                                  InputVariableTypeUpdateEvent,
                                  INPUT_VARIABLE_TYPE_INDEX)
from ...dump.input_distance_matrix import InputDistanceMatrixUpdateEvent
from ..api.input import InputNameUpdateEvent, InputRotationModeChangeEvent
from ..api.inputs import InputNewEvent
from ..api.pose import PoseUpdateEvent
from ..api.poses import PoseNewEvent, PoseRemovedEvent, PoseMoveEvent
from ..api.drivers import DriverNewEvent
if TYPE_CHECKING:
    from ..api.input_variable_data_sample import RBFDriverInputVariableDataSample
    from ..api.input_variable_data import RBFDriverInputVariableData
    from ..api.input_variable import RBFDriverInputVariable
    from ...dump.input_distance_matrix import RBFDriverInputDistanceMatrix
    from ..api.input import RBFDriverInput
    from ..api.driver import RBFDriver


ROTATION_CONVERSION_LUT = {
        'AUTO': {
            'AUTO'      : noop,
            'XYZ'       : noop,
            'XZY'       : noop,
            'YXZ'       : noop,
            'YZX'       : noop,
            'ZXY'       : noop,
            'ZYX'       : noop,
            'SWING_X'   : euler_to_quaternion,
            'SWING_Y'   : euler_to_quaternion,
            'SWING_Z'   : euler_to_quaternion,
            'TWIST_X'   : partial(euler_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(euler_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(euler_to_swing_twist_z, quaternion=True),
            'QUATERNION': euler_to_quaternion,
            },
        'XYZ': {
            'AUTO'      : noop,
            'XYZ'       : noop,
            'XZY'       : noop,
            'YXZ'       : noop,
            'YZX'       : noop,
            'ZXY'       : noop,
            'ZYX'       : noop,
            'SWING_X'   : euler_to_quaternion,
            'SWING_Y'   : euler_to_quaternion,
            'SWING_Z'   : euler_to_quaternion,
            'TWIST_X'   : partial(euler_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(euler_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(euler_to_swing_twist_z, quaternion=True),
            'QUATERNION': euler_to_quaternion,
            },
        'XZY': {
            'AUTO'      : noop,
            'XYZ'       : noop,
            'XZY'       : noop,
            'YXZ'       : noop,
            'YZX'       : noop,
            'ZXY'       : noop,
            'ZYX'       : noop,
            'SWING_X'   : euler_to_quaternion,
            'SWING_Y'   : euler_to_quaternion,
            'SWING_Z'   : euler_to_quaternion,
            'TWIST_X'   : partial(euler_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(euler_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(euler_to_swing_twist_z, quaternion=True),
            'QUATERNION': euler_to_quaternion,
            },
        'YXZ': {
            'AUTO'      : noop,
            'XYZ'       : noop,
            'XZY'       : noop,
            'YXZ'       : noop,
            'YZX'       : noop,
            'ZXY'       : noop,
            'ZYX'       : noop,
            'SWING_X'   : euler_to_quaternion,
            'SWING_Y'   : euler_to_quaternion,
            'SWING_Z'   : euler_to_quaternion,
            'TWIST_X'   : partial(euler_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(euler_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(euler_to_swing_twist_z, quaternion=True),
            'QUATERNION': euler_to_quaternion,
            },
        'YZX': {
            'AUTO'      : noop,
            'XYZ'       : noop,
            'XZY'       : noop,
            'YXZ'       : noop,
            'YZX'       : noop,
            'ZXY'       : noop,
            'ZYX'       : noop,
            'SWING_X'   : euler_to_quaternion,
            'SWING_Y'   : euler_to_quaternion,
            'SWING_Z'   : euler_to_quaternion,
            'TWIST_X'   : partial(euler_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(euler_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(euler_to_swing_twist_z, quaternion=True),
            'QUATERNION': euler_to_quaternion,
            },
        'ZXY': {
            'AUTO'      : noop,
            'XYZ'       : noop,
            'XZY'       : noop,
            'YXZ'       : noop,
            'YZX'       : noop,
            'ZXY'       : noop,
            'ZYX'       : noop,
            'SWING_X'   : euler_to_quaternion,
            'SWING_Y'   : euler_to_quaternion,
            'SWING_Z'   : euler_to_quaternion,
            'TWIST_X'   : partial(euler_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(euler_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(euler_to_swing_twist_z, quaternion=True),
            'QUATERNION': euler_to_quaternion,
            },
        'ZYX': {
            'AUTO'      : noop,
            'XYZ'       : noop,
            'XZY'       : noop,
            'YXZ'       : noop,
            'YZX'       : noop,
            'ZXY'       : noop,
            'ZYX'       : noop,
            'SWING_X'   : euler_to_quaternion,
            'SWING_Y'   : euler_to_quaternion,
            'SWING_Z'   : euler_to_quaternion,
            'TWIST_X'   : partial(euler_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(euler_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(euler_to_swing_twist_z, quaternion=True),
            'QUATERNION': euler_to_quaternion,
            },
        'SWING_X': {
            'AUTO'      : quaternion_to_euler,
            'XYZ'       : quaternion_to_euler,
            'XZY'       : quaternion_to_euler,
            'YXZ'       : quaternion_to_euler,
            'YZX'       : quaternion_to_euler,
            'ZXY'       : quaternion_to_euler,
            'ZYX'       : quaternion_to_euler,
            'SWING_X'   : noop,
            'SWING_Y'   : noop,
            'SWING_Z'   : noop,
            'TWIST_X'   : partial(quaternion_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(quaternion_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(quaternion_to_swing_twist_z, quaternion=True),
            'QUATERNION': noop,
            },
        'SWING_Y': {
            'AUTO'      : quaternion_to_euler,
            'XYZ'       : quaternion_to_euler,
            'XZY'       : quaternion_to_euler,
            'YXZ'       : quaternion_to_euler,
            'YZX'       : quaternion_to_euler,
            'ZXY'       : quaternion_to_euler,
            'ZYX'       : quaternion_to_euler,
            'SWING_X'   : noop,
            'SWING_Y'   : noop,
            'SWING_Z'   : noop,
            'TWIST_X'   : partial(quaternion_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(quaternion_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(quaternion_to_swing_twist_z, quaternion=True),
            'QUATERNION': noop,
            },
        'SWING_Z': {
            'AUTO'      : quaternion_to_euler,
            'XYZ'       : quaternion_to_euler,
            'XZY'       : quaternion_to_euler,
            'YXZ'       : quaternion_to_euler,
            'YZX'       : quaternion_to_euler,
            'ZXY'       : quaternion_to_euler,
            'ZYX'       : quaternion_to_euler,
            'SWING_X'   : noop,
            'SWING_Y'   : noop,
            'SWING_Z'   : noop,
            'TWIST_X'   : partial(quaternion_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(quaternion_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(quaternion_to_swing_twist_z, quaternion=True),
            'QUATERNION': noop,
            },
        'TWIST_X': {
            'AUTO'      : swing_twist_x_to_euler,
            'XYZ'       : swing_twist_x_to_euler,
            'XZY'       : swing_twist_x_to_euler,
            'YXZ'       : swing_twist_x_to_euler,
            'YZX'       : swing_twist_x_to_euler,
            'ZXY'       : swing_twist_x_to_euler,
            'ZYX'       : swing_twist_x_to_euler,
            'SWING_X'   : swing_twist_x_to_quaternion,
            'SWING_Y'   : swing_twist_x_to_quaternion,
            'SWING_Z'   : swing_twist_x_to_quaternion,
            'TWIST_X'   : noop,
            'TWIST_Y'   : swing_twist_x_to_swing_twist_y,
            'TWIST_Z'   : swing_twist_x_to_swing_twist_z,
            'QUATERNION': swing_twist_x_to_quaternion,
            },
        'TWIST_Y': {
            'AUTO'      : swing_twist_y_to_euler,
            'XYZ'       : swing_twist_y_to_euler,
            'XZY'       : swing_twist_y_to_euler,
            'YXZ'       : swing_twist_y_to_euler,
            'YZX'       : swing_twist_y_to_euler,
            'ZXY'       : swing_twist_y_to_euler,
            'ZYX'       : swing_twist_y_to_euler,
            'SWING_X'   : swing_twist_y_to_quaternion,
            'SWING_Y'   : swing_twist_y_to_quaternion,
            'SWING_Z'   : swing_twist_y_to_quaternion,
            'TWIST_X'   : swing_twist_y_to_swing_twist_x,
            'TWIST_Y'   : noop,
            'TWIST_Z'   : swing_twist_y_to_swing_twist_z,
            'QUATERNION': swing_twist_y_to_quaternion,
            },
        'TWIST_Z': {
            'AUTO'      : swing_twist_z_to_euler,
            'XYZ'       : swing_twist_z_to_euler,
            'XZY'       : swing_twist_z_to_euler,
            'YXZ'       : swing_twist_z_to_euler,
            'YZX'       : swing_twist_z_to_euler,
            'ZXY'       : swing_twist_z_to_euler,
            'ZYX'       : swing_twist_z_to_euler,
            'SWING_X'   : swing_twist_z_to_quaternion,
            'SWING_Y'   : swing_twist_z_to_quaternion,
            'SWING_Z'   : swing_twist_z_to_quaternion,
            'TWIST_X'   : swing_twist_z_to_swing_twist_x,
            'TWIST_Y'   : swing_twist_z_to_swing_twist_y,
            'TWIST_Z'   : noop,
            'QUATERNION': swing_twist_z_to_quaternion,
            },
        'QUATERNION': {
            'AUTO'      : quaternion_to_euler,
            'XYZ'       : quaternion_to_euler,
            'XZY'       : quaternion_to_euler,
            'YXZ'       : quaternion_to_euler,
            'YZX'       : quaternion_to_euler,
            'ZXY'       : quaternion_to_euler,
            'ZYX'       : quaternion_to_euler,
            'SWING_X'   : noop,
            'SWING_Y'   : noop,
            'SWING_Z'   : noop,
            'TWIST_X'   : partial(quaternion_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(quaternion_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(quaternion_to_swing_twist_z, quaternion=True),
            'QUATERNION': noop,
            }
        }


def input_variable_data_init(data: 'RBFDriverInputVariableData',
                             default_value: float,
                             pose_count: int,
                             normalize: bool) -> None:
    samples = data.data__internal__
    
    for index in range(pose_count):
        sample = samples.add()
        sample["index"] = index
        sample["value"] = default_value

    if normalize:
        data["is_normalized"] = True
        norm = data["norm"] = np.linalg.norm([default_value] * pose_count)
        if norm != 0.0:
            for sample in samples:
                sample["value_normalized"] = sample.value / norm
    else:
        data["is_normalized"] = False


def input_init__generic(input: 'RBFDriverInput', pose_count: int) -> None:
    '''
    Initializes a user-defined input
    '''
    assert pose_count >= 1

    variable = input.variables.collection__internal__.add()
    variable["type"] = 'SINGLE_PROP'
    variable["name"] = ""
    variable["default_value"] = 0.0

    targets = variable.targets
    targets["length__internal__"] = 1
    targets.collection__internal__.add()

    input_variable_data_init(variable.data, 0.0, pose_count, True)


def input_init__location(input: 'RBFDriverInput', pose_count: int) -> None:
    '''
    Initializes a location input
    '''
    assert pose_count >= 1

    for axis in "xyz":
        variable = input.variables.collection__internal__.add()
        variable["type"] = INPUT_VARIABLE_TYPE_INDEX['TRANSFORMS']
        variable["name"] = axis
        variable["default_value"] = 0.0

        targets = variable.targets
        targets["length__internal__"] = 1

        target = targets.collection__internal__.add()
        target["transform_space"] = TRANSFORM_SPACE_INDEX['LOCAL_SPACE']
        target["transform_type"] = TRANSFORM_TYPE_INDEX[f'LOC_{axis.upper()}']

        input_variable_data_init(variable.data, 0.0, pose_count, False)


def input_init__rotation(input: 'RBFDriverInput', pose_count: int) -> None:
    '''
    Initializes a rotation input
    '''
    assert pose_count >= 1

    for axis, value in zip("wxyz", (1.0, 0.0, 0.0, 0.0)):
        variable = input.variables.collection__internal__.add()
        variable["type"] = INPUT_VARIABLE_TYPE_INDEX['TRANSFORMS']
        variable["name"] = axis
        variable["default_value"] = value

        targets = variable.targets
        targets["length__internal__"] = 1

        target = targets.collection__internal__.add()
        target["rotation_mode"] = ROTATION_MODE_INDEX['QUATERNION']
        target["transform_space"] = TRANSFORM_SPACE_INDEX['LOCAL_SPACE']
        target["transform_type"] = TRANSFORM_TYPE_INDEX[f'ROT_{axis.upper()}']

        input_variable_data_init(variable.data, value, pose_count, False)


def input_init__scale(input: 'RBFDriverInput', pose_count: int) -> None:
    '''
    Initializes a scale input
    '''
    assert pose_count >= 1

    for axis in "xyz":
        variable = input.variables.collection__internal__.add()
        variable["type"] = INPUT_VARIABLE_TYPE_INDEX['TRANSFORMS']
        variable["name"] = axis
        variable["default_value"] = 0.0

        targets = variable.targets
        targets["length__internal__"] = 1

        target = targets.collection__internal__.add()
        target["transform_space"] = TRANSFORM_SPACE_INDEX['LOCAL_SPACE']
        target["transform_type"] = TRANSFORM_TYPE_INDEX[f'SCALE_{axis.upper()}']

        input_variable_data_init(variable.data, 1.0, pose_count, False)


def input_init__bbone(input: 'RBFDriverInput', pose_count: int) -> None:
    '''
    Initializes a bbone input
    '''
    assert pose_count >= 1

    for name, path, value in [
            ("curveinx", "bbone_curveinx", 0.0),
            ("curveinz", "bbone_curveinz", 0.0),
            ("curveoutx", "bbone_curveoutx", 0.0),
            ("curveoutz", "bbone_curveoutz", 0.0),
            ("easein", "bbone_easein", 0.0),
            ("easeout", "bbone_easeout", 0.0),
            ("rollin", "bbone_rollin", 0.0),
            ("rollout", "bbone_rollout", 0.0),
            ("scaleinx", "bbone_scalein[0]", 1.0),
            ("scaleiny", "bbone_scalein[1]", 1.0),
            ("scaleinz", "bbone_scalein[2]", 1.0),
            ("scaleoutx", "bbone_scaleout[0]", 1.0),
            ("scaleouty", "bbone_scaleout[1]", 1.0),
            ("scaleoutz", "bbone_scaleout[2]", 1.0)
        ]:
        variable = input.variables.collection__internal__.add()
        variable["type"] = INPUT_VARIABLE_TYPE_INDEX['SINGLE_PROP']
        variable["name"] = name
        variable["default_value"] = value

        targets = variable.targets
        targets["length__internal__"] = 1

        target = targets.collection__internal__.add()
        target["id_type"] = INPUT_TARGET_ID_TYPE_INDEX['ARMATURE']
        target["data_path"] = f'pose.bones[""].{path}'

        input_variable_data_init(variable.data, value, pose_count, True)


def input_init__shape_key(input: 'RBFDriverInput', pose_count: int) -> None:
    '''
    Initializes a shape key input
    '''
    assert pose_count >= 1

    variable = input.variables.collection__internal__.add()
    variable["type"] = 'SINGLE_PROP'
    variable["name"] = ""
    variable["default_value"] = 0.0

    targets = variable.targets
    targets["length__internal__"] = 1

    target = targets.collection__internal__.add()
    target["id_type"] = 'KEY'

    input_variable_data_init(variable.data, 0.0, pose_count, False)


def input_init(input: 'RBFDriverInput', pose_count: int) -> None:
    '''
    Initializes an input
    '''
    type: str = input.type
    if type == 'LOCATION'  : return input_init__location(input, pose_count)
    if type == 'ROTATION'  : return input_init__rotation(input, pose_count)
    if type == 'SCALE'     : return input_init__scale(input, pose_count)
    if type == 'BBONE'     : return input_init__bbone(input, pose_count)
    if type == 'SHAPE_KEY' : return input_init__shape_key(input, pose_count)
    input_init__generic(input, pose_count)


@event_handler(InputTargetBoneTargetUpdateEvent)
def on_input_target_bone_target_updated(event: InputTargetBoneTargetUpdateEvent) -> None:
    '''
    Synchronizes the bone target setting across input targets and updates input target
    data paths for bbone inputs
    '''
    input: 'RBFDriverInput' = owner_resolve(event.target, ".variables")
    value = event.value

    if input.type in {'LOCATION', 'ROTATION', 'SCALE', 'BBONE'}:
        for variable in input.variables:
            variable.targets[0]["bone_target"] = value

    if input.type == 'BBONE':
        for variable in input.variables:
            variable.targets[0]["data_path"] = f'pose.bones["{value}"].{variable.name}'


@event_handler(InputTargetObjectUpdateEvent)
def on_input_target_object_updated(event: InputTargetObjectUpdateEvent) -> None:
    '''
    Synchronizes the target object across input targets
    '''
    input: 'RBFDriverInput' = owner_resolve(event.target, ".variables")
    value = event.value

    if input.type in {'LOCATION', 'ROTATION', 'SCALE', 'BBONE', 'SHAPE_KEY'}:
        for variable in input.variables:
            variable.targets[0]["object"] = value


@event_handler(InputTargetRotationModeUpdateEvent)
def on_input_target_rotation_mode_updated(event: InputTargetRotationModeUpdateEvent) -> None:
    '''
    Sycnrhonizes the rotation mode across input targets for rotation inputs
    '''
    input: 'RBFDriverInput' = owner_resolve(event.target, ".variables")
    value = event.value

    if input.type == 'ROTATION':
        for variable in input.variables:
            variable.targets[0]["rotation_mode"] = value


@event_handler(InputTargetTransformSpaceUpdateEvent)
def on_input_target_transform_space_update(event: InputTargetTransformSpaceUpdateEvent) -> None:
    '''
    Synchronizes the transform space across input targets for transform inputs
    '''
    input: 'RBFDriverInput' = owner_resolve(event.target, ".variables")
    value = TRANSFORM_SPACE_INDEX[event.value]

    if input.type in {'LOCATION', 'ROTATION', 'SCALE'}:
        for variable in input.variables:
            variable.targets[0]["transform_space"] = value


@event_handler(InputVariableDataSampleUpdateEvent)
def on_input_variable_data_sample_update(event: InputVariableDataSampleUpdateEvent) -> None:
    '''
    Propagates an input variable data sample update to the parent data structure to
    ensure normalization occurs when needed.
    '''
    data: 'RBFDriverInputVariableData' = owner_resolve(event.sample, ".data.")
    data.update()


@event_handler(InputVariableDataUpdateEvent)
def on_input_variable_data_update(event: InputVariableDataUpdateEvent) -> None:
    '''
    Propagates an input variable data update to the input distance matrix
    '''
    matrix: 'RBFDriverInputDistanceMatrix' = owner_resolve(event.data, ".variables").distance.matrix
    matrix.update()


@event_handler(InputVariableIsEnabledUpdateEvent)
def on_input_variable_is_enabled_update(event: InputVariableIsEnabledUpdateEvent) -> None:
    '''
    Updates the input distance matrix when an input variable is enabled/disabled
    '''
    matrix: 'RBFDriverInputDistanceMatrix' = owner_resolve(event.variable, ".variables").distance.matrix
    matrix.update()


@event_handler(InputVariableNameUpdateEvent)
def on_input_variable_name_update(event: InputVariableNameUpdateEvent) -> None:
    '''
    Updates a shape key input target's data path according to the input variable's name
    '''
    input: 'RBFDriverInput' = owner_resolve(event.variable, ".variables")
    if input.type == 'SHAPE_KEY':
        event.variable.targets[0]["data_path"] = f'key_blocks["{event.value}"].value'


@event_handler(InputVariableTypeUpdateEvent)
def on_input_variable_type_update(event: InputVariableTypeUpdateEvent) -> None:
    '''
    Ensures the input variable has the correct number of targets
    '''
    if event.variable.type.endswith('DIFF'):
        if len(event.variable.targets) < 2:
            event.variable.targets['length__internal__'] = 2
            event.variable.targets.collection__internal__.add()
    else:
        event.variable.targets["length__internal__"] = 1


@event_handler(InputNameUpdateEvent)
def on_input_name_update(event: InputNameUpdateEvent) -> None:
    '''
    Ensures the input's name is unique
    '''
    driver: 'RBFDriver' = owner_resolve(event.input, ".inputs")
    names = [item.name for item in driver.inputs if item != event.input]
    index = 0
    value = event.value
    while value in names:
        index += 1
        value = f'{event.value}.{str(index).zfill(3)}'
    event.input["name"] = value


@event_handler(InputRotationModeChangeEvent)
def on_input_rotation_mode_change(event: InputRotationModeChangeEvent) -> None:
    '''
    Transforms variable data for rotation inputs to match the input's rotation mode
    and updates the input distance matrix
    '''
    if event.input.type == 'ROTATION':

        value = event.value
        cache = event.previous_value
        input = event.input
        variables = input.variables

        if len(value) < 4:
            variables[0]["enabled"] = False
        elif value.startswith('TWIST'):
            axis = value[-1]
            variables[0]["enabled"] = False
            variables[1]["enabled"] = axis == 'X'
            variables[2]["enabled"] = axis == 'Y'
            variables[3]["enabled"] = axis == 'Z'
        else:
            for variable in variables:
                variable["enabled"] = True

        convert = ROTATION_CONVERSION_LUT[cache][value]

        matrix = np.array([
            tuple(scalar.value for scalar in variable.data) for variable in variables
            ], dtype=np.float)
        
        for vector, column in zip(matrix.T if len(cache) > 4 else matrix[1:].T,
                                  matrix.T if len(value) > 4 else matrix[1:].T):
            column[:] = convert(vector)

        if len(value) < 5:
            matrix[0] = 0.0

        for variable, data in zip(variables, matrix):
            variable.data.__init__(data, value != 'QUATERNION')

        matrix: 'RBFDriverInputDistanceMatrix' = input.distance.matrix
        matrix.update()


def input_distance_pose_radii_update(radii: 'ArrayContainer', matrix: np.ndarray) -> None:
    data = []

    if len(matrix):
        matrix = matrix.view(np.ma.MaskedArray)
        matrix.mask = np.identity(len(matrix), dtype=bool)
        for row in matrix:
            row = row.compressed()
            data.append(0.0 if len(row) == 0 else np.min(row))

    radii.__init__(data)


@event_handler(InputDistanceMatrixUpdateEvent)
def on_input_distance_pose_matrix_update(event: InputDistanceMatrixUpdateEvent) -> None:
    '''
    Updates input pose radii
    '''
    radii: 'ArrayContainer' = owner_resolve(event.matrix, ".").pose_radii
    input_distance_pose_radii_update(radii, event.matrix.to_array())


@event_handler(InputNewEvent)
def on_input_new(event: InputNewEvent) -> None:
    '''
    Initializes input variable data for each pose
    '''
    driver: 'RBFDriver' = owner_resolve(event.input, ".inputs")
    input_init(event.input, len(driver.poses))

    matrix: 'RBFDriverInputDistanceMatrix' = event.input.distance.matrix
    matrix.update(propagate=False)

    input_distance_pose_radii_update(event.input.distance.pose_radii, matrix.to_array())


@event_handler(PoseNewEvent)
def on_pose_new(event: PoseNewEvent) -> None:
    '''
    Appends input variable data when a new pose is added. Note that the update is not
    propagated to the RBF driver's distance matrix because the data manager handles
    that.
    '''
    driver: 'RBFDriver' = owner_resolve(event.pose, ".poses")

    input: 'RBFDriverInput'
    for input in driver.inputs:

        variable: 'RBFDriverInputVariable'
        for variable in input.variables:
            data: 'RBFDriverInputVariableData' = variable.data

            item: 'RBFDriverInputVariableDataSample' = data.data__internal__.add()
            item["index"] = len(data) - 1
            item["value"] = variable.value

            data.update(propagate=False)

        matrix: 'RBFDriverInputDistanceMatrix' = input.distance.matrix
        matrix.update(propagate=False)

        # TODO are input distance pose radii still in use???
        input_distance_pose_radii_update(input.distance.pose_radii, matrix.to_array())


@event_handler(PoseRemovedEvent)
def on_pose_removed(event: PoseRemovedEvent) -> None:
    '''
    Removes input variable data when a pose is removed. Note that the update is not
    propagated to the RBF driver's distance matrix because the data manager handles
    that.
    '''
    driver: 'RBFDriver' = owner_resolve(event.poses, ".")

    input: 'RBFDriverInput'
    for input in driver.inputs:

        variable: 'RBFDriverInputVariable'
        for variable in input.variables:
            data: 'RBFDriverInputVariableData' = variable.data
            data.data__internal__.remove(event.index)
            data.update(propagate=False)

        matrix: 'RBFDriverInputDistanceMatrix' = input.distance.matrix
        matrix.update(propagate=False)

        input_distance_pose_radii_update(input.distance.pose_radii, matrix.to_array())


@event_handler(PoseUpdateEvent)
def on_pose_update(event: PoseUpdateEvent) -> None:
    '''
    Updates input variable data when a pose is updated. Note that the update is not
    propagated to the RBF driver's distance matrix because the data manager handles
    that.
    '''
    driver: 'RBFDriver' = owner_resolve(event.pose, ".poses")

    index = driver.poses.index(event.pose)
    
    for input in driver.inputs:
        for variable in input.variables:
            data: 'RBFDriverInputVariableData' = variable.data
            data[index]["value"] = variable.value
            data.update(propagate=False)

        matrix: 'RBFDriverInputDistanceMatrix' = input.distance.matrix
        matrix.update(propagate=False)

        input_distance_pose_radii_update(input.distance.pose_radii, matrix.to_array())


@event_handler(PoseMoveEvent)
def on_pose_move(event: PoseMoveEvent) -> None:
    '''
    Moves input variable data when a pose is moved. Note that the update is not
    propagated to the RBF driver's distance matrix because the data manager handles
    that.
    '''
    driver: 'RBFDriver' = owner_resolve(event.pose, ".poses")

    for input in driver.inputs:
        for variable in input.variables:
            data: 'RBFDriverInputVariableData' = variable.data
            data.data__internal__.move(event.from_index, event.to_index)

        matrix: 'RBFDriverInputDistanceMatrix' = input.distance.matrix
        matrix.update(propagate=False)

        input_distance_pose_radii_update(input.distance.pose_radii, matrix.to_array())


@event_handler(DriverNewEvent)
def on_driver_new(event: DriverNewEvent) -> None:
    '''
    Clones inputs for new symmetrical RBF drivers
    '''
    if event.driver.has_symmetry_target:
        # TODO clone inputs for symmetrical driver
        raise NotImplementedError()
