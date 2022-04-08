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


@event_handler(PoseNewEvent)
def on_pose_new(event: PoseNewEvent) -> None:
    '''
    '''
    influence: 'RBFDriverPropertyTarget' = event.pose.influence
    influence["name"] = f'rbfn_pinf_{event.pose.identifier}'
    idprop_create(influence.id, influence.name, default=1.0, min=0.0, max=1.0, soft_min=0.0, soft_max=1.0)

    radius: 'RBFDriverPropertyTarget' = event.pose.radius
    radius["name"] = f'rbfn_prad_{event.pose.identifier}'
    idprop_create(radius.id, radius.name, default=1.0, min=0.0, soft_min=0.0, soft_max=5.0)


@event_handler(PoseDisposableEvent)
def on_pose_disposable(event: PoseDisposableEvent) -> None:
    '''
    '''
    influence: 'RBFDriverPropertyTarget' = event.pose.influence
    idprop_remove(influence.id, influence.name)

    radius: 'RBFDriverPropertyTarget' = event.pose.radius
    idprop_remove(radius.id, radius.name)


@event_handler(OutputNewEvent)
def on_output_new(event: OutputNewEvent) -> None:
    '''
    '''
    influence: 'RBFDriverPropertyTarget' = event.output.influence
    influence["name"] = f'rbfn_oinf_{event.output.identifier}'
    idprop_create(influence.id, influence.name, default=1.0, min=0.0, max=1.0, soft_min=0.0, soft_max=1.0)    


@event_handler(OutputDisposableEvent)
def on_output_disposable(event: OutputDisposableEvent) -> None:
    '''
    '''
    influence: 'RBFDriverPropertyTarget' = event.output.influence
    idprop_remove(influence.id, influence.name)

