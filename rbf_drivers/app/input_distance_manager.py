
from typing import TYPE_CHECKING, Callable, Sequence
from functools import partial
from math import acos, asin, fabs, pi, sqrt
import numpy as np
from .events import dataclass, dispatch_event, event_handler, Event
from .input_data_manager import InputDataInitializedEvent, InputDataUpdatedEvent
from ..api.pose_data_ import pose_data_container_update, pose_data_group_remove
from ..api.inputs import InputDisposableEvent
if TYPE_CHECKING:
    from ..api.input import Input

INPUT_DISTANCE = "pose_distance_matrix"


@dataclass
class InputDistanceMatrixInitializedEvent(Event):
    input: 'Input'
    data: np.ndarray


@dataclass
class InputDistanceMatrixUpdatedEvent(Event):
    input: 'Input'
    data: np.narray


def distance_euclidean(a: Sequence[float], b: Sequence[float]) -> float:
    return sqrt(sum(pow(ai - bi, 2.0) for ai, bi in zip(a, b)))


def distance_angle(a: Sequence[float], b: Sequence[float]) -> float:
    return fabs(a[0]-b[0])/pi


def distance_quaternion(a: Sequence[float], b: Sequence[float]) -> float:
    return acos((2.0 * pow(min(max(sum(ai * bi for ai, bi in zip(a, b)), -1.0), 1.0), 2.0)) - 1.0) / pi


def distance_direction(a: Sequence[float], b: Sequence[float], axis: str) -> float:
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    if axis == 'X':
        a = (1.0 - 2.0 * (ay * ay + az * az), 2.0 * (ax * ay + aw * az), 2.0 * (ax * az - aw * ay))
        b = (1.0 - 2.0 * (by * by + bz * bz), 2.0 * (bx * by + bw * bz), 2.0 * (bx * bz - bw * by))
    elif axis == 'Y':
        a = (2.0 * (ax * ay - aw * az), 1.0 - 2.0 * (ax * ax + az * az), 2.0 * (ay * az + aw * ax))
        b = (2.0 * (bx * by - bw * bz), 1.0 - 2.0 * (bx * bx + bz * bz), 2.0 * (by * bz + bw * bx))
    else:
        a = (2.0 * (ax * az + aw * ay), 2.0 * (ay * az - aw * ax), 1.0 - 2.0 * (ax * ax + ay * ay))
        b = (2.0 * (bx * bz + bw * by), 2.0 * (by * bz - bw * bx), 1.0 - 2.0 * (bx * bx + by * by))
    return (asin((sum(ai * bi for ai, bi in zip(a, b)))) - -(pi / 2.0)) / pi


def distance_function(input_: 'Input') -> Callable[[Sequence[float], Sequence[float]], float]:
    type_ = input_.type
    if type_ == 'ROTATION':
        mode = input_.rotation_mode
        if mode == 'QUATERNION': return distance_quaternion
        if mode == 'SWING'     : return partial(distance_direction, axis=input_.rotation_axis)
        if mode == 'TWIST'     : return distance_angle
    return distance_euclidean


def distance_matrix(input_: 'Input', data: np.ndarray) -> np.ndarray:
    input_ = input_
    metric = distance_function(input_)
    matrix = np.array([metric(a, b) for a in data for b in data], dtype=float)
    length = len(data)
    return matrix.reshape(length, length)


def distance_matrix_dataframe_create(input_: 'Input', data: np.ndarray) -> np.ndarray:
    input_.parameters.internal__.add()["name"] = INPUT_DISTANCE
    return distance_matrix_dataframe_update(input_, data)


def distance_matrix_dataframe_update(input_: 'Input', data: np.ndarray) -> np.ndarray:
    matrix = distance_matrix(input_, data)
    pose_data_container_update(input_.parameters[INPUT_DISTANCE], matrix)
    return matrix


def distance_matrix_dataframe_delete(input_: 'Input') -> None:
    pose_data_group_remove(input_.parameters, INPUT_DISTANCE)


@event_handler(InputDataInitializedEvent)
def on_input_initialized(event: InputDataInitializedEvent) -> None:
    input_ = event.input
    matrix = distance_matrix_dataframe_create(input_, event.data)
    dispatch_event(InputDistanceMatrixInitializedEvent(input_, matrix))


@event_handler(InputDataUpdatedEvent)
def on_input_data_update(event: InputDataUpdatedEvent) -> None:
    input_ = event.input
    matrix = distance_matrix_dataframe_update(input_, event.data)
    dispatch_event(InputDistanceMatrixUpdatedEvent(input_, matrix), immediate=True)


@event_handler(InputDisposableEvent)
def on_input_disposable(event: InputDisposableEvent) -> None:
    distance_matrix_dataframe_delete(event.input)
