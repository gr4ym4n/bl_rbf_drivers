
from typing import TYPE_CHECKING
from .events import event_handler
from .utils import owner_resolve
from ..api.input_target import (InputTargetPropertyUpdateEvent,
                                InputTargetBoneTargetUpdateEvent,
                                InputTargetDataPathUpdateEvent,
                                InputTargetIDTypeUpdateEvent,
                                InputTargetObjectUpdateEvent,
                                InputTargetRotationModeUpdateEvent,
                                InputTargetTransformSpaceUpdateEvent,
                                InputTargetTransformTypeUpdateEvent)
if TYPE_CHECKING:
    from ..api.driver import RBFDriver

@event_handler(InputTargetBoneTargetUpdateEvent,
               InputTargetDataPathUpdateEvent,
               InputTargetIDTypeUpdateEvent,
               InputTargetObjectUpdateEvent,
               InputTargetRotationModeUpdateEvent,
               InputTargetTransformSpaceUpdateEvent,
               InputTargetTransformTypeUpdateEvent)
def on_input_target_property_update(event: InputTargetPropertyUpdateEvent) -> None:
    driver: 'RBFDriver' = owner_resolve(event.target, ".inputs")
    for pose in driver.poses:
        pose.weight.update(propagate=False)

