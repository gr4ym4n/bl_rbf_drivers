
from typing import Iterator, List, Optional, Sequence, Tuple, Union, TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, EnumProperty, FloatProperty, StringProperty
from ..app.events import dataclass, dispatch_event, Event
from .input import Input
from .outputs import Output
if TYPE_CHECKING:
    from .poses import Pose


POSE_DATA_COMPONENT_TYPE_ITEMS = [
    ('FLOAT', "Float", ""),
    ('ANGLE', "Angle", ""),
    ]

POSE_DATA_COMPONENT_TYPE_TABLE = {
    _item[0]: _index for _index, _item in enumerate(POSE_DATA_COMPONENT_TYPE_ITEMS)
    }


@dataclass
class PoseDataComponentValueUpdateEvent(Event):
    component: 'PoseDataComponent'
    value: float


def pose_data_component_value_get(component: 'PoseDataComponent') -> float:
    return component.get("value", component.default_value)


def pose_data_component_value_set(component: 'PoseDataComponent', value: float) -> None:
    component["value"] = value
    dispatch_event(PoseDataComponentValueUpdateEvent(component, value))


class PoseDataComponent(PropertyGroup):

    @property
    def data(self) -> 'PoseDataContainer':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])

    default_value: FloatProperty(
        name="Default",
        get=lambda self: self.get("default_value", 0.0),
        options=set()
        )

    @property
    def pose(self) -> 'Pose':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".data")[0])

    type: EnumProperty(
        items=POSE_DATA_COMPONENT_TYPE_ITEMS,
        options=set()
        )

    angle: FloatProperty(
        name="Value",
        get=pose_data_component_value_get,
        set=pose_data_component_value_set,
        options=set()
        )

    value: FloatProperty(
        name="Value",
        get=pose_data_component_value_get,
        set=pose_data_component_value_set,
        options=set()
        )

    def __init__(self,
                 value: float,
                 type: Optional[str]='FLOAT',
                 name: Optional[str]="",
                 default_value: Optional[float]=0.0) -> None:
        self["type"] = POSE_DATA_COMPONENT_TYPE_TABLE[type]
        self["value"] = value
        self["name"] = name
        self["default_value"] = default_value


POSE_DATA_CONTAINER_TYPE_ITEMS = [
    ('FLOAT', "Float", ""),
    ('ANGLE', "Angle", ""),
    ('TRANSLATION', "Translation", ""),
    ('EULER', "Euler", ""),
    ('AXIS_ANGLE', "Axis/Angle", ""),
    ('QUATERNION', "Quaternion", ""),
    ('SCALE', "Scale", ""),
    ]

POSE_DATA_CONTAINER_TYPE_SIZES = {
    'FLOAT': 1,
    'ANGLE': 1,
    'TRANSLATION': 3,
    'EULER': 3,
    'AXIS_ANGLE': 4,
    'QUATERNION': 4,
    'SCALE': 3
    }

POSE_DATA_CONTAINER_TYPE_SPECS = {
    'ANGLE': [
        {"type": 'ANGLE', "name": "", "default_value": 0.0},
        ],
    'FLOAT': [
        {"type": 'FLOAT', "name": "", "default_value": 0.0},
        ],
    'TRANSLATION': [
        {"type": 'FLOAT', "name": "x", "default_value": 0.0},
        {"type": 'FLOAT', "name": "y", "default_value": 0.0},
        {"type": 'FLOAT', "name": "z", "default_value": 0.0},
        ],
    'QUATERNION': [
        {"type": 'FLOAT', "name": "w", "default_value": 1.0},
        {"type": 'FLOAT', "name": "x", "default_value": 0.0},
        {"type": 'FLOAT', "name": "y", "default_value": 0.0},
        {"type": 'FLOAT', "name": "z", "default_value": 0.0},
        ],
    'AXIS_ANGLE': [
        {"type": 'ANGLE', "name": "w", "default_value": 0.0},
        {"type": 'FLOAT', "name": "x", "default_value": 0.0},
        {"type": 'FLOAT', "name": "y", "default_value": 1.0},
        {"type": 'FLOAT', "name": "z", "default_value": 0.0},
        ],
    'EULER': [
        {"type": 'ANGLE', "name": "x", "default_value": 0.0},
        {"type": 'ANGLE', "name": "y", "default_value": 0.0},
        {"type": 'ANGLE', "name": "z", "default_value": 0.0},
        ],
    'SCALE': [
        {"type": 'FLOAT', "name": "x", "default_value": 1.0},
        {"type": 'FLOAT', "name": "y", "default_value": 1.0},
        {"type": 'FLOAT', "name": "z", "default_value": 1.0},
        ]
    }


def pose_data_container_name_get(container: 'PoseDataContainer') -> str:
    return container.get("name", "")


def pose_data_container_name_set(container: 'PoseDataContainer', _) -> None:
    raise AttributeError(f'{container.__class__.__name__}.name is read-only')


class PoseDataContainer(PropertyGroup):

    internal__: CollectionProperty(
        type=PoseDataComponent,
        options={'HIDDEN'}
        )

    name: StringProperty(
        name="Name",
        get=pose_data_container_name_get,
        set=pose_data_container_name_set,
        options=set()
        )

    type: EnumProperty(
        items=POSE_DATA_CONTAINER_TYPE_ITEMS,
        options=set()
        )

    def __init__(self, type: str, data: Optional[Union[float,
                                                 Sequence[float],
                                                 Tuple[Sequence[float], float]]]=None) -> None:
        values = self.internal__
        values.clear()
        spec = POSE_DATA_CONTAINER_TYPE_SPECS[type]
        if data is None:
            data = [item["default_value"] for item in spec]
        elif type == 'AXIS_ANGLE' and isinstance(data, tuple):
            data = (data[1],) + tuple(data[0])
        elif isinstance(data, float):
            data = [data]
        for value, settings in zip(data, spec):
            values.add().__init__(value, **settings)


class PoseData(PropertyGroup):

    internal__: CollectionProperty(
        type=PoseDataContainer,
        options={'HIDDEN'}
        )

    def __iter__(self) -> Iterator[PoseDataContainer]:
        return iter(self.internal__)

    def __getitem__(self, key: Union[int, str, slice]) -> Union[PoseDataContainer,
                                                                List[PoseDataContainer]]:
        return self.internal__[key]

    def __len__(self) -> int:
        return len(self.internal__)

    def get(self, key: Union[str, Input, Output]) -> Optional[PoseDataContainer]:
        if isinstance(key, str):
            return self.internal__.get(key)
        if isinstance(key, (Input, Output)):
            return self.internal__.get(key.identifier)
        raise TypeError()
