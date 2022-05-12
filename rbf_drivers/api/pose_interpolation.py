
from typing import TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import BoolProperty
from ..lib.curve_mapping import BCLMAP_CurveManager
from ..app.events import dataclass, dispatch_event, Event
if TYPE_CHECKING:
    from bpy.types import Context


@dataclass(frozen=True)
class PoseInterpolationUpdateEvent(Event):
    interpolation: 'RBFDriverPoseInterpolation'


def pose_interpolation_use_curve_update_handler(interpolation: 'RBFDriverPoseInterpolation', _: 'Context') -> None:
    interpolation.update()


class RBFDriverPoseInterpolation(BCLMAP_CurveManager, PropertyGroup):

    use_curve: BoolProperty(
        name="Override",
        default=False,
        options=set(),
        update=pose_interpolation_use_curve_update_handler
        )

    def update(self) -> None:
        super().update()
        dispatch_event(PoseInterpolationUpdateEvent(self))

    def __repr__(self) -> str:
        # TODO
        return super().__repr__()

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".collection__internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'