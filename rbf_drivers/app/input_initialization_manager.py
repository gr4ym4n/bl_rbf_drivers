
from typing import TYPE_CHECKING
import numpy as np
from .events import event_handler
from .utils import owner_resolve
from ..api.input_target import INPUT_TARGET_ID_TYPE_INDEX
from ..api.input_variable import INPUT_VARIABLE_TYPE_INDEX
from ..api.inputs import InputNewEvent
from ..api.drivers import DriverNewEvent
from ..lib.transform_utils import ROTATION_MODE_INDEX, TRANSFORM_TYPE_INDEX, TRANSFORM_SPACE_INDEX
if TYPE_CHECKING:
    from ..api.input_variable_data import RBFDriverInputVariableData
    from ..api.input import RBFDriverInput
    from ..api.driver import RBFDriver


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

    for axis in "XYZ":
        variable = input.variables.collection__internal__.add()
        variable["type"] = INPUT_VARIABLE_TYPE_INDEX['TRANSFORMS']
        variable["name"] = axis
        variable["default_value"] = 0.0

        targets = variable.targets
        targets["length__internal__"] = 1

        target = targets.collection__internal__.add()
        target["transform_space"] = TRANSFORM_SPACE_INDEX['LOCAL_SPACE']
        target["transform_type"] = TRANSFORM_TYPE_INDEX[f'LOC_{axis}']

        input_variable_data_init(variable.data, 0.0, pose_count, False)


def input_init__rotation(input: 'RBFDriverInput', pose_count: int) -> None:
    '''
    Initializes a rotation input
    '''
    assert pose_count >= 1

    for axis, value in zip("WXYZ", (1.0, 0.0, 0.0, 0.0)):
        variable = input.variables.collection__internal__.add()
        variable["type"] = INPUT_VARIABLE_TYPE_INDEX['TRANSFORMS']
        variable["name"] = axis
        variable["default_value"] = value

        targets = variable.targets
        targets["length__internal__"] = 1

        target = targets.collection__internal__.add()
        target["rotation_mode"] = ROTATION_MODE_INDEX['QUATERNION']
        target["transform_space"] = TRANSFORM_SPACE_INDEX['LOCAL_SPACE']
        target["transform_type"] = TRANSFORM_TYPE_INDEX[f'ROT_{axis}']

        input_variable_data_init(variable.data, value, pose_count, False)


def input_init__scale(input: 'RBFDriverInput', pose_count: int) -> None:
    '''
    Initializes a scale input
    '''
    assert pose_count >= 1

    for axis in "XYZ":
        variable = input.variables.collection__internal__.add()
        variable["type"] = INPUT_VARIABLE_TYPE_INDEX['TRANSFORMS']
        variable["name"] = axis
        variable["default_value"] = 0.0

        targets = variable.targets
        targets["length__internal__"] = 1

        target = targets.collection__internal__.add()
        target["transform_space"] = TRANSFORM_SPACE_INDEX['LOCAL_SPACE']
        target["transform_type"] = TRANSFORM_TYPE_INDEX[f'SCALE_{axis}']

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


@event_handler(InputNewEvent)
def on_input_new(event: InputNewEvent) -> None:
    '''
    Initializes input variable data for each pose
    '''
    input = event.input
    driver: 'RBFDriver' = owner_resolve(input, ".inputs")
    type: str = input.type
    pose_count = len(driver.poses)

    if type == 'LOCATION'  : return input_init__location(input, pose_count)
    if type == 'ROTATION'  : return input_init__rotation(input, pose_count)
    if type == 'SCALE'     : return input_init__scale(input, pose_count)
    if type == 'BBONE'     : return input_init__bbone(input, pose_count)
    if type == 'SHAPE_KEY' : return input_init__shape_key(input, pose_count)

    input_init__generic(input, pose_count)


@event_handler(DriverNewEvent)
def on_driver_new(event: DriverNewEvent) -> None:
    '''
    Clones inputs for new symmetrical RBF drivers
    '''
    if event.driver.has_symmetry_target:
        # TODO clone inputs for symmetrical driver
        raise NotImplementedError()