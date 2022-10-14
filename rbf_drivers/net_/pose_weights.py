
from typing import TYPE_CHECKING
from ..app.utils import idprop_driver_ensure, idprop_remove, to_bezier, keyframe_points_assign
from ..app.events import event_handler
from ..api.poses import PoseWeightsAreNormalizedUpdateEvent
if TYPE_CHECKING:
    from ..api.pose_interpolation import PoseInterpolation
    from ..api.pose_weight import PoseWeight
    from ..api.poses import Pose, Poses


def pose_weight_sum_driver_update(poses: 'Poses') -> None:
    fcurve = idprop_driver_ensure(poses.summed_weights, clear_variables=True)
    driver = fcurve.driver
    driver.type = 'SUM'

    for index, pose in enumerate(poses):
        weight = pose.weight

        variable = driver.variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = f'pose_{str(index).zfill(2)}'
        
        target = variable.targets[0]
        target.id_type = weight.id_type
        target.id = weight.id
        target.data_path = weight.data_path


def pose_weight_sum_driver_remove(poses: 'Poses') -> None:
    idprop_remove(poses.summed_weights, remove_drivers=True)


def pose_weight_normalized_driver_update(pose: 'Pose') -> None:
    fcurve = idprop_driver_ensure(pose.weight.normalized, clear_variables=True)
    driver = fcurve.driver

    for name, prop in zip("ws", (pose.weight, pose.driver.poses.summed_weight)):
        variable = driver.variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = name

        target = variable.targets[0]
        target.id_type = prop.id_type
        target.id = prop.id
        target.data_path = prop.data_path

    driver.type = 'SCRIPTED'
    driver.expression = "/".join(v.name for v in driver.variables)


def pose_weight_normalized_driver_remove(pose: 'Pose') -> None:
    idprop_remove(pose.weight, remove_drivers=True)


def pose_weight_driver_update(pose: 'Pose') -> None:
    fcurve = idprop_driver_ensure(pose.weight, clear_variables=True)
    driver = fcurve.driver
    variables = driver.variables

    for input in pose.driver.inputs:
        input_weight = input.pose_weights[pose.name]

        variable = variables.new()
        variable.type = 'SINGLE_PROP'

        target = variable.targets[0]
        target.id_type = input_weight.id_type
        target.id = input_weight.id
        target.data_path = input_weight.data_path

    if len(variables) == 0:
        expression = "0.0"
    elif len(variables) == 1:
        expression = variables[0].name
    else:
        expression = f'({"+".join([v.name for v in variables])})/{float(len(variables))}'

    driver.type = 'SCRIPTED'
    driver.expression = expression


def pose_weight_fcurve_update(pose: 'Pose') -> None:
    fcurve = idprop_driver_ensure(pose.weight)

    interpolation: 'PoseInterpolation' = pose.interpolation
    radius = pose.radius

    if radius == 1.0:
        rangex = (0.0, 1.0)
    elif radius > 1.0:
        offset = (1.0-radius) * 0.5
        rangex = (-offset, 1.0+offset)
    else:
        offset = (radius-1.0) * 0.5
        rangex = (offset, 1.0+offset)

    points = to_bezier(interpolation.points, rangex, (0.0, 1.0))
    keyframe_points_assign(fcurve.keyframe_points, points)


@event_handler(PoseWeightsAreNormalizedUpdateEvent)
def on_pose_weights_are_normalized_update(event: PoseWeightsAreNormalizedUpdateEvent) -> None:
    poses = event.poses
    if event.value:
        pose_weight_sum_driver_update(poses)
        for pose in poses:
            pose_weight_normalized_driver_update(pose)
    else:
        for pose in poses:
            pose_weight_normalized_driver_remove(pose)
        pose_weight_sum_driver_remove(poses)
