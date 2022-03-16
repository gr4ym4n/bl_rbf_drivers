
from typing import TYPE_CHECKING
from bpy.types import Context, PropertyGroup
from bpy.props import FloatProperty
from ..lib.curve_mapping import BCLMAP_CurveManager
if TYPE_CHECKING:
    from .pose_weight import RBFDriverPoseWeight
    from .pose import RBFDriverPose
    from .driver import RBFDriver

def falloff_radius_factor_update_handler(falloff: 'RBFDriverFalloff', _: Context) -> None:
    falloff.update()


class RBFDriverFalloff(BCLMAP_CurveManager, PropertyGroup):

    radius_factor: FloatProperty(
        name="Factor",
        description="",
        min=0.0,
        max=10.0,
        soft_min=0.0,
        soft_max=2.0,
        default=1.0,
        options=set(),
        update=falloff_radius_factor_update_handler
        )

    @property
    def rbf_driver(self) -> 'RBFDriver':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])

    def update(self) -> None:
        # TODO update variable matrix


        pose: 'RBFDriverPose'
        for pose in self.rbf_driver.poses:
            weight: 'RBFDriverPoseWeight' = pose.weight
            weight.update()