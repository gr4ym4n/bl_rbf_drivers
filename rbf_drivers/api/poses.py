
from typing import Any, Iterator, List, Optional, Tuple, Union, TYPE_CHECKING
from logging import getLogger
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, IntProperty, PointerProperty
from .pose_weight_property import RBFDriverPoseWeightProperty
from .pose_weight_driver import RBFDriverPoseWeightDriver
from .pose_weight import RBFDriverPoseWeight
from .pose_weight_normalized_property import RBFDriverPoseWeightNormalizedProperty
from .pose_weight_normalized_driver import RBFDriverPoseWeightNormalizedDriver
from .pose_weight_normalized import RBFDriverPoseWeightNormalized
from .pose import RBFDriverPose
from .poses_weight_sum_driver import RBFDriverPosesWeightSumDriver
from .poses_weight_sum_property import RBFDriverPosesWeightSumProperty
from .poses_weight_sum import RBFDriverPosesWeightSum
if TYPE_CHECKING:
    from .input_variable_data_sample import RBFDriverInputVariableDataSample
    from .input_variable_data import RBFDriverInputVariableData
    from .input_variable import RBFDriverInputVariable
    from .input_distance_property import RBFDriverInputDistanceProperty
    from .input_distance_driver import RBFDriverInputDistanceDriver
    from .input_distance_matrix import RBFDriverInputDistanceMatrix
    from .input import RBFDriverInput
    from .driver_distance_matrix import RBFDriverDistanceMatrix
    from .driver_variable_matrix import RBFDriverVariableMatrix
    from .driver import RBFDriver

log = getLogger("rbf_drivers")

class RBFDriverPoses(PropertyGroup):

    active_index: IntProperty(
        name="Shape Key",
        min=0,
        default=0,
        options=set()
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
    def rbf_driver(self) -> 'RBFDriver':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])

    weight_sum: PointerProperty(
        name="Weights",
        type=RBFDriverPosesWeightSum,
        options=set()
        )

    def __len__(self) -> int:
        return len(self.collection__internal__)

    def __iter__(self) -> Iterator[RBFDriverPose]:
        return iter(self.collection__internal__)

    def __getitem__(self, key: Union[str, int, slice]) -> Union[RBFDriverPose, List[RBFDriverPose]]:
        return self.collection__internal__[key]

    def find(self, name: str) -> int:
        return self.collection__internal__.find(name)

    def keys(self) -> Iterator[str]:
        return iter(self.collection__internal__.keys())

    def get(self, name: str, default: Any) -> Any:
        return self.collection__internal__.get(name, default)

    def items(self) -> Iterator[Tuple[str, RBFDriverPose]]:
        for item in self:
            yield item.name, item

    def new(self, name: Optional[str]="") -> RBFDriverPose:
        rbf_driver = self.rbf_driver

        log.info("Adding new pose")
        pose: RBFDriverPose = self.collection__internal__.add()
        pose.name = name or "Pose"

        input: RBFDriverInput
        for input in rbf_driver.inputs:

            variable: RBFDriverInputVariable
            for variable in input.variables:
                data: RBFDriverInputVariableData = variable.data
                item: RBFDriverInputVariableDataSample = input.variables.data.data__internal__.add()
                item.__init__(len(data)-1, variable.value)

            matrix: RBFDriverInputDistanceMatrix = input.distance.matrix
            matrix.update(propagate=False)

            idprop: RBFDriverInputDistanceProperty = input.distance.id_property
            idprop.update()
            driver: RBFDriverInputDistanceDriver = input.distance.drivers.collection__internal__.add()
            driver.update()

        matrix: RBFDriverInputDistanceMatrix = rbf_driver.distance.matrix
        matrix.update(propagate=False)

        matrix: RBFDriverDistanceMatrix = rbf_driver.distance_matrix
        matrix.update(propagate=False)

        matrix: RBFDriverVariableMatrix = rbf_driver.variable_matrix
        matrix.update(propagate=False)

        weight: RBFDriverPoseWeight = pose.weight
        idprop: RBFDriverPoseWeightProperty = weight.id_property
        driver: RBFDriverPoseWeightDriver = weight.driver
        idprop.update()
        driver.update()

        weight: RBFDriverPosesWeightSum = self.weight_sum
        idprop: RBFDriverPosesWeightSumProperty = weight.id_property
        driver: RBFDriverPosesWeightSumDriver = weight.driver
        idprop.update()
        driver.update()

        weight: RBFDriverPoseWeightNormalized = self.weight.normalized
        idprop: RBFDriverPoseWeightNormalizedProperty = weight.id_property
        driver: RBFDriverPoseWeightNormalizedDriver = weight.driver
        idprop.update()
        driver.update()

        # TODO mirror pose

        return pose

    def remove(self, pose: RBFDriverPose) -> None:

        if not isinstance(pose, RBFDriverPose):
            raise TypeError((f'{self.__class__.__name__}.remove(pose): '
                             f'Expected pose to be RBFDriverPose, not {pose.__class__.__name__}'))

        index = next((index for index, item in enumerate(self) if item == pose), -1)

        if index == -1:
            raise ValueError((f'{self.__class__.__name__}.remove(pose): '
                             f'pose is not a member of this collection'))

        if index == 0:
            raise RuntimeError((f'{self.__class__.__name__}.remove(pose): '
                                f'pose is rest pose and cannot be removed'))

        # TODO lots of stuff

        self.collection__internal__.remove(index)

    def search(self, identifier: str) -> Optional[RBFDriverPose]:
        return next((item for item in self if item.identifier == identifier), None)

    def values(self) -> Iterator[RBFDriverPose]:
        return iter(self)
