
#region Imports
###################################################################################################

from typing import Any, Iterator, List, Optional, Tuple, Union
import logging
import numpy as np
from bpy.types import PropertyGroup
from bpy.props import (BoolProperty,
                       CollectionProperty,
                       EnumProperty,
                       FloatProperty,
                       IntProperty,
                       PointerProperty)
from rbf_drivers.posedata import RBFDriverPoseDataMatrix

from .lib.curve_mapping import BCLMAP_CurveManager
from .lib.symmetry import symmetrical_target

from .mixins import Symmetrical

from .input import (RBFDriverInputs,
                    input_influence_sum_driver_update,
                    input_influence_sum_idprop_ensure,
                    input_pose_distance_driver_update_all,
                    input_pose_distance_fcurve_update_all,
                    input_pose_distance_idprop_update, input_pose_distance_matrix, input_pose_distance_matrix_update,
                    input_pose_radii_update)

from .pose import (RBFDriverPose,
                   RBFDriverPoses,
                   pose_distance_sum_driver_update_all,
                   pose_distance_sum_idprop_update, pose_variable_idprop_update,
                   pose_weight_driver_update_all,
                   pose_weight_fcurve_update,
                   pose_weight_fcurve_update_all,
                   pose_weight_idprop_update, pose_weight_normalized_driver_update_all, pose_weight_normalized_idprop_update, pose_weight_sum_driver_update, pose_weight_sum_idprop_update)

from .output import RBFDriverOutputs

#endregion Imports

#region Configuration
###################################################################################################

log = logging.getLogger("rbf_drivers")

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
        super().update()
        driver = self.rbf_driver
        radius = self.radius
        curve = self.curve
        poses = driver.poses
        shape = driver.type == 'SHAPE_KEYS'

        for index, pose in enumerate(poses):
            if not pose.falloff.enabled:
                pose_weight_fcurve_update(poses, index, radius, curve, shape)

        if driver.has_symmetry_target and not driver.symmetry_lock__internal__:
            mirror: RBFDriver = driver.id_data.rbf_drivers.search(driver.symmetry_identifier)
            if mirror is None:
                log.warning(f'Search failed for symmetry target of {driver}.')
            else:
                mirror.symmetry_lock__internal__ = True
                try:
                    falloff = mirror.falloff
                    falloff["radius"] = self.radius
                    falloff["curve_type"] = self.get("curve_type")
                    falloff["easing"] = self.get("easing")
                    falloff["interpolation"] = self.get("interpolation")
                    falloff["offset"] = self.offset
                    falloff["ramp"] = self.ramp
                    falloff.curve.__init__(self.curve)
                    falloff.update()
                finally:
                    mirror.symmetry_lock__internal__ = False


class RBFDriver(Symmetrical, PropertyGroup):

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

    pose_distance_matrix: PointerProperty(
        name="Pose Distances",
        type=RBFDriverPoseDataMatrix,
        options=set()
        )

    @property
    def reference_pose(self) -> Optional[RBFDriverPose]:
        return self.poses[0] if len(self.poses) else None

    symmetry_lock__internal__: BoolProperty(
        default=False,
        options=set()
        )

    type: EnumProperty(
        items=DRIVER_TYPE_ITEMS,
        get=lambda self: self.get("type", 0),
        options=set()
        )

    def get_symmetry_target(self) -> Optional['RBFDriver']:
        name = symmetrical_target(self.name)
        if name:
            return self.id_data.rbf_drivers.get(name)

    def pose_distance_matrix_update(self) -> None:
        matrices = [
            np.array(list(i.pose_distance_matrix.values()), dtype=float) for i in self.inputs
            ]

        count = len(matrices)

        if count == 0:
            matrix = None
        elif count == 1:
            matrix = matrices[0]
        else:
            matrix = np.add.reduce(matrices)
            matrix /= float(len(matrices))

        self.pose_distance_matrix.__init__(matrix)

    def solution_update(self) -> None:
        distance_matrix = self.pose_distance_matrix

        if len(distance_matrix) == 0:
            for pose in self.poses:
                pose_variable_idprop_update(pose, [])
        else:
            distance_matrix = np.array(list(distance_matrix.values()), dtype=float)
            identity_matrix = np.identity(distance_matrix.shape[0], dtype=float)

            try:
                solution = np.linalg.solve(distance_matrix, identity_matrix)
            except np.linalg.LinAlgError:
                solution = np.linalg.lstsq(distance_matrix, identity_matrix, rcond=None)[0]

            for pose, data in zip(self.poses, solution.T):
                pose_variable_idprop_update(pose, list(data))

    def update(self) -> None:

        inputs = self.inputs
        poses = self.poses
        pose_count = len(self.poses)

        for input in inputs:
            matrix = input_pose_distance_matrix(input)
            input_pose_distance_matrix_update(input, matrix)
            input_pose_radii_update(input, matrix)
            input_pose_distance_idprop_update(input, pose_count)
            input_pose_distance_driver_update_all(input, pose_count)
            input_pose_distance_fcurve_update_all(input, pose_count)

        # self.pose_distance_matrix_update()
        # self.solution_update()

        input_influence_sum_idprop_ensure(inputs)
        input_influence_sum_driver_update(inputs)
        
        pose_distance_sum_idprop_update(poses)
        pose_distance_sum_driver_update_all(poses, inputs)
        
        radius_basis = self.falloff.radius
        default_curve = self.falloff.curve
        shape_keys = self.type == 'SHAPE_KEYS'

        if not shape_keys:
            pose_weight_idprop_update(poses)
            pose_weight_sum_idprop_update(poses)
            pose_weight_normalized_idprop_update(poses)

        pose_weight_driver_update_all(poses, inputs, shape_keys)
        pose_weight_fcurve_update_all(poses, radius_basis, default_curve, shape_keys)

        pose_weight_sum_driver_update(poses)
        pose_weight_normalized_driver_update_all(poses)

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

    def search(self, identifier: str) -> Optional[RBFDriver]:
        return next((driver for driver in self if driver.identifier == identifier), None)

    def values(self) -> List[RBFDriver]:
        return list(self)

#endregion Properties
