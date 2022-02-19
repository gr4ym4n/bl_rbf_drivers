
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union, TYPE_CHECKING
import sys
import logging
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, FloatProperty, IntProperty, PointerProperty, StringProperty
from rbf_drivers.lib.rotation_utils import euler_to_quaternion, swing_twist_to_quaternion
from .lib.driver_utils import driver_ensure, driver_remove, driver_variables_clear
from .lib.curve_mapping import BCLMAP_CurveManager, BLCMAP_Curve, keyframe_points_assign, to_bezier
from .mixins import LAYER_TYPE_ITEMS, Identifiable, Symmetrical
from .input import RBFDriverInputs, input_pose_data_update, input_pose_distance_driver_update, input_pose_distance_fcurve_update_all, input_pose_radii_update

if TYPE_CHECKING:
    from .driver import RBFDriver

DEBUG = 'DEBUG_MODE' in sys.argv

log = logging.getLogger('rbf_drivers')

def pose_falloff_radius_update_handler(falloff: 'RBFDriverPoseFalloff', _) -> None:
    if falloff.enabled:
        falloff.update()


def pose_falloff_enabled_update_handler(falloff: 'RBFDriverPoseFalloff', _) -> None:
    falloff.update()


class RBFDriverPoseFalloff(BCLMAP_CurveManager, PropertyGroup):

    enabled: BoolProperty(
        name="Enabled",
        default=False,
        options=set(),
        update=pose_falloff_enabled_update_handler
        )

    @property
    def pose(self) -> 'RBFDriverPose':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])

    radius: FloatProperty(
        name="Radius",
        description="Radius of pose interpolation (factor of pose distance)",
        min=0.0,
        max=10.0,
        soft_min=0.0,
        soft_max=2.0,
        default=1.0,
        options=set(),
        update=pose_falloff_radius_update_handler
        )

    def update(self, _=None) -> None:
        super().update()
        pose = self.pose
        driver = pose.rbf_driver
        pose_weight_fcurve_update(driver.poses,
                                  driver.poses.find(pose.name),
                                  driver.falloff.radius,
                                  driver.falloff.curve,
                                  driver.type == 'SHAPE_KEYS')

        if pose.has_symmetry_target:
            m_pose = pose_symmetry_target(pose)
            if m_pose is None:
                log.warning(f'Search failed for symmetry target of {driver}.')
            else:
                driver = m_pose.rbf_driver
                if not driver.symmetry_lock__internal__:
                    driver.symmetry_lock__internal__ = True
                    try:
                        falloff = m_pose.falloff
                        falloff["radius"] = self.radius
                        falloff["curve_type"] = self.get("curve_type")
                        falloff["easing"] = self.get("easing")
                        falloff["interpolation"] = self.get("interpolation")
                        falloff["offset"] = self.offset
                        falloff["ramp"] = self.ramp
                        falloff.curve.__init__(self.curve)
                        falloff.update()
                    finally:
                        driver.symmetry_lock__internal__ = False



def pose_name_get(pose: 'RBFDriverPose') -> str:
    return pose.get("name", "")


def pose_name_set(pose: 'RBFDriverPose', value: str) -> None:
    cache = pose_name_get(pose)
    if cache == value:
        return

    driver = pose.rbf_driver
    if driver.type == 'SHAPE_KEYS':
        key = driver.id_data.data.shape_keys
        if key:

            shape = key.key_blocks.get(value)
            if shape is not None:
                return

            shape = key.key_blocks.get(cache)
            if shape:
                shape.name = value
                pose["name"] = shape.name
                return

    names = [item.name for item in driver.poses if item != pose]
    value = pose.name
    index = 0
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

    name: StringProperty(
        name="Name",
        description="Unique pose name",
        get=pose_name_get,
        set=pose_name_set,
        options=set(),
        )

    @property
    def rbf_driver(self) -> 'RBFDriver':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".poses.")[0])


def poses_active_index_update_handler(poses: 'RBFDriverPoses', _) -> None:
    pose = poses.active

    if pose is not None:
        driver = pose.rbf_driver
        pose_index = poses.active_index

        for input in driver.inputs:
            input.active_pose.__init__(input, pose_index)

        for output in driver.outputs:
            output.active_pose.__init__(output, pose_index)

    else:
        driver = poses.id_data.path_resolve(poses.path_from_id().rpartition(".")[0])

        for input in driver.inputs:
            input.active_pose.data__internal__.clear()

        for output in driver.outputs:
            output.active_pose.data__internal__.clear()


class RBFDriverPoses(Identifiable, PropertyGroup):

    active_index: IntProperty(
        name="Index",
        description="Index of the active pose",
        min=0,
        default=0,
        options=set(),
        update=poses_active_index_update_handler
        )

    @property
    def active(self) -> Optional[RBFDriverPose]:
        index = self.active_index
        return self[index] if index < len(self) else None

    collection__internal__: CollectionProperty(
        type=RBFDriverPose,
        options={'HIDDEN'}
        )

    @property
    def weight_property_name(self) -> str:
        return f'rbfp_wgts_{self.identifier}'

    @property
    def weight_property_path(self) -> str:
        return f'["{self.weight_property_name}"]'

    @property
    def summed_distances_property_name(self) -> str:
        return f'rbfp_dist_{self.identifier}'

    @property
    def summed_distances_property_path(self) -> str:
        return f'["{self.summed_distances_property_name}"]'

    def __len__(self) -> int:
        return len(self.collection__internal__)

    def __getitem__(self, key: Union[str, int, slice]) -> Union[RBFDriverPose, List[RBFDriverPose]]:
        return self.collection__internal__[key]

    def __contains__(self, name: str) -> bool:
        return name in self.collection__internal__

    def __iter__(self) -> Iterator[RBFDriverPose]:
        return iter(self.collection__internal__)

    def find(self, name: str) -> int:
        return self.collection__internal__.find(name)

    def get(self, name: str, default: Optional[object]=None) -> Any:
        return self.collection__internal__.get(name, default)

    def keys(self) -> List[str]:
        return self.collection__internal__.keys()

    def items(self) -> List[Tuple[str, RBFDriverPose]]:
        return self.collection__internal__.items()

    def search(self, identifier: str) -> Optional[RBFDriverPose]:
        return next((pose for pose in self if pose.identifier == identifier), None)

    def values(self) -> List[RBFDriverPose]:
        return list(self)

#
#
#


def pose_symmetry_target(pose: RBFDriverPose) -> Optional[RBFDriverPose]:
    """
    """
    driver = pose.rbf_driver
    if not driver.has_symmetry_target:
        log.warning(f'Symmetry target defined for component {pose} but not for {driver}')
        return

    m_driver = driver.id_data.rbf_drivers.search(driver.symmetry_identifier)
    if m_driver is None:
        log.warning(f'Search failed for symmetry target of {driver}.')
        return

    return m_driver.poses.search(pose.symmetry_identifier)


def pose_symmetry_assign(a: RBFDriverPose, b: RBFDriverPose) -> None:
    a["symmetry_identifier"] = b.identifier
    b["symmetry_identifier"] = a.identifier


def pose_distance_sum_idprop_update(poses: RBFDriverPoses) -> None:
    poses.id_data.data[poses.summed_distances_property_name] = [0.0] * len(poses)


def pose_distance_sum_idprop_remove(poses: RBFDriverPoses) -> None:
    try:
        del poses.id_data.data[poses.summed_distances_property_name]
    except KeyError: pass


def pose_distance_sum_driver_update(poses: RBFDriverPoses, inputs: RBFDriverInputs, pose_index: int) -> None:
    fcurve = driver_ensure(poses.id_data.data, poses.summed_distances_property_path, pose_index)
    driver = fcurve.driver
    driver.type = 'SUM'
    driver_variables_clear(driver.variables)

    for index, input in enumerate(inputs):
        variable = driver.variables.new()
        variable.name = f'var_{str(index+1).zfill(3)}'
        variable.type = 'SINGLE_PROP'

        target = variable.targets[0]
        target.id_type = input.id_data.type
        target.id = input.id_data.data
        target.data_path = f'{input.pose_distance_property_path}[{pose_index}]'


def pose_distance_sum_driver_remove(poses: RBFDriverPoses, pose_index: int) -> None:
    driver_remove(poses.id_data.data, poses.summed_distances_property_path, pose_index)


def pose_distance_sum_driver_update_all(poses: RBFDriverPoses, inputs: RBFDriverInputs) -> None:
    for pose_index in range(len(poses)):
        pose_distance_sum_driver_update(poses, inputs, pose_index)


def pose_distance_sum_driver_remove_all(poses: RBFDriverPoses) -> None:
    for pose_index in range(len(poses)):
        pose_distance_sum_driver_remove(poses, pose_index)

#
#
#


def pose_weight_idprop_update(poses: RBFDriverPoses) -> None:
    poses.id_data.data[poses.weight_property_name] = [0.0] * len(poses)


def pose_weight_idprop_remove(poses: RBFDriverPoses) -> None:
    try:
        del poses.id_data.data[poses.weight_property_name]
    except KeyError: pass


def pose_weight_fcurve_update(poses: RBFDriverPoses,
                              pose_index: int,
                              radius_basis: float,
                              default_curve: BLCMAP_Curve,
                              shape_key: Optional[bool]=False) -> None:
    """
    """
    pose = poses[pose_index]
    fcurve = None

    if shape_key:
        key = poses.id_data.data.shape_keys
        if key:
            fcurve = driver_ensure(key, f'key_blocks["{pose.name}"].value')
    else:
        fcurve = driver_ensure(poses.id_data.data, poses.weight_property_path, pose_index)

    if fcurve:
        if pose.falloff.enabled:
            points = pose.falloff.curve.points
            radius = radius_basis * pose.falloff.radius
        else:
            points = default_curve.points
            radius = radius_basis

        keyframe_points_assign(fcurve.keyframe_points, to_bezier(points,
                                                                 x_range=(0.0, radius),
                                                                 y_range=(0.0, 1.0),
                                                                 extrapolate=False))


def pose_weight_driver_update(poses: RBFDriverPoses,
                              inputs: RBFDriverInputs,
                              pose_index: int,
                              shape_key: Optional[bool]=False) -> None:
    """
    """
    fcurve = None

    if shape_key:
        if pose_index == 0:
            return
        key = poses.id_data.data.shape_keys
        if key:
            fcurve = driver_ensure(key, f'key_blocks["{poses[pose_index].name}"].value')
    else:
        fcurve = driver_ensure(poses.id_data.data, poses.weight_property_path, pose_index)

    if fcurve:
        driver = fcurve.driver
        driver.type = 'SCRIPTED'
        driver.expression = '0.0 if influence == 0.0 else distance / influence'
        driver_variables_clear(driver.variables)

        variable = driver.variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = "distance"

        target = variable.targets[0]
        target.id_type = poses.id_data.type
        target.id = poses.id_data.data
        target.data_path = f'{poses.summed_distances_property_path}[{pose_index}]'

        variable = driver.variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = "influence"

        target = variable.targets[0]
        target.id_type = inputs.id_data.type
        target.id = inputs.id_data.data
        target.data_path = inputs.summed_influence_property_path


def pose_weight_driver_remove(poses: RBFDriverPoses,
                              pose_index: int,
                              shape_key: Optional[bool]=False) -> None:
    """
    """
    id = poses.id_data.data

    if shape_key:
        key = id.shape_keys
        if key:
            driver_remove(key, f'key_blocks["{poses[pose_index].name}"].value')
    else:
        driver_remove(id, poses.weight_property_path, pose_index)


def pose_weight_fcurve_update_all(poses: RBFDriverPoses,
                                  radius_basis: float,
                                  default_curve: BLCMAP_Curve,
                                  shape_keys: Optional[bool]=False) -> None:
    """
    """
    for pose_index in range(len(poses)):
        pose_weight_fcurve_update(poses, pose_index, radius_basis, default_curve, shape_keys)


def pose_weight_driver_update_all(poses: RBFDriverPoses,
                                  inputs: RBFDriverInputs,
                                  shape_keys: Optional[bool]=False) -> None:
    """
    """
    for pose_index in range(len(poses)):
        pose_weight_driver_update(poses, inputs, pose_index, shape_keys)


def pose_weight_driver_remove_all(poses: RBFDriverPoses,
                                  shape_keys: Optional[bool]=None) -> None:
    """
    """
    for pose_index in range(len(poses)):
        pose_weight_driver_remove(poses, pose_index, shape_keys)

#
#
#