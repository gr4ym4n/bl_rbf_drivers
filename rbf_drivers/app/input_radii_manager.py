
from typing import TYPE_CHECKING, Iterator, Tuple
import numpy as np
from rbf_drivers.api.pose_data_ import pose_data_container_update, pose_data_group_remove
from .events import dataclass, dispatch_event, event_handler, Event
from .input_distance_manager import (
    InputDistanceMatrixInitializedEvent,
    InputDistanceMatrixUpdatedEvent,
    )
from ..api.inputs import InputDisposableEvent
if TYPE_CHECKING:
    from ..api.input import Input

INPUT_RADII = "pose_radii"


@dataclass(frozen=True)
class InputPoseRadiiInitializedEvent(Event):
    input: 'Input'
    data: np.ndarray


@dataclass(frozen=True)
class InputPoseRadiusUpdatedEvent(Event):
    input: 'Input'
    index: int
    value: float


def input_pose_radii_calculate(input_: 'Input', distance_matrix: np.ndarray) -> np.ndarray:
    matrix = np.ma.masked_values(distance_matrix, 0.0, atol=input_.tolerance)
    result = []
    for row in matrix:
        row = row.compressed()
        result.append(0.0 if len(row) else np.min(row))
    return np.array(result, dtype=float)


def input_pose_radii_dataframe_create(input_: 'Input', distance_matrix: np.ndarray) -> np.ndarray:
    radii = input_pose_radii_calculate(input_, distance_matrix)
    pose_data_container_update(input_.parameters[INPUT_RADII], radii)
    return radii


def input_pose_radii_dataframe_update(input_: 'Input',
                                      distance_matrix: np.ndarray) -> Iterator[Tuple[int, float]]:
    container = input_.parameters[INPUT_RADII]
    radii = input_pose_radii_calculate(input_, distance_matrix)
    for index, (radius, component) in enumerate(zip(radii, container)):
        if abs(radius - component.value) > input_.tolerance:
            component["value"] = radius
            yield index, radius


def input_pose_radii_dataframe_delete(input_: 'Input') -> None:
    pose_data_group_remove(input_.parameters, INPUT_RADII)


@event_handler(InputDistanceMatrixInitializedEvent)
def on_input_distance_matrix_initialized(event: InputDistanceMatrixInitializedEvent) -> None:
    input_ = event.input
    input_.parameters.internal__.add()["name"] = INPUT_RADII
    radii = input_pose_radii_dataframe_create(input_, event.data)
    dispatch_event(InputPoseRadiiInitializedEvent(input_, radii))


@event_handler(InputDistanceMatrixUpdatedEvent)
def on_input_distance_matrix_update(event: InputDistanceMatrixUpdatedEvent) -> None:
    input_ = event.input
    for index, value in input_pose_radii_dataframe_update(input_, event.data):
        dispatch_event(InputPoseRadiusUpdatedEvent(input_, index, value), immediate=True)


@event_handler(InputDisposableEvent)
def on_input_disposable(event: InputDisposableEvent) -> None:
    input_pose_radii_dataframe_delete(event.input)
