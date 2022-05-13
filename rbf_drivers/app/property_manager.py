'''
Manages ID properties for RBF driver components, with the exception of the pose weight property
which is managed by the pose weight driver manager.
'''

from typing import TYPE_CHECKING
from .events import event_handler
from .utils import idprop_create, idprop_remove
from ..api.poses import PoseNewEvent, PoseDisposableEvent
from ..api.outputs import OutputNewEvent, OutputDisposableEvent
if TYPE_CHECKING:
    from ..api.property_target import RBFDriverPropertyTarget
    from ..api.pose import RBFDriverPose
    from ..api.output import RBFDriverOutput


def pose_idprops_create(pose: 'RBFDriverPose') -> None:
    influence: 'RBFDriverPropertyTarget' = pose.influence
    influence["name"] = f'rbfn_pinf_{pose.identifier}'
    idprop_create(influence.id, influence.name, default=1.0, min=0.0, max=1.0, soft_min=0.0, soft_max=1.0)

    radius: 'RBFDriverPropertyTarget' = pose.radius
    radius["name"] = f'rbfn_prad_{pose.identifier}'
    idprop_create(radius.id, radius.name, default=1.0, min=0.0, soft_min=0.0, soft_max=5.0)


def pose_idprops_remove(pose: 'RBFDriverPose') -> None:
    influence: 'RBFDriverPropertyTarget' = pose.influence
    idprop_remove(influence.id, influence.name)

    radius: 'RBFDriverPropertyTarget' = pose.radius
    idprop_remove(radius.id, radius.name)


def output_idprops_create(output: 'RBFDriverOutput') -> None:
    influence: 'RBFDriverPropertyTarget' = output.influence
    influence["name"] = f'rbfn_oinf_{output.identifier}'
    idprop_create(influence.id, influence.name, default=1.0, min=0.0, max=1.0, soft_min=0.0, soft_max=1.0)


def output_idprops_remove(output: 'RBFDriverOutput') -> None:
    influence: 'RBFDriverPropertyTarget' = output.influence
    idprop_remove(influence.id, influence.name)


@event_handler(PoseNewEvent)
def on_pose_new(event: PoseNewEvent) -> None:
    pose_idprops_create(event.pose)


@event_handler(PoseDisposableEvent)
def on_pose_disposable(event: PoseDisposableEvent) -> None:
    pose_idprops_remove(event.pose)


@event_handler(OutputNewEvent)
def on_output_new(event: OutputNewEvent) -> None:
    output_idprops_create(event.output)


@event_handler(OutputDisposableEvent)
def on_output_disposable(event: OutputDisposableEvent) -> None:
    output_idprops_remove(event.output)

