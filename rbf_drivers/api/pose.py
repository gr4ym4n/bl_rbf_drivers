
from typing import TYPE_CHECKING, Iterable, Optional, Union
from bpy.types import PropertyGroup
from bpy.props import PointerProperty, StringProperty
from .pose_interpolation import RBFDriverPoseInterpolation
from .mixins import Symmetrical
from .property_target import RBFDriverPropertyTarget
from ..app.events import dataclass, dispatch_event, Event
from ..app.utils import owner_resolve
if TYPE_CHECKING:
    from bpy.types import Context
    from .input import RBFDriverInput
    from .output import RBFDriverOutput
    from .driver import RBFDriver


@dataclass(frozen=True)
class PoseNameUpdateEvent(Event):
    pose: 'RBFDriverPose'
    value: str


@dataclass(frozen=True)
class PoseUpdateEvent(Event):
    driver: 'RBFDriver'
    pose: 'RBFDriverPose'
    inputs: bool = True
    outputs: bool = True


def pose_name_update_handler(pose: 'RBFDriverPose', _: 'Context') -> None:
    dispatch_event(PoseNameUpdateEvent(pose, pose.name))


class RBFDriverPose(Symmetrical, PropertyGroup):

    interpolation: PointerProperty(
        name="Interpolation",
        type=RBFDriverPoseInterpolation,
        options=set()
        )

    influence: PointerProperty(
        name="Influence",
        type=RBFDriverPropertyTarget,
        options=set()
        )

    name: StringProperty(
        name="Name",
        default="",
        options=set(),
        update=pose_name_update_handler
        )

    radius: PointerProperty(
        name="Radius",
        type=RBFDriverPropertyTarget,
        options=set()
        )

    weight: PointerProperty(
        name="Weight",
        type=RBFDriverPropertyTarget,
        options=set()
        )

    def update(self,
               inputs : Optional[Union[bool, Iterable['RBFDriverInput' ]]]=True,
               outputs: Optional[Union[bool, Iterable['RBFDriverOutput']]]=True) -> None:

        driver: 'RBFDriver' = owner_resolve(self, ".poses")

        if inputs is True:
            inputs = tuple(driver.inputs)
        elif inputs is False:
            inputs = tuple()
        else:
            if any(item not in driver.inputs for item in inputs):
                raise ValueError(f'All inputs must be inputs of {driver}')
        
        if outputs is True:
            outputs = tuple(driver.outputs)
        elif outputs is False:
            outputs = tuple()
        else:
            if any(item not in driver.outputs for item in outputs):
                raise ValueError(f'All outputs must be outputs of {driver}')

        dispatch_event(PoseUpdateEvent(driver, self, inputs, outputs))
