'''
Note that output channel data initialization is handled by the output inititialization manager
'''

from itertools import chain
from operator import attrgetter
from typing import TYPE_CHECKING, Iterable, Iterator, Optional, Tuple
from functools import partial
import numpy as np
from .events import event_handler
from .utils import owner_resolve
from ..api.pose import PoseUpdateEvent
from ..api.poses import PoseMoveEvent, PoseNewEvent, PoseRemovedEvent
from ..api.output import OutputRotationModeChangeEvent
from ..api.drivers import DriverNewEvent
from ..lib.rotation_utils import (axis_angle_to_euler,
                                  axis_angle_to_quaternion,
                                  euler_to_axis_angle,
                                  euler_to_quaternion,
                                  quaternion_to_axis_angle,
                                  quaternion_to_euler)
if TYPE_CHECKING:
    from ..api.output_channel_data import RBFDriverOutputChannelData
    from ..api.output_channel import RBFDriverOutputChannel
    from ..api.output import RBFDriverOutput
    from ..api.driver import RBFDriver


ROTATION_CONVERSION_LUT = {
    'EULER': {
        'QUATERNION': euler_to_quaternion,
        'AXIS_ANGLE': partial(euler_to_axis_angle, vectorize=True)
        },
    'QUATERNION': {
        'EULER': quaternion_to_euler,
        'AXIS_ANGLE': partial(quaternion_to_axis_angle, vectorize=True)
        },
    'AXIS_ANGLE': {
        'EULER': axis_angle_to_euler,
        'QUATERNION': axis_angle_to_quaternion
        }
    }


channels = attrgetter("channels")
data = attrgetter("data")


def channel_state(channel: 'RBFDriverOutputChannel') -> Tuple['RBFDriverOutputChannelData', float]:
    return channel.data, channel.value


def channel_chain(outputs: Iterable['RBFDriverOutput']) -> Iterator['RBFDriverOutputChannel']:
    return chain(*tuple(map(channels, outputs)))


def channel_data_chain(outputs: Iterable['RBFDriverOutput']) -> Iterator['RBFDriverOutputChannelData']:
    return map(data, channel_chain(outputs))


def channel_state_chain(outputs: Iterable['RBFDriverOutput']) -> Iterator[Tuple['RBFDriverOutputChannelData', float]]:
    return map(channel_state, channel_chain(outputs))


@event_handler(OutputRotationModeChangeEvent)
def on_output_rotation_mode_change(event: OutputRotationModeChangeEvent) -> None:
    '''
    '''
    output = event.output
    if output.type == 'ROTATION' and event.value != event.previous_value:

        convert = ROTATION_CONVERSION_LUT[event.previous_value][event.value]

        matrix = np.array([
            tuple(scalar.value for scalar in channel.data) for channel in output.channels
            ], dtype=np.float)

        for vector, column in zip(matrix.T if event.previous_value != 'EULER' else matrix[1:].T,
                                  matrix.T if event.value          != 'EULER' else matrix[1:].T):
            column[:] = convert(vector)

        if event.value == 'EULER':
            matrix[0] = 0.0

        for channel, values in zip(output.channels, matrix):
            channel.data.__init__(values)


@event_handler(PoseNewEvent)
def on_pose_new(event: PoseNewEvent) -> None:
    '''
    '''
    for data, value in channel_state_chain(owner_resolve(event.pose, ".poses").outputs):
        data.data__internal__.add().__init__(len(data)-1, value)


@event_handler(PoseRemovedEvent)
def on_pose_removed(event: PoseRemovedEvent) -> None:
    '''
    '''
    for data in channel_data_chain(owner_resolve(event.poses, ".").outputs):
        data.data__internal__.remove(event.index)


@event_handler(PoseUpdateEvent)
def on_pose_update(event: PoseUpdateEvent) -> None:
    '''
    '''
    if event.outputs:
        index = event.driver.poses.index(event.pose)
        for data, value in channel_state_chain(event.outputs):
            data[index].update(value, propagate=False)


@event_handler(PoseMoveEvent)
def on_pose_move(event: PoseMoveEvent) -> None:
    '''
    '''
    a, b = event.from_index, event.to_index
    for data in channel_data_chain(owner_resolve(event.pose, ".poses").outputs):
        data.data__internal__.move(a, b)


@event_handler(DriverNewEvent)
def on_driver_new(event: DriverNewEvent) -> None:
    '''
    '''
    if event.driver.has_symmetry_target:
        # TODO clone outputs for symmetrical driver
        pass
