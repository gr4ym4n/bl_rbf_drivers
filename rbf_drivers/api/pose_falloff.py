
from typing import TYPE_CHECKING
from bpy.types import Context, PropertyGroup
from bpy.props import BoolProperty, FloatProperty
from ..lib.curve_mapping import BCLMAP_CurveManager
if TYPE_CHECKING:
    from .pose import RBFDriverPose


def pose_falloff_radius_update_handler(falloff: 'RBFDriverPoseFalloff', _: Context) -> None:
    falloff.update()


def pose_falloff_radius_factor_update_handler(falloff: 'RBFDriverPoseFalloff', _: Context) -> None:
    falloff.update()


def pose_falloff_radius_is_auto_adjusted_update_handler(falloff: 'RBFDriverPoseFalloff', _: Context) -> None:
    if falloff.radius_is_auto_adjusted:
        falloff.radius_adjust()


def pose_falloff_use_curve_update_handler(falloff: 'RBFDriverPoseFalloff', _: Context) -> None:
    falloff.update()


class RBFDriverPoseFalloff(BCLMAP_CurveManager, PropertyGroup):

    @property
    def pose(self) -> 'RBFDriverPose':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])

    radius: FloatProperty(
        name="Radius",
        default=1.0,
        options=set(),
        update=pose_falloff_radius_update_handler
        )

    radius_factor: FloatProperty(
        name="Factor",
        description="",
        min=0.0,
        max=10.0,
        soft_min=0.0,
        soft_max=2.0,
        default=1.0,
        options=set(),
        update=pose_falloff_radius_factor_update_handler
        )

    radius_is_auto_adjusted: BoolProperty(
        name="Auto-Adjust",
        default=True,
        options=set(),
        update=pose_falloff_radius_is_auto_adjusted_update_handler
        )

    use_curve: BoolProperty(
        name="Override",
        default=False,
        options=set(),
        update=pose_falloff_use_curve_update_handler
        )

    def radius_adjust(self) -> None:
        pose = self.pose
        index = pose.index
        data = pose.rbf_driver.distance_matrix[index]
        if len(data) < 2:
            self.radius = 1.0
        else:
            self.radius = min([v for i, v in enumerate(data) if i != index])

    def update(self) -> None:
        self.pose.weight.update()
