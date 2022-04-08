
from typing import Any, Iterator, List, Optional, Tuple, Union, TYPE_CHECKING
from logging import getLogger
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, CollectionProperty, IntProperty
from .pose import RBFDriverPose
from ..app.events import dataclass, dispatch_event, Event
if TYPE_CHECKING:
    from bpy.types import Context

log = getLogger("rbf_drivers")


@dataclass(frozen=True)
class PoseNewEvent(Event):
    pose: 'RBFDriverPose'


@dataclass(frozen=True)
class PoseDisposableEvent(Event):
    pose: RBFDriverPose


@dataclass(frozen=True)
class PoseRemovedEvent(Event):
    poses: 'RBFDriverPoses'
    index: int


@dataclass(frozen=True)
class PoseMoveEvent(Event):
    pose: RBFDriverPose
    from_index: int
    to_index: int


@dataclass(frozen=True)
class PoseActiveIndexUpdateEvent(Event):
    poses: 'RBFDriverPoses'
    value: int


def poses_active_index_update_handler(poses: 'RBFDriverPoses', _: 'Context') -> None:
    dispatch_event(PoseActiveIndexUpdateEvent(poses, poses.active_index))


class RBFDriverPoses(PropertyGroup):

    active_index: IntProperty(
        name="Shape Key",
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

    display_influence: BoolProperty(
        name="Influence",
        description="Show/Hide influence in list",
        default=True,
        options=set()
        )

    display_radius: BoolProperty(
        name="Radius",
        description="Show/Hide radius in list",
        default=True,
        options=set()
        )

    display_weight: BoolProperty(
        name="Weight",
        description="Show/Hide weight in list",
        default=True,
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

    def get(self, name: str, default: Any) -> Any:
        return self.collection__internal__.get(name, default)

    def keys(self) -> Iterator[str]:
        return iter(self.collection__internal__.keys())

    def index(self, pose: RBFDriverPose) -> int:
        if not isinstance(pose, RBFDriverPose):
            raise TypeError((f'{self.__class__.__name__}.index(pose): '
                             f'Expected pose to be RBFDriverPose, not {pose.__class__.__name__}'))

        return next(index for index, item in enumerate(self) if item == pose)

    def items(self) -> Iterator[Tuple[str, RBFDriverPose]]:
        for item in self:
            yield item.name, item

    def move(self, from_index: int, to_index: int) -> None:

        if not isinstance(from_index, int):
            raise TypeError((f'{self.__class__.__name__}.move(from_index, to_index): '
                             f'Expected from_index to be int, not {from_index.__class__.__name__}'))

        if not isinstance(to_index, int):
            raise TypeError((f'{self.__class__.__name__}.move(from_index, to_index): '
                             f'Expected to_index to be int, not {to_index.__class__.__name__}'))

        if 0 > from_index >= len(self):
            raise IndexError((f'{self.__class__.__name__}.move(from_index, to_index): '
                              f'from_index {from_index} out of range 0-{len(self)-1}'))

        if 0 > to_index >= len(self):
            raise IndexError((f'{self.__class__.__name__}.move(from_index, to_index): '
                              f'to_index {to_index} out of range 0-{len(self)-1}'))

        if from_index != to_index:
            self.collection__internal__.move(from_index, to_index)
            dispatch_event(PoseMoveEvent(self[to_index], from_index, to_index))

    def new(self, name: Optional[str]="") -> RBFDriverPose:
        log.info("Adding new pose")
        pose: RBFDriverPose = self.collection__internal__.add()
        pose.name = name or "Pose"
        dispatch_event(PoseNewEvent(pose))
        self.active_index = len(self) - 1
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

        dispatch_event(PoseDisposableEvent(pose))
        
        self.collection__internal__.remove(index)
        self.active_index = min(self.active_index, len(self) - 1)

        dispatch_event(PoseRemovedEvent(self, index))

    def search(self, identifier: str) -> Optional[RBFDriverPose]:
        return next((item for item in self if item.identifier == identifier), None)

    def values(self) -> Iterator[RBFDriverPose]:
        return iter(self)
