
from typing import TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import PointerProperty
from .mixins import IDPropertyController
if TYPE_CHECKING:
    from .poses import Pose


class PoseWeightNormalized(IDPropertyController, PropertyGroup):

    @property
    def name(self) -> str:
        return self.pose.name

    @property
    def pose(self) -> 'Pose':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".weight")[0])

    @property
    def weight(self) -> 'PoseWeight':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])

    def __init__(self, pose: 'Pose') -> None:
        key = f'rbf_pose_{pose.identifier}_weight_normalized'
        enable = pose.driver.poses.normalize_weights
        super().__init__(key, enable)


class PoseWeight(IDPropertyController, PropertyGroup):

    normalized: PointerProperty(
        name="Normalized",
        type=PoseWeightNormalized,
        options=set()
        )

    @property
    def pose(self) -> 'Pose':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".weight")[0])

    def __init__(self, pose: 'Pose') -> None:
        super().__init__(f'rbf_poseweight_{pose.identifier}', True)
        self.normalized.__init__(pose)
