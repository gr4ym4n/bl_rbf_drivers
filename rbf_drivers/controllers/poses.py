
from typing import Iterator, List, Optional, Tuple, Union
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, FloatProperty, StringProperty
from .mixins import Observable


def pose_name_get(pose: 'Pose') -> str:
    return pose.get("name", "")


def pose_name_set(pose: 'Pose', name: str) -> None:
    cache = pose.name
    poses = pose.id_data.path_resolve(pose.path_from_id().rpartition(".internal__")[0])
    names = poses.keys()
    index = 0
    value = name
    while value in names:
        index += 1
        value = f'{name}.{str(index).zfill(3)}'
    pose["name"] = value
    pose.dispatch("name", value, cache)


def pose_radius_get(pose: 'Pose') -> float:
    return pose.get("radius", 0.0)


def pose_radius_set(pose: 'Pose', value: float) -> None:
    cache = pose.radius
    pose["radius"] = value
    pose.notify_observers("radius", value, cache)


class Pose(Observable, PropertyGroup):

    name: StringProperty(
        name="Name",
        description="Unique pose name",
        get=pose_name_get,
        set=pose_name_set,
        options=set()
        )

    radius: FloatProperty(
        name="Radius",
        description="",
        get=pose_radius_get,
        set=pose_radius_set,
        options=set()
        )


class Poses(Observable, PropertyGroup):

    internal__: CollectionProperty(
        type=Pose,
        options={'HIDDEN'}
        )

    def __iter__(self) -> Iterator[Pose]:
        return iter(self.internal__)

    def __len__(self) -> int:
        return len(self.internal__)

    def __getitem__(self, key: Union[str, int, slice]) -> Union[Pose, List[Pose]]:
        return self.internal__[key]

    def find(self, name: str) -> int:
        return self.internal__.find(name)

    def get(self, name: str) -> Optional[Pose]:
        return self.internal__.get(name)

    def items(self) -> Iterator[Tuple[str, Pose]]:
        return self.internal__.items()

    def keys(self) -> Iterator[str]:
        return self.internal__.keys()

    def new(self, name: Optional[str]="Pose") -> Pose:
        if not isinstance(name, str):
            raise TypeError()
        pose = self.internal__.add()
        pose.name = name
        self.notify_observers("new", pose)
