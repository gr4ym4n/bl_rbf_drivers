
from typing import TYPE_CHECKING
from .events import event_handler
from ..api.poses import PoseNewEvent, PoseDisposableEvent
from ..api.drivers import DriverNewEvent, DriverDisposableEvent
from ..lib.curve_mapping import nodetree_node_remove
if TYPE_CHECKING:
    from ..lib.curve_mapping import BLCMAP_Curve
    from ..api.pose_interpolation import RBFDriverPoseInterpolation
    from ..api.driver_interpolation import RBFDriverInterpolation


@event_handler(PoseNewEvent)
def on_pose_new(event: PoseNewEvent) -> None:
    '''
    Creates a interpolation curve node for a newly created pose's interpolation
    '''
    interpolation: 'RBFDriverPoseInterpolation' = event.pose.interpolation
    interpolation.__init__(type='SIGMOID', interpolation='LINEAR')


@event_handler(PoseDisposableEvent)
def on_pose_disposable(event: PoseDisposableEvent) -> None:
    '''
    Removes the interpolation curve node for a disposable pose's interpolation
    '''
    curve: 'BLCMAP_Curve' = event.pose.interpolation.curve
    nodetree_node_remove(curve.node_identifier)


@event_handler(DriverNewEvent)
def on_driver_new(event: DriverNewEvent) -> None:
    '''
    Creates a interpolation curve node for a newly created driver's interpolation
    '''
    interpolation: 'RBFDriverInterpolation' = event.driver.interpolation
    interpolation.__init__(type='SIGMOID', interpolation='LINEAR')


@event_handler(DriverDisposableEvent)
def on_driver_disposable(event: DriverDisposableEvent) -> None:
    '''
    Removes the interpolation curve node for a disposable driver's interpolation
    '''
    curve: 'BLCMAP_Curve' = event.driver.interpolation.curve
    nodetree_node_remove(curve.node_identifier)
