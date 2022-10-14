
# key = (pose index, i/o, i/oindex, )

# container is input or output
#
#            group     |   group   |        group
# pose : value , value |   value   | value, value, value
# pose : value , value |   value   | value, value, value


# Nodes
# Input -> [Pose, ...] -> InputPoseWeightController


from typing import TYPE_CHECKING, Optional, Tuple, Union
from bpy.types import PropertyGroup
from bpy.props import EnumProperty, FloatProperty, IntProperty, IntVectorProperty, StringProperty
from .mixins import Identifiable
from ..app.events import dataclass, dispatch_event, Event
if TYPE_CHECKING:
    from bpy.types import ID


@dataclass(frozen=True)
class PoseDataValueUpdateEvent(Event):
    value: 'PoseDataValue'


def pose_data_value_get(data: 'PoseDataValue') -> float:
    return data.get("value", 0.0)


def pose_data_value_set(data: 'PoseDataValue', value: float) -> None:
    data["value"] = value
    dispatch_event(PoseDataValueUpdateEvent(data))


class PoseDataValue(PropertyGroup):

    angle: FloatProperty(
        name="Value",
        get=pose_data_value_get,
        set=pose_data_value_set,
        options=set()
        )

    @property
    def id_type(self) -> str:
        return self.id_data.type

    @property
    def id(self) -> 'ID':
        return self.id_data.data

    index: IntProperty(
        name="Index",
        get=lambda self: self.get("index", 0),
        options={'HIDDEN'}
        )

    @property
    def data(self) -> 'PoseDataTable':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])

    data_path: StringProperty(
        name="Path",
        get=lambda self: self.get("data_path", "")
        )

    @property
    def data_path(self) -> str:
        return self.data.path

    @property
    def value_path(self) -> str:
        return f'{self.data_path}[{self.index}]'

    value: FloatProperty(
        name="Value",
        get=pose_data_value_get,
        set=pose_data_value_set,
        options=set()
        )

    def __init__(self, path: str, index: int, group: str, value: Optional[float]=0.0) -> None:
        self["data_path"] = path
        self["index"] = index
        self["group"] = group
        self["value"] = value


POSE_DATA_GROUP_TYPE_ITEMS = [
    ('FLOAT', "Float", ""),
    ('EULER', "Euler", ""),
    ('QUATERNION', "Quaternion", ""),
    ('AXIS_ANGLE', "Axis/Angle", ""),
    ('TRANSLATION', "Translation", ""),
    ('SCALE', "Scale", ""),
    ]

POSE_DATA_GROUP_SIZES = {
    'FLOAT': 1,
    'EULER': 3,
    'QUATERNION': 4,
    'AXIS_ANGLE': 4,
    'TRANSLATION': 3,
    'SCALE': 3
    }


class PoseDataGroup(PropertyGroup):

    range: IntVectorProperty(
        size=2,
        options={'HIDDEN'}
        )

    type: EnumProperty(
        name="Type",
        items=POSE_DATA_GROUP_TYPE_ITEMS,
        options=set()
        )


class PoseDataBlock:
    
    def group(self, name: str) -> 'PoseDataBlock':
        pass


class PoseDataTable(PropertyGroup):

    name: StringProperty(

        )

    @property
    def path(self) -> str:
        return f'["{self.name}"]'

    def __getitem__(self, key: Union[Identifiable,
                                     str,
                                     int,
                                     slice,
                                     Tuple[Union[Identifiable, str, int, slice],
                                           Union[Identifiable, str, int, slice]]]
                    ) -> Union[PoseDataValue, PoseDataBlock]:
        pass

    def group(self, name: str) -> Optional[PoseDataGroup]:
        pass

    def pose(self, name: str) -> Optional[PoseDataBlock]:
        pass

table = PoseDataTable()
# pose
table[pose]
# input / output
table[:, input_]
# pose for input / output
table[pose, input_]
