
from typing import TYPE_CHECKING
import numpy as np
from .events import event_handler
from .utils import owner_resolve
from ..api.input_variable import INPUT_VARIABLE_TYPE_TABLE
from ..api.inputs import InputNewEvent
from ..lib.transform_utils import ROTATION_MODE_TABLE, TRANSFORM_TYPE_TABLE, TRANSFORM_SPACE_TABLE
if TYPE_CHECKING:
    from ..api.input_variable_data import RBFDriverInputVariableData
    from ..api.input import RBFDriverInput


def input_variable_data_init(data: 'RBFDriverInputVariableData',
                             default_value: float,
                             pose_count: int,
                             normalize: bool) -> None:
    '''
    Initializes input variable data
    '''
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


def input_init__location(input: 'RBFDriverInput', pose_count: int) -> None:
    '''
    Initializes a location input
    '''
    assert pose_count >= 1

    input["transform_space"] = TRANSFORM_SPACE_TABLE['LOCAL_SPACE']

    for axis in "XYZ":
        variable = input.variables.collection__internal__.add()
        variable["type"] = INPUT_VARIABLE_TYPE_TABLE['TRANSFORMS']
        variable["name"] = axis
        variable["default_value"] = 0.0

        targets = variable.targets
        targets["length__internal__"] = 1

        target = targets.collection__internal__.add()
        target["transform_space"] = TRANSFORM_SPACE_TABLE['LOCAL_SPACE']
        target["transform_type"] = TRANSFORM_TYPE_TABLE[f'LOC_{axis}']
        targets.collection__internal__.add()

        input_variable_data_init(variable.data, 0.0, pose_count, False)


def input_init__rotation(input: 'RBFDriverInput', pose_count: int) -> None:
    '''
    Initializes a rotation input
    '''
    assert pose_count >= 1

    input["transform_space"] = TRANSFORM_SPACE_TABLE['LOCAL_SPACE']

    for axis, value in zip("WXYZ", (1.0, 0.0, 0.0, 0.0)):
        variable = input.variables.collection__internal__.add()
        variable["type"] = INPUT_VARIABLE_TYPE_TABLE['TRANSFORMS']
        variable["name"] = axis
        variable["default_value"] = value

        targets = variable.targets
        targets["length__internal__"] = 1

        target = targets.collection__internal__.add()
        target["rotation_mode"] = ROTATION_MODE_TABLE['QUATERNION']
        target["transform_space"] = TRANSFORM_SPACE_TABLE['LOCAL_SPACE']
        target["transform_type"] = TRANSFORM_TYPE_TABLE[f'ROT_{axis}']
        targets.collection__internal__.add()

        input_variable_data_init(variable.data, value, pose_count, False)


def input_init__scale(input: 'RBFDriverInput', pose_count: int) -> None:
    '''
    Initializes a scale input
    '''
    assert pose_count >= 1

    input["transform_space"] = TRANSFORM_SPACE_TABLE['LOCAL_SPACE']

    for axis in "XYZ":
        variable = input.variables.collection__internal__.add()
        variable["type"] = INPUT_VARIABLE_TYPE_TABLE['TRANSFORMS']
        variable["name"] = axis
        variable["default_value"] = 0.0

        targets = variable.targets
        targets["length__internal__"] = 1

        target = targets.collection__internal__.add()
        target["transform_space"] = TRANSFORM_SPACE_TABLE['LOCAL_SPACE']
        target["transform_type"] = TRANSFORM_TYPE_TABLE[f'SCALE_{axis}']
        targets.collection__internal__.add()

        input_variable_data_init(variable.data, 1.0, pose_count, False)


def input_init__rotation_diff(input: 'RBFDriverInput', pose_count: int) -> None:
    assert pose_count >= 1

    variable = input.variables.collection__internal__.add()
    variable["type"] = INPUT_VARIABLE_TYPE_TABLE['ROTATION_DIFF']
    variable["name"] = "var"
    variable["default_value"] = 0.0

    targets = variable.targets
    targets["length__internal__"] = 2

    targets.collection__internal__.add()
    targets.collection__internal__.add()

    input_variable_data_init(variable.data, 0.0, pose_count, False)


def input_init__loc_diff(input: 'RBFDriverInput', pose_count: int) -> None:
    assert pose_count >= 1

    variable = input.variables.collection__internal__.add()
    variable["type"] = INPUT_VARIABLE_TYPE_TABLE['LOC_DIFF']
    variable["name"] = "var"
    variable["default_value"] = 0.0

    targets = variable.targets
    targets["length__internal__"] = 2

    targets.collection__internal__.add()
    targets.collection__internal__.add()

    input_variable_data_init(variable.data, 0.0, pose_count, False)


def input_init__shape_key(input: 'RBFDriverInput', pose_count: int) -> None:
    '''
    Initializes a shape key input
    '''
    assert pose_count >= 1

    variable = input.variables.collection__internal__.add()
    variable["type"] = INPUT_VARIABLE_TYPE_TABLE['SINGLE_PROP']
    variable["name"] = ""
    variable["default_value"] = 0.0

    targets = variable.targets
    targets["length__internal__"] = 1

    target = targets.collection__internal__.add()
    target["id_type"] = 'KEY'
    targets.collection__internal__.add()

    input_variable_data_init(variable.data, 0.0, pose_count, False)


def input_init__user_def(input: 'RBFDriverInput', pose_count: int) -> None:
    '''
    Initializes a user-defined input
    '''
    assert pose_count >= 1

    variable = input.variables.collection__internal__.add()
    variable["type"] = INPUT_VARIABLE_TYPE_TABLE['SINGLE_PROP']
    variable["name"] = "var"
    variable["default_value"] = 0.0

    targets = variable.targets
    targets["length__internal__"] = 1
    targets.collection__internal__.add()
    targets.collection__internal__.add()

    input_variable_data_init(variable.data, 0.0, pose_count, True)


INPUT_INIT_FUNCS = {
    'LOCATION'     : input_init__location,
    'ROTATION'     : input_init__rotation,
    'SCALE'        : input_init__scale,
    'ROTATION_DIFF': input_init__rotation_diff,
    'LOC_DIFF'     : input_init__loc_diff,
    'SHAPE_KEY'    : input_init__shape_key,
    'USER_DEF'     : input_init__user_def
    }


@event_handler(InputNewEvent)
def on_input_new(event: InputNewEvent) -> None:
    '''
    Initializes input variable data for each pose
    '''
    input = event.input
    INPUT_INIT_FUNCS[input.type](input, len(owner_resolve(input, ".inputs").poses))
