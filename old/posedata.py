
from typing import Generic, Iterable, Iterator, List, Optional, Sequence, Tuple, TypeVar, Union
from functools import partial
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, EnumProperty, FloatProperty
from .mixins import LAYER_TYPE_ITEMS
from .lib.rotation_utils import (axis_angle_to_euler,
                                 axis_angle_to_quaternion,
                                 euler_to_axis_angle,
                                 euler_to_quaternion,
                                 quaternion_to_axis_angle,
                                 quaternion_to_euler)


ACTIVE_POSE_DATA_ROTATION_MODE_ITEMS = [
    ('EULER', "Euler", "Euler angles"),
    ('QUATERNION', "Quaternion", "Quaternion rotation"),
    ('AXIS_ANGLE', "Axis/Angle", "Axis and angle rotation"),
    ]

ACTIVE_POSE_DATA_ROTATION_MODE_INDEX = {
    index: item[0] for index, item in enumerate(ACTIVE_POSE_DATA_ROTATION_MODE_ITEMS)
    }

ACTIVE_POSE_DATA_ROTATION_CONVERSION_LUT = {
    'EULER': {
        'QUATERNION': lambda seq: euler_to_quaternion(seq[1:]),
        'AXIS_ANGLE': lambda seq: euler_to_axis_angle(seq[1:], vectorize=True),
        },
    'QUATERNION': {
        'EULER': lambda seq: (0.0,) + tuple(quaternion_to_euler(seq)),
        'AXIS_ANGLE': partial(quaternion_to_axis_angle, vectorize=True),
        },
    'AXIS_ANGLE': {
        'EULER': lambda seq: (0.0,) + tuple(axis_angle_to_euler(seq)),
        'QUATERNION': axis_angle_to_quaternion
        }
    }

RBFDriverLayer = TypeVar("RBFDriverLayer")


class RBFDriverPoseDataScalar(PropertyGroup):

    angle: FloatProperty(
        name="Value",
        subtype='ANGLE',
        get=lambda self: self.get("value", 0.0),
        options=set()
        )

    value: FloatProperty(
        name="Value",
        get=lambda self: self.get("value", 0.0),
        options=set()
        )


class RBFDriverPoseDataVector(PropertyGroup):

    data__internal__: CollectionProperty(
        type=RBFDriverPoseDataScalar,
        options={'HIDDEN'}
        )

    def __len__(self) -> int:
        return len(self.data__internal__)

    def __getitem__(self, key: Union[int, slice]) -> Union[RBFDriverPoseDataScalar, List[RBFDriverPoseDataScalar]]:
        return self.data__internal__[key]

    def __iter__(self) -> Iterator[RBFDriverPoseDataScalar]:
        return iter(self.data__internal__)

    def __init__(self, data: Optional[Iterable[float]]=None) -> None:
        scalars = self.data__internal__
        scalars.clear()
        if data is not None:
            for value in data:
                scalars.add()["value"] = value

    def values(self) -> Iterator[float]:
        for scalar in self:
            yield scalar.value


class RBFDriverPoseDataMatrix(PropertyGroup):

    data__internal__: CollectionProperty(
        type=RBFDriverPoseDataVector,
        options={'HIDDEN'}
        )

    def __len__(self) -> int:
        return len(self.data__internal__)

    def __iter__(self) -> Iterator[RBFDriverPoseDataVector]:
        return iter(self.data__internal__)

    def __init__(self, data: Optional[Sequence[Sequence[float]]]=None) -> None:
        rows = self.data__internal__
        rows.clear()
        if data is not None:
            for seq in data:
                rows.add().__init__(seq)

    def values(self) -> Iterator[Tuple[float]]:
        for vector in self:
            yield tuple(vector.values())


def input_pose_value_get(data: 'RBFDriverActivePoseDataValue') -> float:
    return data.value


def input_pose_value_set(data: 'RBFDriverActivePoseDataValue', value: float) -> None:
    data.value = value


def input_pose_value_update_handler(data: 'RBFDriverActivePoseDataValue', _) -> None:
    data.owner.update()


class RBFDriverActivePoseDataValue(PropertyGroup):

    angle: FloatProperty(
        name="Value",
        subtype='ANGLE',
        get=input_pose_value_get,
        set=input_pose_value_set,
        precision=3,
        options=set()
        )

    easing: FloatProperty(
        min=-5.0,
        max=5.0,
        get=input_pose_value_get,
        set=input_pose_value_set,
        precision=3,
        options=set()
        )

    @property
    def owner(self) -> 'ActivePoseData':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])

    value: FloatProperty(
        name="Value",
        default=0.0,
        update=input_pose_value_update_handler,
        precision=3,
        options=set()
        )


def input_active_pose_data_rotation_mode_get(data: 'ActivePoseData') -> int:
    return data.get("rotation_mode", 1)


def input_active_pose_data_rotation_mode_set(data: 'ActivePoseData', value: int) -> None:
    cache = input_active_pose_data_rotation_mode_get(data)
    if cache != value:
        data["rotation_mode"] = value
        if data.type == 'ROTATION':
            prevmode = ACTIVE_POSE_DATA_ROTATION_MODE_INDEX[cache]
            currmode = ACTIVE_POSE_DATA_ROTATION_MODE_INDEX[value]
            for item, value in zip(data, ACTIVE_POSE_DATA_ROTATION_CONVERSION_LUT[prevmode][currmode](list(data.values()))):
                item["value"] = value


class ActivePoseData(Generic[RBFDriverLayer]):

    data__internal__: CollectionProperty(
        type=RBFDriverActivePoseDataValue,
        options={'HIDDEN'}
        )

    @property
    def layer(self) -> RBFDriverLayer:
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])

    rotation_mode: EnumProperty(
        name="Edit Mode",
        items=ACTIVE_POSE_DATA_ROTATION_MODE_ITEMS,
        get=input_active_pose_data_rotation_mode_get,
        set=input_active_pose_data_rotation_mode_set,
        options=set()
        )

    type: EnumProperty(
        name="Type",
        items=LAYER_TYPE_ITEMS,
        get=lambda self: self.get("type", 0),
        options=set()
        )

    def __iter__(self) -> Iterator[RBFDriverActivePoseDataValue]:
        return iter(self.data__internal__)

    def __len__(self) -> int:
        return len(self.data__internal__)

    def __getitem__(self, key: Union[int, slice]) -> Union[RBFDriverActivePoseDataValue, List[RBFDriverActivePoseDataValue]]:
        return self.data__internal__[key]

    def __init__(self, layer: RBFDriverLayer, pose_index: int) -> None:
        raise NotImplementedError()

    def update(self) -> None:
        raise NotImplementedError()

    def values(self) -> Iterator[float]:
        for item in self:
            yield item.value
