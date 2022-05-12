
from typing import Optional, TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, CollectionProperty, IntProperty
from .mixins import Collection, Reorderable, Searchable
from .pose import RBFDriverPose
from ..app.events import dataclass, dispatch_event, Event
if TYPE_CHECKING:
    from bpy.types import Context


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


class RBFDriverPoses(Reorderable,
                     Searchable[RBFDriverPose],
                     Collection[RBFDriverPose],
                     PropertyGroup):

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

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(active_index={self.active_index})'

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".collection__internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'

    def move(self, from_index: int, to_index: int) -> None:
        super().move(from_index, to_index)
        dispatch_event(PoseMoveEvent(self[to_index], from_index, to_index))

    def new(self, name: Optional[str]="") -> RBFDriverPose:
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
