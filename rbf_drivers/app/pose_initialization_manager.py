
from .events import event_handler
from ..api.drivers import DriverNewEvent

@event_handler(DriverNewEvent)
def on_driver_new(event: DriverNewEvent) -> None:
    '''
    Adds the rest pose when a new driver is added, or clones poses for symmetrical drivers
    '''
    rbfn = event.driver
    # For new symmetrical RBF drivers, the symmetry manager will handle initialization of
    # all poses.
    if not rbfn.has_symmetry_target:
        rbfn.poses.new(name="Rest")
