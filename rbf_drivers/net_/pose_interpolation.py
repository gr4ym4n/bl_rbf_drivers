
from typing import TYPE_CHECKING
from ..app.events import dispatch_event, event_handler
from ..api.pose_interpolation import PoseInterpolationUpdateEvent
from ..api.poses import (
    PoseNewEvent,
    PoseDisposableEvent,
    POSE_INTERPOLATION_TYPE_TABLE,
    POSE_INTERPOLATION_EXTEND_TABLE,
    POSE_INTERPOLATION_EASING_TABLE
    )
if TYPE_CHECKING:
    from bpy.types import ShaderNodeTree, ShaderNodeVectorCurve
    from ..api.pose_interpolation import PoseInterpolation
    from ..api.poses import Pose, Poses
    from ..api.driver import RBFDriver


def tree_ensure(driver: 'RBFDriver') -> ShaderNodeTree:
    tree = driver.nodetree_internal__
    if tree is None:
        import bpy
        name = f'rbf_driver_{driver.identifier}_node_tree'
        tree = bpy.data.node_groups.new(name, "ShaderNodeTree")
        driver.nodetree_internal__ = tree
    return tree


def node_create(tree: 'ShaderNodeTree', pose: 'Pose') -> None:
    node = tree.nodes.new("ShaderNodeVectorCurve")
    node.name = pose.identifier
    mapping = node.mapping
    mapping.clip_min_x = 0.0
    mapping.clip_max_x = 1.0
    mapping.clip_min_y = 0.0
    mapping.clip_max_y = 1.0
    mapping.use_clip = True
    mapping.extend = 'HORIZONTAL'


def node_update(node: 'ShaderNodeVectorCurve', interpolation: 'PoseInterpolation') -> None:
    points = node.mapping.curves[0].points
    length = max(len(interpolation.points), 2)

    while len(points) > length:
        points.remove(points[-2])

    while len(points) < length:
        points.new(0.0, 0.0)

    for point, props in zip(points, interpolation.points):
        point.handle_type = props.handle_type
        point.location = props.location
        point.select = props.select

    node.mapping.update()


def node_remove(tree: 'ShaderNodeTree', pose: 'Pose') -> None:
    node = tree.nodes.get(pose.identifier)
    if node:
        tree.nodes.remove(node)


@event_handler(PoseNewEvent)
def on_pose_new(event: PoseNewEvent) -> None:
    node_create(tree_ensure(event.pose.driver), event.pose)


@event_handler(PoseDisposableEvent)
def on_pose_disposable(event: PoseDisposableEvent) -> None:
    tree = event.pose.driver.nodetree_internal__
    if tree:
        node_remove(tree, event.pose)


@event_handler(PoseInterpolationUpdateEvent)
def on_pose_interpolation_update(event: PoseInterpolationUpdateEvent) -> None:

    pose = event.interpolation.pose
    tree = tree_ensure(pose.driver)
    node = tree.nodes.get(pose.identifier)
    if node:
        node_update(node, event.interpolation)
    else:
        node_create(tree, pose)

    if not pose.sync__internal__:
        poses: 'Poses' = pose.driver.poses

        if poses.sync_interpolation:
            item: 'Pose'
            type = pose.get("type", POSE_INTERPOLATION_TYPE_TABLE['LINEAR'])
            extend = pose.get("extend", POSE_INTERPOLATION_EXTEND_TABLE['HORIZONTAL'])
            easing = pose.get("easing", POSE_INTERPOLATION_EASING_TABLE['EASE_IN_OUT'])
            points = pose.points

            for item in poses:
                if item != pose:
                    item["sync__internal__"] = True
                    try:
                        item["type"] = type
                        item["extend"] = extend
                        item["easing"] = easing
                        item.points.__init__(points)
                        dispatch_event(PoseInterpolationUpdateEvent(item))
                    finally:
                        item["sync__internal__"] = False
