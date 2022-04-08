
from bpy.types import PropertyGroup
from ..lib.curve_mapping import BCLMAP_CurveManager
from ..app.events import dataclass, dispatch_event, Event


@dataclass(frozen=True)
class DriverInterpolationUpdateEvent(Event):
    interpolation: 'RBFDriverInterpolation'


class RBFDriverInterpolation(BCLMAP_CurveManager, PropertyGroup):

    def update(self) -> None:
        super().update()
        dispatch_event(DriverInterpolationUpdateEvent(self))
