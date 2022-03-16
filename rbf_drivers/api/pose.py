
from typing import TYPE_CHECKING
from bpy.types import Context, PropertyGroup
from bpy.props import PointerProperty, StringProperty
from rbf_drivers.api.pose_falloff import RBFDriverPoseFalloff
from rbf_drivers.api.pose_weight import RBFDriverPoseWeight
from .mixins import Symmetrical
if TYPE_CHECKING:
    from .driver import RBFDriver


def pose_name_update_handler(pose: 'RBFDriverPose', _: Context) -> None:
    names = [item.name for item in pose.rbf_driver.poses if item != pose]
    index = 0
    value = pose.name
    while value in names:
        index += 1
        value = f'{pose.name}.{str(index).zfill(3)}'
    pose["name"] = value


class RBFDriverPose(Symmetrical, PropertyGroup):

    falloff: PointerProperty(
        name="Falloff",
        type=RBFDriverPoseFalloff,
        options=set()
        )

    @property
    def index(self) -> int:
        return self.rbf_driver.poses.find(self.name)

    name: StringProperty(
        name="Name",
        default="",
        options=set(),
        update=pose_name_update_handler
        )

    @property
    def rbf_driver(self) -> 'RBFDriver':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".poses.")[0])

    weight: PointerProperty(
        name="Weight",
        type=RBFDriverPoseWeight,
        options=set()
        )
