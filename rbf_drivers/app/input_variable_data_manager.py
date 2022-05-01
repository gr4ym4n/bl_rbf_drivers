'''
Note that input variable data initialization is handled by the input inititialization manager
'''

from typing import Iterable, Iterator, Tuple, TYPE_CHECKING
from itertools import chain
from operator import attrgetter
from functools import partial
import numpy as np
from .events import event_handler
from .utils import owner_resolve
from ..api.input import InputRotationModeChangeEvent
from ..api.pose import PoseUpdateEvent
from ..api.poses import PoseMoveEvent, PoseNewEvent, PoseRemovedEvent
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
if TYPE_CHECKING:
    from ..api.input_variable_data import RBFDriverInputVariableData
    from ..api.input_variable import RBFDriverInputVariable
    from ..api.input import RBFDriverInput

ROTATION_CONVERSION_LUT = {
        'EULER': {
            'EULER'     : noop,
            'SWING'     : euler_to_quaternion,
            'TWIST_X'   : partial(euler_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(euler_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(euler_to_swing_twist_z, quaternion=True),
            'QUATERNION': euler_to_quaternion,
            },
        'SWING': {
            'EULER'     : quaternion_to_euler,
            'SWING'     : noop,
            'TWIST_X'   : partial(quaternion_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(quaternion_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(quaternion_to_swing_twist_z, quaternion=True),
            'QUATERNION': noop,
            },
        'TWIST_X': {
            'EULER'     : swing_twist_x_to_euler,
            'SWING'     : swing_twist_x_to_quaternion,
            'TWIST_X'   : noop,
            'TWIST_Y'   : swing_twist_x_to_swing_twist_y,
            'TWIST_Z'   : swing_twist_x_to_swing_twist_z,
            'QUATERNION': swing_twist_x_to_quaternion,
            },
        'TWIST_Y': {
            'EULER'     : swing_twist_y_to_euler,
            'SWING'     : swing_twist_y_to_quaternion,
            'TWIST_X'   : swing_twist_y_to_swing_twist_x,
            'TWIST_Y'   : noop,
            'TWIST_Z'   : swing_twist_y_to_swing_twist_z,
            'QUATERNION': swing_twist_y_to_quaternion,
            },
        'TWIST_Z': {
            'EULER'     : swing_twist_z_to_euler,
            'SWING'     : swing_twist_z_to_quaternion,
            'TWIST_X'   : swing_twist_z_to_swing_twist_x,
            'TWIST_Y'   : swing_twist_z_to_swing_twist_y,
            'TWIST_Z'   : noop,
            'QUATERNION': swing_twist_z_to_quaternion,
            },
        'QUATERNION': {
            'EULER'     : quaternion_to_euler,
            'SWING'     : noop,
            'TWIST_X'   : partial(quaternion_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(quaternion_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(quaternion_to_swing_twist_z, quaternion=True),
            'QUATERNION': noop,
            }
        }

variables = attrgetter("variables")
data = attrgetter("data")


def variable_state(variable: 'RBFDriverInputVariable') -> Tuple['RBFDriverInputVariableData', float]:
    return variable.data, variable.value


def variable_chain(inputs: Iterable['RBFDriverInput']) -> Iterator['RBFDriverInputVariable']:
    return chain(*tuple(map(variables, inputs)))


def variable_data_chain(inputs: Iterable['RBFDriverInput']) -> Iterator['RBFDriverInputVariableData']:
    return map(data, variable_chain(inputs))


def variable_state_chain(inputs: Iterable['RBFDriverInput']) -> Iterator[Tuple['RBFDriverInputVariableData', float]]:
    return map(variable_state, variable_chain(inputs))


@event_handler(InputRotationModeChangeEvent)
def on_input_rotation_mode_change(event: InputRotationModeChangeEvent) -> None:
    '''
    Transforms variable data for rotation inputs to match the input's rotation mode
    '''
    if event.input.type == 'ROTATION':

        value = event.value
        cache = event.previous_value
        input = event.input
        variables = input.variables

        if value == 'EULER':
            variables[0]["is_enabled"] = False
        elif value == 'TWIST':
            axis = event.input.rotation_axis
            value = f'TWIST_{axis}'
            variables[0]["is_enabled"] = False
            variables[1]["is_enabled"] = axis == 'X'
            variables[2]["is_enabled"] = axis == 'Y'
            variables[3]["is_enabled"] = axis == 'Z'
        else:
            for variable in variables:
                variable["is_enabled"] = True

        if cache == 'TWIST':
            cache = f'TWIST_{event.input.rotation_axis}'

        if value != cache:
            convert = ROTATION_CONVERSION_LUT[cache][value]

            matrix = np.array([
                tuple(scalar.value for scalar in variable.data) for variable in variables
                ], dtype=np.float)
            
            for vector, column in zip(matrix.T if cache != 'EULER' else matrix[1:].T,
                                      matrix.T if value != 'EULER' else matrix[1:].T):
                column[:] = convert(vector)

            if value == 'EULER':
                matrix[0] = 0.0

            for variable, data in zip(variables, matrix):
                variable.data.__init__(data, False)


@event_handler(PoseMoveEvent)
def on_pose_move(event: PoseMoveEvent) -> None:
    '''
    Moves input variable data when a pose is moved.
    '''
    a, b = event.from_index, event.to_index
    for data in variable_data_chain(owner_resolve(event.pose, ".poses").inputs):
        data.data__internal__.move(a, b)


@event_handler(PoseNewEvent)
def on_pose_new(event: PoseNewEvent) -> None:
    '''
    Appends input variable data when a new pose is added.
    '''
    for data, value in variable_state_chain(owner_resolve(event.pose, ".poses").inputs):
        data.data__internal__.add().__init__(len(data)-1, value)
        data.update(propagate=False)


@event_handler(PoseRemovedEvent)
def on_pose_removed(event: PoseRemovedEvent) -> None:
    '''
    Removes input variable data when a pose is removed.
    '''
    for data in variable_data_chain(owner_resolve(event.poses, ".").inputs):
        data.data__internal__.remove(event.index)
        data.update(propagate=False)


@event_handler(PoseUpdateEvent)
def on_pose_update(event: PoseUpdateEvent) -> None:
    '''
    Updates input variable data when a pose is updated.
    '''
    if event.inputs:
        index = event.driver.poses.index(event.pose)
        for data, value in variable_state_chain(event.inputs):
            data[index].update(value, propagate=False)
            data.update(propagate=False)

