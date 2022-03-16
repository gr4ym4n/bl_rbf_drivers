
from typing import Iterable, Iterator, List, Optional, Tuple, Union
from contextlib import suppress
from logging import getLogger
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty
from .input_distance_property import RBFDriverInputDistanceProperty
from .input_distance_driver import RBFDriverInputDistanceDriver
from .input import RBFDriverInput
from .pose_weight_property import RBFDriverPoseWeightProperty
from .pose_weight_driver import RBFDriverPoseWeightDriver
from .pose_weight_normalized_property import RBFDriverPoseWeightNormalizedProperty
from .pose_weight_normalized_driver import RBFDriverPoseWeightNormalizedDriver
from .pose_weight_normalized import RBFDriverPoseWeightNormalized
from .pose_weight import RBFDriverPoseWeight
from .pose import RBFDriverPose
from .poses_weight_sum_property import RBFDriverPosesWeightSumProperty
from .poses_weight_sum_driver import RBFDriverPosesWeightSumDriver
from .poses_weight_sum import RBFDriverPosesWeightSum
from .driver import RBFDriver
from ..lib.driver_utils import driver_remove
from ..lib.curve_mapping import BLCMAP_Curve, nodetree_node_remove

log = getLogger("rbf_drivers")

class RBFDrivers(PropertyGroup):

    collection__internal__: CollectionProperty(
        type=RBFDriver,
        options={'HIDDEN'}
        )

    def __len__(self) -> int:
        return len(self.collection__internal__)

    def __iter__(self) -> Iterator[RBFDriver]:
        return iter(self.collection__internal__)

    def __getitem__(self, key: Union[str, int, slice]) -> Union[RBFDriver, List[RBFDriver]]:
        return self.collection__internal__.get(key)

    def find(self, name: str) -> int:
        return self.collection__internal__.find(name)

    def get(self, name: str, default: Optional[object]=None) -> Optional[RBFDriver]:
        return self.collection__internal__.get(name, default)

    def keys(self) -> Iterable[str]:
        return self.collection__internal__.keys()

    def items(self) -> Iterable[Tuple[str, RBFDriver]]:
        return self.collection__internal__.items()

    def new(self, name: Optional[str]="") -> RBFDriver:
        log.info(f'Creating new RBF driver at {self.id_data}')

        driver = self.collection__internal__.add()
        driver.name = name or "RBFDriver"

        log.info(f'Adding rest pose')
        driver.poses.new(name="Rest")

        log.info(f'Created new RBF driver "{driver.name}" at {self.id_data}')
        return driver

    def remove(self, rbf_driver: RBFDriver) -> None:

        if not isinstance(rbf_driver, RBFDriver):
            raise TypeError((f'{self.__class__.__name__}.remove(driver): '
                             f'Expected driver to be RBFDriver, not {rbf_driver.__class__.__name__}'))

        index = next((index for index, item in enumerate(self) if item == rbf_driver), -1)

        if index == -1:
            raise ValueError((f'{self.__class__.__name__}.remove(driver): '
                              f'driver is not a member of this collection'))

        log.info(f'Removing RBF driver {rbf_driver}')

        input: RBFDriverInput
        for input in rbf_driver.inputs:
            driven: RBFDriverInputDistanceProperty = input.distance.id_property
            driver: RBFDriverInputDistanceDriver

            for driver in input.distance.drivers:
                log.info(f'Removing input distance driver for pose {driver.array_index}')
                driver_remove(driven.id, driven.data_path, driver.array_index)

            log.info(f'Removing input distance property for pose {driver.array_index}')
            with suppress(KeyError):
                del driven.id[driven.name]

        pose: RBFDriverPose
        for pose_index, pose in enumerate(rbf_driver.poses):
            log.info(f'Removing pose data and drivers for pose {pose_index}')

            weight: RBFDriverPoseWeight = pose.weight
            driven: RBFDriverPoseWeightProperty = weight.id_property
            driver: RBFDriverPoseWeightDriver = weight.driver

            log.info(f'Removing pose weight driver for pose {pose_index}')
            driver_remove(driven.id, driven.data_path, driver.array_index)

            log.info(f'Removing pose weight property for pose {pose_index}')
            with suppress(KeyError):
                del driven.id[driven.name]

            weight: RBFDriverPoseWeightNormalized = weight.normalized
            driven: RBFDriverPoseWeightNormalizedProperty = weight.id_property
            driver: RBFDriverPoseWeightNormalizedDriver = weight.driver

            log.info(f'Removing normalized pose weight driver for pose {pose_index}')
            driver_remove(driven.id, driven.data_path, driver.array_index)

            log.info(f'Removing normalized pose weight property for pose {pose_index}')
            with suppress(KeyError):
                del driven.id[driven.name]

            log.info(f'Removing pose falloff curve node for pose {pose_index}')
            curve: BLCMAP_Curve = pose.falloff.curve
            nodetree_node_remove(curve.node_identifier)

        weight: RBFDriverPosesWeightSum = rbf_driver.poses.weight
        driven: RBFDriverPosesWeightSumProperty = weight.id_property
        driver: RBFDriverPosesWeightSumDriver = weight.driver

        log.info(f'Removing poses weight sum driver')
        driver_remove(driven.id, driven.data_path)

        log.info(f'Removing poses weight sum property')
        with suppress(KeyError):
            del driven.id[driven.name]

        log.info(f'Removing RBF driver falloff curve node')
        curve: BLCMAP_Curve = rbf_driver.falloff.curve
        nodetree_node_remove(curve.node_identifier)

        log.info(f'Removing RBF driver properties')
        self.collection__internal__.remove(index)
        self.active_index = min(self.active_index, len(self)-1)

    def search(self, identifier: str) -> Optional[RBFDriver]:
        return next((item for item in self if item.identifier == identifier), None)

    def values(self) -> Iterable[RBFDriver]:
        return self.collection__internal__.values()