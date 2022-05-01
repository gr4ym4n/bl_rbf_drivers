
from typing import Any, Iterable, Iterator, List, Optional, Tuple, Union
from functools import partial
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, FloatProperty, IntProperty, StringProperty
from ..rbf_drivers.app.events import dataclass, dispatch_event, Event
from ..rbf_drivers.lib.rotation_utils import (axis_angle_to_euler,
                                  axis_angle_to_quaternion,
                                  euler_to_axis_angle,
                                  euler_to_quaternion,
                                  quaternion_to_axis_angle,
                                  quaternion_to_euler)

POSE_DATUM_TYPE_ITEMS = [
    ('VALUE' , "Float" , ""),
    ('ANGLE' , "Angle" , ""),
    ('EASING', "Easing", ""),
    ]

POSE_DATUM_TYPE_INDEX = {
    item[0]: index for index, item in enumerate(POSE_DATUM_TYPE_ITEMS)
    }

POSE_DATA_GROUP_TYPE_ITEMS = [
    ('NONE'      , "None"    , ""),
    ('EULER'     , "Euler", ""),
    ('QUATERNION', "Quaternion", ""),
    ('AXIS_ANGLE', "Axis/Angle"   , ""),
    ]

POSE_DATA_GROUP_TYPE_INDEX = {
    item[0]: index for index, item in enumerate(POSE_DATA_GROUP_TYPE_ITEMS)
    }

POSE_DATA_GROUP_ROTATION_CONVERSION_LUT = {
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


@dataclass(frozen=True)
class PoseDatumUpdateEvent(Event):
    datum: 'RBFDriverPoseDatum'
    value: float


def pose_datum_index(datum: 'RBFDriverPoseDatum') -> int:
    return datum.get("index", 0)


def pose_datum_is_enabled(datum: 'RBFDriverPoseDatum') -> bool:
    return datum.get("is_enabled", False)


def pose_datum_name(datum: 'RBFDriverPoseDatum') -> str:
    return datum.get("name", "")


def pose_datum_type(datum: 'RBFDriverPoseDatum') -> int:
    return datum.get("type", 0)


def pose_datum_value(datum: 'RBFDriverPoseDatum') -> float:
    return datum.value


def pose_datum_value_set(datum: 'RBFDriverPoseDatum', value: float) -> None:
    datum.value = value


def pose_datum_value_update_handler(datum: 'RBFDriverPoseDatum', _) -> None:
    dispatch_event(PoseDatumUpdateEvent(datum, datum.value))


class RBFDriverPoseDatum(PropertyGroup):

    angle: FloatProperty(
        name="Value",
        subtype='ANGLE',
        get=pose_datum_value,
        set=pose_datum_value_set,
        precision=3,
        options=set()
        )

    easing: FloatProperty(
        name="Value",
        min=-5.0,
        max=5.0,
        get=pose_datum_value,
        set=pose_datum_value_set,
        precision=3,
        options=set()
        )

    index: IntProperty(
        name="Index",
        min=0,
        get=pose_datum_index,
        options=set()
        )

    is_enabled: BoolProperty(
        name="Enabled",
        get=pose_datum_is_enabled,
        options=set()
        )

    name: StringProperty(
        name="Name",
        get=pose_datum_name,
        options=set()
        )

    type: EnumProperty(
        name="Type",
        items=POSE_DATUM_TYPE_ITEMS,
        get=pose_datum_type,
        options=set()
        )

    value: FloatProperty(
        name="Value",
        default=0.0,
        update=pose_datum_value_update_handler,
        precision=3,
        options=set()
        )


class RBFDriverPoseDataPathItem(PropertyGroup):

    icon: StringProperty(
        name="Icon",
        default='NONE',
        options=set()
        )


def pose_data_group_name(group: 'RBFDriverPoseDataGroup') -> str:
    return group.get("name", "")


def pose_data_group_type(group: 'RBFDriverPoseDataGroup') -> int:
    return group.get("type", 0)


class RBFDriverPoseDataGroup(PropertyGroup):

    data__internal__: CollectionProperty(
        type=RBFDriverPoseDatum,
        options={'HIDDEN'}    
        )

    name: StringProperty(
        name="Name",
        get=pose_data_group_name,
        options=set()
        )

    path: CollectionProperty(
        name="Path",
        type=RBFDriverPoseDataPathItem,
        options=set()
        )

    type: EnumProperty(
        name="Type",
        items=POSE_DATA_GROUP_TYPE_ITEMS,
        get=pose_datum_type,
        options=set()
        )

    def __iter__(self) -> Iterator[RBFDriverPoseDatum]:
        return iter(self.data__internal__)

    def __len__(self) -> int:
        return len(self.data__internal__)

    def __getitem__(self, key: Union[int, slice]) -> Union[RBFDriverPoseDatum, List[RBFDriverPoseDatum]]:
        return self.data__internal__[key]

    def find(self, name: str) -> int:
        return next((index for index, item in enumerate(self) if item.name == name), -1)

    def get(self, name: str, default: Optional[object]=None) -> Any:
        return self.data__internal__.get(name, default)

    def index(self, datum: RBFDriverPoseDatum) -> int:
        return next(index for index, item in enumerate(self) if item == datum)

    def items(self) -> Iterator[Tuple[str, RBFDriverPoseDatum]]:
        for item in self:
            yield item.name, item

    def keys(self) -> Iterator[str]:
        for item in self:
            yield item.name


class RBFDriverPoseData(PropertyGroup):

    data__internal__: CollectionProperty(
        type=RBFDriverPoseDataGroup,
        options={'HIDDEN'}
        )

    def __iter__(self) -> Iterator[RBFDriverPoseDataGroup]:
        return iter(self.data__internal__)

    def __len__(self) -> int:
        return len(self.data__internal__)

    def __getitem__(self, key: Union[str, int, slice]) -> Union[RBFDriverPoseDataGroup, List[RBFDriverPoseDataGroup]]:
        return self.data__internal__[key]

    def find(self, name: str) -> int:
        return next((index for index, item in enumerate(self) if item.name == name), -1)

    def get(self, name: str, default: Optional[object]=None) -> Any:
        return self.data__internal__.get(name, default)

    def index(self, group: RBFDriverPoseDataGroup) -> int:
        return next(index for index, item in enumerate(self) if item == group)

    def items(self) -> Iterator[Tuple[str, RBFDriverPoseDataGroup]]:
        for item in self:
            yield item.name, item

    def keys(self) -> Iterator[str]:
        for item in self:
            yield item.name

