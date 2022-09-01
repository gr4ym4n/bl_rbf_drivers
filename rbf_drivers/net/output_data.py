
from typing import TYPE_CHECKING
from functools import partial
from numpy import array
from ..app.utils import (
    axis_angle_to_euler,
    axis_angle_to_quaternion,
    euler_to_axis_angle,
    euler_to_quaternion,
    quaternion_to_axis_angle,
    quaternion_to_euler)
from ..app.events import event_handler
from ..api.output_data import OutputSampleUpdateEvent
from ..api.outputs import (
    OutputBoneTargetUpdateEvent,
    OutputObjectUpdateEvent,
    OutputRotationModeUpdateEvent
    )
from ..api.poses import PoseNewEvent, PoseDisposableEvent
if TYPE_CHECKING:
    from ..api.outputs import OutputPropertyUpdateEvent

ROTATION_CONVERSION_LUT = {
    'EULER': {
        'EULER': None,
        'QUATERNION': euler_to_quaternion,
        'AXIS_ANGLE': partial(euler_to_axis_angle, vectorize=True)
        },
    'QUATERNION': {
        'EULER': quaternion_to_euler,
        'AXIS_ANGLE': partial(quaternion_to_axis_angle, vectorize=True),
        'QUATERNION': None
        },
    'AXIS_ANGLE': {
        'EULER': axis_angle_to_euler,
        'AXIS_ANGLE': None,
        'QUATERNION': axis_angle_to_quaternion
        }
    }


@event_handler(OutputRotationModeUpdateEvent)
def on_output_rotation_mode_update(event: OutputRotationModeUpdateEvent) -> None:
    '''
    '''
    output = event.output
    convert = ROTATION_CONVERSION_LUT[event.previous_value][event.value]

    if convert:
        matrix = array([
            tuple(scalar.value for scalar in channel.data) for channel in output.channels
            ], dtype=float)

        for vector, column in zip(matrix.T if event.previous_value != 'EULER' else matrix[1:].T,
                                    matrix.T if event.value          != 'EULER' else matrix[1:].T):
            column[:] = convert(vector)

        if event.value == 'EULER':
            matrix[0] = 0.0

        for channel, values in zip(output.channels, matrix):
            channel.data.__init__(values)


@event_handler(OutputBoneTargetUpdateEvent, OutputObjectUpdateEvent)
def on_output_target_update(event: 'OutputPropertyUpdateEvent') -> None:
    output = event.output
    target = output.object

    if target is not None and target.type == 'ARMATURE' and output.bone_target:
        target = target.pose.bones.get(output.bone_target)

    if target is not None:
        mode = target.rotation_mode
        if len(mode) < 5:
            mode = 'EULER'

        if output.rotation_mode != mode:
            userdef = output.rotation_mode_is_user_defined
            output.rotation_mode = mode
            output["rotation_mode_is_user_defined"] = userdef


@event_handler(PoseNewEvent)
def on_pose_new(event: PoseNewEvent) -> None:
    for output in event.pose.driver.outputs:
        for channel in output.channels:
            sample = channel.data.internal__.add()
            sample["name"] = event.pose.name
            sample["value"] = channel.value


@event_handler(PoseDisposableEvent)
def on_pose_disposable(event: PoseDisposableEvent) -> None:
    for output in event.pose.driver.outputs:
        for channel in output.channels:
            index = channel.data.find(event.pose.name)
            if index != -1:
                channel.data.internal__.remove(index)
            else:
                # TODO error message an recovery
                raise RuntimeError()