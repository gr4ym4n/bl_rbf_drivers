
from typing import Optional, TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty
    )
from .pose_interpolation import PoseInterpolation
from .mixins import Collection, Reorderable, Searchable, Symmetrical, IDPropertyController
from .pose_weight import PoseWeight
from ..app.events import dataclass, dispatch_event, Event
from ..app.utils import name_unique, driver_ensure, driver_variables_clear
if TYPE_CHECKING:
    from .input_data import InputSample
    from .input_variables import InputVariable
    from .poses import Poses
    from .driver import RBFDriver


class PoseInfluence(IDPropertyController, PropertyGroup):

    @property
    def pose(self) -> 'Pose':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])

    def __init__(self, pose: 'Pose') -> None:
        super().__init__(f'rbf_pose_{pose.identifier}_influence', True, min=0.0, soft_max=1.0)


@dataclass(frozen=True)
class PoseNameUpdateEvent(Event):
    pose: 'Pose'
    value: str
    previous_value: str


@dataclass(frozen=True)
class PoseRadiusUpdateEvent(Event):
    pose: 'Pose'
    value: float


def pose_name(pose: 'Pose') -> str:
    return pose.get("name", "")


def pose_name_set(pose: 'Pose', value: str) -> None:
    cache = pose.name
    value = name_unique(value, [p.name for p in pose.driver.poses if p != pose])
    pose["name"] = value
    dispatch_event(PoseNameUpdateEvent(pose, value, cache))


def pose_radius_update_handler(pose: 'Pose', _) -> None:
    pose.weight._update({'FCURVE'})
    dispatch_event(PoseRadiusUpdateEvent(pose, pose.radius))


class Pose(Symmetrical, PropertyGroup):

    @property
    def driver(self) -> 'RBFDriver':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".poses")[0])

    @property
    def index(self) -> int:
        return self.driver.poses.index(self)

    interpolation: PointerProperty(
        name="Interpolation",
        type=PoseInterpolation,
        options=set()
        )

    influence: PointerProperty(
        name="Influence",
        type=PoseInfluence,
        options=set()
        )

    name: StringProperty(
        name="Name",
        description="Unique pose name",
        get=pose_name,
        set=pose_name_set,
        options=set()
        )

    radius: FloatProperty(
        name="Radius",
        description="",
        options=set(),
        update=pose_radius_update_handler
        )

    weight: PointerProperty(
        name="Weight",
        type=PoseWeight,
        options=set()
        )

    def __init__(self, name: str) -> None:
        self["name"] = name
        self.interpolation.__init__()
        self.influence.__init__(self)
        self.radius.__init__(self)
        self.weight.__init__(self)

    def __repr__(self) -> str:
        # TODO
        return super().__repr__()

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'


class SummedPoseWeights(IDPropertyController, PropertyGroup):

    @property
    def poses(self) -> 'Poses':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])

    def __init__(self, poses: 'Poses') -> None:
        key = f'rbf_{poses.driver.identifier}_summed_pose_weights'
        enable = poses.normalize_weights
        super().__init__(key, enable)


@dataclass(frozen=True)
class PoseNewEvent(Event):
    pose: 'Pose'


@dataclass(frozen=True)
class PoseDisposableEvent(Event):
    pose: Pose


@dataclass(frozen=True)
class PoseRemovedEvent(Event):
    poses: 'Poses'
    index: int


@dataclass(frozen=True)
class PoseMoveEvent(Event):
    pose: Pose
    from_index: int
    to_index: int


@dataclass(frozen=True)
class PoseActiveIndexUpdateEvent(Event):
    poses: 'Poses'
    value: int


@dataclass(frozen=True)
class PoseWeightsAreNormalizedUpdateEvent(Event):
    poses: 'Poses'
    value: bool


def poses_active_index_update_handler(poses: 'Poses', _) -> None:
    dispatch_event(PoseActiveIndexUpdateEvent(poses, poses.active_index))


def poses_normalize_weights_update_handler(poses: 'Poses', _) -> None:
    dispatch_event(PoseWeightsAreNormalizedUpdateEvent(poses, poses.normalize_weights))


class Poses(Reorderable, Searchable[Pose], Collection[Pose], PropertyGroup):

    internal__: CollectionProperty(
        type=Pose,
        options={'HIDDEN'}
        )

    active_index: IntProperty(
        name="Shape Key",
        min=0,
        default=0,
        options=set(),
        update=poses_active_index_update_handler
        )

    @property
    def active(self) -> Optional[Pose]:
        index = self.active_index
        return self[index] if index < len(self) else None

    @property
    def driver(self) -> 'RBFDriver':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])

    normalize_weights: BoolProperty(
        name="Normalized",
        default=True,
        options=set(),
        update=poses_normalize_weights_update_handler
        )

    summed_weights: PointerProperty(
        name="Summed Weights",
        type=SummedPoseWeights,
        options=set()
        )

    sync_interpolation: BoolProperty(
        name="Apply To All Poses",
        description="Synchronize pose interpolation settings",
        default=True,
        options=set(),
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(active_index={self.active_index})'

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'

    def move(self, from_index: int, to_index: int) -> None:
        super().move(from_index, to_index)
        dispatch_event(PoseMoveEvent(self[to_index], from_index, to_index))

    def new(self, name: Optional[str]="Pose") -> Pose:
        name = name_unique(name, list(self.keys()))

        pose: Pose = self.internal__.add()
        pose.__init__(name)

        for input in pose.driver.inputs:
            variable: 'InputVariable'
            for variable in input.variables:
                sample: 'InputSample' = variable.data.internal__.add()
                sample.__init__(value=variable.value)

        dispatch_event(PoseNewEvent(pose))

        self.active_index = len(self) - 1
        return pose

    def remove(self, pose: Pose) -> None:
        if not isinstance(pose, Pose):
            raise TypeError((f'{self.__class__.__name__}.remove(pose): '
                             f'Expected pose to be Pose, not {pose.__class__.__name__}'))

        index = next((index for index, item in enumerate(self) if item == pose), -1)
        if index == -1:
            raise ValueError((f'{self.__class__.__name__}.remove(pose): '
                             f'pose is not a member of this collection'))
        if index == 0:
            raise RuntimeError((f'{self.__class__.__name__}.remove(pose): '
                                f'pose is rest pose and cannot be removed'))

        for input in pose.driver.inputs:
            variable: 'InputVariable'
            for variable in input.variables:
                variable.data.internal__.remove(index)

        dispatch_event(PoseDisposableEvent(pose))

        self.internal__.remove(index)
        self.active_index = min(self.active_index, len(self) - 1)

        dispatch_event(PoseRemovedEvent(self, index))
