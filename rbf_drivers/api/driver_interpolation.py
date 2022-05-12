
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

    def __repr__(self) -> str:
        return (f'{self.__class__.__name__}(interpolation="{self.interpolation}", '
                                          f'easing="{self.easing}")')

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".collection__internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'
