
#region Imports
###################################################################################################

from typing import Any, Iterator, List, Optional, Tuple, Union

from bpy.types import PropertyGroup
from bpy.props import (CollectionProperty,
                       EnumProperty,
                       FloatProperty,
                       IntProperty,
                       PointerProperty)

from .lib.curve_mapping import BCLMAP_CurveManager

from .mixins import Identifiable

from .input import (RBFDriverInputs, input_influence_sum_driver_update, input_influence_sum_idprop_ensure,
                    input_pose_distance_driver_update_all,
                    input_pose_distance_fcurve_update_all,
                    input_pose_distance_idprop_update,
                    input_pose_radii_update)

from .pose import (RBFDriverPose,
                   RBFDriverPoses,
                   pose_distance_sum_driver_update_all,
                   pose_distance_sum_idprop_update,
                   pose_weight_driver_update_all, pose_weight_fcurve_update,
                   pose_weight_fcurve_update_all,
                   pose_weight_idprop_update)

from .output import RBFDriverOutputs

#endregion Imports

#region Configuration
###################################################################################################

DRIVER_TYPE_ITEMS = [
    ('NONE'      , "Generic"   , "", 'DRIVER'       , 0),
    ('SHAPE_KEYS', "Shape Keys", "", 'SHAPEKEY_DATA', 1),
    ]

DRIVER_TYPE_INDEX = {
    item[0]: item[4] for item in DRIVER_TYPE_ITEMS
    }

#endregion Configuration

#region Properties
###################################################################################################

def driver_falloff_radius_update_handler(falloff: 'RBFDriverFalloff', _) -> None:
    falloff.update()


class RBFDriverFalloff(BCLMAP_CurveManager, PropertyGroup):

    radius: FloatProperty(
        name="Radius",
        description="Radius of pose interpolation (factor of pose distance)",
        min=0.0,
        max=10.0,
        soft_min=0.0,
        soft_max=2.0,
        default=1.0,
        options=set(),
        update=driver_falloff_radius_update_handler
        )

    @property
    def rbf_driver(self) -> 'RBFDriver':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])

    def update(self, _=None) -> None:
        driver = self.rbf_driver
        radius = self.radius
        curve = self.curve
        poses = driver.poses
        shape = driver.type == 'SHAPE_KEYS'

        for index, pose in enumerate(poses):
            if not pose.falloff.enabled:
                pose_weight_fcurve_update(poses, index, radius, curve, shape)


class RBFDriver(Identifiable, PropertyGroup):

    falloff: PointerProperty(
        name="Falloff",
        type=RBFDriverFalloff,
        options=set()
        )

    inputs: PointerProperty(
        name="Inputs",
        type=RBFDriverInputs,
        options=set()
        )

    outputs: PointerProperty(
        name="Outputs",
        type=RBFDriverOutputs,
        options=set()
        )

    poses: PointerProperty(
        name="Poses",
        type=RBFDriverPoses,
        options=set()
        )

    @property
    def reference_pose(self) -> Optional[RBFDriverPose]:
        return self.poses[0] if len(self.poses) else None

    type: EnumProperty(
        items=DRIVER_TYPE_ITEMS,
        get=lambda self: self.get("type", 0),
        options=set()
        )

    def update(self) -> None:

        inputs = self.inputs
        poses = self.poses
        pose_count = len(self.poses)

        for input in inputs:
            input_pose_radii_update(input)
            input_pose_distance_idprop_update(input, pose_count)
            input_pose_distance_driver_update_all(input, pose_count)
            input_pose_distance_fcurve_update_all(input, pose_count)

        input_influence_sum_idprop_ensure(inputs)
        input_influence_sum_driver_update(inputs)
        
        pose_distance_sum_idprop_update(poses)
        pose_distance_sum_driver_update_all(poses, inputs)
        
        radius_basis = self.falloff.radius
        default_curve = self.falloff.curve
        shape_keys = self.type == 'SHAPE_KEYS'

        if not shape_keys:
            pose_weight_idprop_update(poses)

        pose_weight_driver_update_all(poses, inputs, shape_keys)
        pose_weight_fcurve_update_all(poses, radius_basis, default_curve, shape_keys)

        for output in self.outputs:
            output.update()


class RBFDrivers(PropertyGroup):

    active_index: IntProperty(
        name="Index",
        description="Index of the active pose",
        min=0,
        default=0,
        options=set(),
        )

    @property
    def active(self) -> Optional[RBFDriver]:
        index = self.active_index
        return self[index] if index < len(self) else None

    collection__internal__: CollectionProperty(
        type=RBFDriver,
        options={'HIDDEN'}
        )

    def __len__(self) -> int:
        return len(self.collection__internal__)

    def __getitem__(self, key: Union[str, int, slice]) -> Union[RBFDriver, List[RBFDriver]]:
        return self.collection__internal__[key]

    def __contains__(self, name: str) -> bool:
        return name in self.collection__internal__

    def __iter__(self) -> Iterator[RBFDriver]:
        return iter(self.collection__internal__)

    def find(self, name: str) -> int:
        return self.collection__internal__.find(name)

    def get(self, name: str, default: Optional[object]=None) -> Any:
        return self.collection__internal__.get(name, default)

    def keys(self) -> List[str]:
        return self.collection__internal__.keys()

    def items(self) -> List[Tuple[str, RBFDriver]]:
        return self.collection__internal__.items()

    def values(self) -> List[RBFDriver]:
        return list(self)

#endregion Properties
