
from typing import TYPE_CHECKING
from ..rbf_drivers.app.events import event_handler
from ..rbf_drivers.app.utils import idprop_remove, owner_resolve
from .input_distance_matrix import InputDistanceMatrixUpdateEvent
from ..rbf_drivers.api.inputs import InputNewEvent, InputRemovedEvent
from ..rbf_drivers.api.pose_interpolation import PoseFalloffUpdateEvent
from ..rbf_drivers.api.pose import PoseUpdateEvent
from ..rbf_drivers.api.poses import PoseNewEvent, PoseRemovedEvent, PoseMoveEvent
from .driver_distance_matrix import DriverDistanceMatrixUpdateEvent
from ..rbf_drivers.api.driver_interpolation import DriverFalloffUpdateEvent
from ..rbf_drivers.api.driver import RadiusUpdateEvent, RegularizationUpdateEvent, SmoothingUpdateEvent
from ..rbf_drivers.api.drivers import DriverNewEvent, DriverDisposableEvent
if TYPE_CHECKING:
    from ..rbf_drivers.api.driver import RBFDriver


@event_handler(InputNewEvent)
def on_input_new_event(event: InputNewEvent) -> None:
    '''
    Updates the RBF driver's distance matrix when a new input is added. Note that the
    input has already been initialized by the input manager.'
    '''
    rbfn: 'RBFDriver' = owner_resolve(event.input, ".inputs")
    rbfn.distance_matrix.update()


@event_handler(InputRemovedEvent)
def on_input_removed_event(event: InputRemovedEvent) -> None:
    '''
    Updates the RBF driver's distance matrix when an input is removed
    '''
    rbfn: 'RBFDriver' = owner_resolve(event.inputs, ".")
    rbfn.distance_matrix.update()


@event_handler(InputDistanceMatrixUpdateEvent)
def on_input_distance_matrix_update(event: InputDistanceMatrixUpdateEvent) -> None:
    '''
    Updates the RBF driver's distance matrix when an input's distance matrix
    is updated.
    '''
    rbfn: 'RBFDriver' = owner_resolve(event.matrix, ".inputs")
    rbfn.distance_matrix.update()


@event_handler(PoseFalloffUpdateEvent)
def on_pose_falloff_update(event: PoseFalloffUpdateEvent) -> None:
    '''
    Updates the RBF driver's variable matrix when a pose's falloff
    is updated.
    '''
    rbfn: 'RBFDriver' = owner_resolve(event.falloff, ".poses")
    rbfn.variable_matrix.update()


@event_handler(DriverFalloffUpdateEvent)
def on_driver_falloff_update(event: DriverFalloffUpdateEvent) -> None:
    '''
    Updates the RBF driver's variable matrix when the RBF driver's falloff
    is updated.
    '''
    rbfn: 'RBFDriver' = owner_resolve(event.falloff, ".")
    rbfn.variable_matrix.update()


@event_handler(DriverDistanceMatrixUpdateEvent)
def on_driver_distance_matrix_update(event: DriverDistanceMatrixUpdateEvent) -> None:
    '''
    Updates the RBF driver's variable matrix when the RBF driver's distance matrix
    is updated.
    '''
    rbfn: 'RBFDriver' = owner_resolve(event.matrix, ".")
    rbfn.variable_matrix.update()


@event_handler(PoseNewEvent)
def on_pose_new(event: PoseNewEvent) -> None:
    '''
    Updates the RBF driver's distance matrix when a new pose is added. Note that the
    input manager has already created input variable data for the pose prior to this
    handler being called.
    '''
    rbfn: 'RBFDriver' = owner_resolve(event.pose, ".poses")
    rbfn.distance_matrix.update()


@event_handler(PoseRemovedEvent)
def on_pose_removed(event: PoseRemovedEvent) -> None:
    '''
    Updates the RBF driver's distance matrix when a pose is removed. Note that the
    input manager has already removed input variable data for the pose prior to this
    handler being called.
    '''
    rbfn: 'RBFDriver' = owner_resolve(event.poses, ".")
    rbfn.distance_matrix.update()


@event_handler(PoseUpdateEvent)
def on_pose_update(event: PoseUpdateEvent) -> None:
    '''
    Updates the RBF driver's distance matrix when a pose is updated. Note that the
    input manager has already updated input variable data for the pose prior to this
    handler being called.
    '''
    rbfn: 'RBFDriver' = owner_resolve(event.pose, ".poses")
    rbfn.distance_matrix.update()


@event_handler(PoseMoveEvent)
def on_pose_move(event: PoseMoveEvent) -> None:
    '''
    Updates the RBF driver's distance matrix when a pose is updated. Note that the
    input manager has already updated input variable data for the pose prior to this
    handler being called.
    '''
    rbfn: 'RBFDriver' = owner_resolve(event.pose, ".poses")
    rbfn.distance_matrix.update()


@event_handler(DriverNewEvent)
def on_driver_new(event: DriverNewEvent) -> None:
    '''
    Calculates the distance and variable matrices for new symmetrical RBF drivers.
    Note that changes are not propagated as the pose manager will handle downstream
    updates itself
    '''
    rbfn = event.driver
    rbfn.distance_matrix.update(propagate=False)
    rbfn.variable_matrix.update(propagate=False)


@event_handler(DriverDisposableEvent)
def on_driver_disposable(event: DriverDisposableEvent) -> None:
    '''
    Removes the variable matrix ID property when a driver
    becomes disposable
    '''
    rbfn = event.driver
    idprop_remove(rbfn.id_data.data, rbfn.variable_matrix.name, remove_drivers=False)


@event_handler(RadiusUpdateEvent)
def on_radius_update(event: RadiusUpdateEvent) -> None:
    '''
    '''
    if event.driver.smoothing == 'LINEAR':
        event.driver.variable_matrix.update()


@event_handler(RegularizationUpdateEvent)
def on_regularization_update(event: RegularizationUpdateEvent) -> None:
    '''
    '''
    if event.driver.smoothing == 'LINEAR':
        event.driver.variable_matrix.update()


@event_handler(SmoothingUpdateEvent)
def on_smoothing_update(event: SmoothingUpdateEvent) -> None:
    '''
    '''
    if event.driver.smoothing == 'LINEAR':
        event.driver.variable_matrix.update()
    else:
        event.driver.variable_matrix.__init__([])