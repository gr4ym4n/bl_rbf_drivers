
from typing import TYPE_CHECKING, Dict, List, Tuple
from bpy.types import Object, PropertyGroup
from bpy.props import BoolProperty, EnumProperty, PointerProperty, StringProperty
from .mixins import Symmetrical
from ..app.events import dataclass, dispatch_event, Event
if TYPE_CHECKING:
    from bpy.types import Context
    from .driver import RBFDriver


INPUT_ID_TYPE_ITEMS: List[Tuple[str, str, str, str, int]] = [
    ('OBJECT'     , "Object"  , "", 'OBJECT_DATA',                0),
    ('MESH'       , "Mesh"    , "", 'MESH_DATA',                  1),
    ('CURVE'      , "Curve"   , "", 'CURVE_DATA',                 2),
    ('SURFACE'    , "Surface" , "", 'SURFACE_DATA',               3),
    ('META'       , "Metaball", "", 'META_DATA',                  4),
    ('FONT'       , "Font"    , "", 'FONT_DATA',                  5),
    ('HAIR'       , "Hair"    , "", 'HAIR_DATA',                  6),
    ('POINTCLOUD' , "Point"   , "", 'POINTCLOUD_DATA',            7),
    ('VOLUME'     , "Volume"  , "", 'VOLUME_DATA',                8),
    ('GPENCIL'    , "GPencil" , "", 'OUTLINER_DATA_GREASEPENCIL', 9),
    ('ARMATURE'   , "Armature", "", 'ARMATURE_DATA',              10),
    ('LATTICE'    , "Lattice" , "", 'LATTICE_DATA',               11),
    ('EMPTY'      , "Empty"   , "", 'EMPTY_DATA',                 12),
    ('LIGHT'      , "Light"   , "", 'LIGHT_DATA',                 13),
    ('LIGHT_PROBE', "Light"   , "", 'OUTLINER_DATA_LIGHTPROBE',   14),
    ('CAMERA'     , "Camera"  , "", 'CAMERA_DATA',                15),
    ('SPEAKER'    , "Speaker" , "", 'OUTLINER_DATA_SPEAKER',      16),
    ('KEY'        , "Key"     , "", 'SHAPEKEY_DATA',              17),
]

INPUT_ID_TYPE_INDEX: List[str] = [
    item[1] for item in INPUT_ID_TYPE_ITEMS
    ]

INPUT_ID_TYPE_TABLE: Dict[str, int] = {
    item[0]: item[4] for item in INPUT_ID_TYPE_ITEMS
    }

INPUT_ROTATION_AXIS_ITEMS = [
    ('X', "X", "X axis"),
    ('Y', "Y", "Y axis"),
    ('Z', "Z", "Z axis"),
    ]

INPUT_ROTATION_AXIS_INDEX: List[str] = [
    _item[0] for _item in INPUT_ROTATION_AXIS_ITEMS
    ]

INPUT_ROTATION_AXIS_TABLE: Dict[str, int] = {
    _item[0]: _index for _index, _item in enumerate(INPUT_ROTATION_AXIS_ITEMS)
    }

INPUT_ROTATION_MODE_ITEMS = [
    ('EULER'     , "Euler"     , "Euler angles"       ),
    ('QUATERNION', "Quaternion", "Quaternion rotation"),
    ('SWING'     , "Swing"     , "Swing rotation"     ),
    ('TWIST'     , "Twist"     , "Twist rotation"     ),
    ]

INPUT_ROTATION_MODE_INDEX: List[str] = [
    _item[0] for _item in INPUT_ROTATION_MODE_ITEMS
    ]

INPUT_ROTATION_MODE_TABLE: Dict[str, int] = {
    _item[0]: _index for _index, _item in enumerate(INPUT_ROTATION_MODE_ITEMS)
    }

INPUT_ROTATION_ORDER_ITEMS = [
    ('AUTO', "Auto", "Euler using the rotation order of the target."),
    ('XYZ' , "XYZ" , "Euler using the XYZ rotation order."          ),
    ('XZY' , "XZY" , "Euler using the XZY rotation order."          ),
    ('YXZ' , "YXZ" , "Euler using the YXZ rotation order."          ),
    ('YZX' , "YZX" , "Euler using the YZX rotation order."          ),
    ('ZXY' , "ZXY" , "Euler using the ZXY rotation order."          ),
    ('ZYX' , "ZYX" , "Euler using the ZYX rotation order."          ),
    ]

INPUT_ROTATION_ORDER_INDEX: List[str] = [
    _item[0] for _item in INPUT_ROTATION_ORDER_ITEMS
    ]

INPUT_ROTATION_ORDER_TABLE: Dict[str, int] = {
    _item[0]: _index for _index, _item in enumerate(INPUT_ROTATION_ORDER_ITEMS)
    }

INPUT_TRANSFORM_SPACE_ITEMS: list[str, str, str] = [
    ('WORLD_SPACE'    , "World Space"    , "Transforms include effects of parenting/restpose and constraints"    ),
    ('TRANSFORM_SPACE', "Transform Space", "Transforms don't include parenting/restpose or constraints"          ),
    ('LOCAL_SPACE'    , "Local Space"    , "Transforms include effects of constraints but not parenting/restpose"),
    ]

INPUT_TRANSFORM_SPACE_INDEX: List[str] = [
    _item[0] for _item in INPUT_TRANSFORM_SPACE_ITEMS
    ]

INPUT_TRANSFORM_SPACE_TABLE: Dict[str, int] = {
    _item[0]: _index for _index, _item in enumerate(INPUT_TRANSFORM_SPACE_ITEMS)
    }

INPUT_TYPE_ITEMS = [
    ('LOCATION', "Location", "Location transform channels", 'CON_LOCLIMIT' , 0),
    ('ROTATION', "Rotation", "Rotation transform channels", 'CON_ROTLIMIT' , 1),
    ('SCALE'   , "Scale"   , "Scale transform channels"   , 'CON_SIZELIMIT', 2),
    None,
    ('ROTATION_DIFF', "Rotational Difference", "Angle between two bones or objects."   , 'DRIVER_ROTATIONAL_DIFFERENCE', 3),
    ('LOC_DIFF'     , "Distance"             , "Distance between two bones or objects.", 'DRIVER_DISTANCE'             , 4),
    None,
    ('SHAPE_KEY', "Shape Keys"  , "Shape key values"               , 'SHAPEKEY_DATA', 5),
    ('USER_DEF' , "User-defined", "Fully configurable input values", 'RNA'          , 6),
    ]

INPUT_TYPE_INDEX: List[str] = [
    _item[0] for _item in INPUT_TYPE_ITEMS if _item is not None
    ]

INPUT_TYPE_TABLE: Dict[str, int] = {
    _item[0]: _item[4] for _item in INPUT_TYPE_ITEMS if _item is not None
    }

INPUT_TYPE_ICONS: Dict[str, str] = {
    _item[0]: _item[3] for _item in INPUT_TYPE_ITEMS if _item is not None
    }


@dataclass(frozen=True)
class InputPropertyUpdateEvent(Event):
    input: 'Input'


@dataclass(frozen=True)
class InputBoneTargetUpdateEvent(InputPropertyUpdateEvent):
    value: str


@dataclass(frozen=True)
class InputNameUpdateEvent(InputPropertyUpdateEvent):
    value: str


@dataclass(frozen=True)
class InputObjectUpdateEvent(InputPropertyUpdateEvent):
    value: Object


@dataclass(frozen=True)
class InputRotationAxisUpdateEvent(InputPropertyUpdateEvent):
    value: str
    previous_value: str


@dataclass(frozen=True)
class InputRotationModeUpdateEvent(InputPropertyUpdateEvent):
    value: str
    previous_value: str


@dataclass(frozen=True)
class InputTransformSpaceUpdateEvent(InputPropertyUpdateEvent):
    value: str


@dataclass(frozen=True)
class InputUseMirrorXUpdateEvent(InputPropertyUpdateEvent):
    value: bool


@dataclass(frozen=True)
class InputUseSwingUpdateEvent(InputPropertyUpdateEvent):
    value: bool


@dataclass(frozen=True)
class InputUseXUpdateEvent(InputPropertyUpdateEvent):
    value: bool


@dataclass(frozen=True)
class InputUseYUpdateEvent(InputPropertyUpdateEvent):
    value: bool


@dataclass(frozen=True)
class InputUseZUpdateEvent(InputPropertyUpdateEvent):
    value: bool


def input_bone_target_update_handler(input_: 'Input', _: 'Context') -> None:
    dispatch_event(InputBoneTargetUpdateEvent(input_, input_.bone_target))


def input_name_update_handler(input_: 'Input', _: 'Context') -> None:
    dispatch_event(InputNameUpdateEvent(input_, input_.name))


def input_name_is_user_defined(input: 'Input') -> bool:
    return input.get("name_is_user_defined", False)


def input_object_validate(input: 'Input', object: Object) -> None:
    return input.type != 'SHAPE_KEY' or object.type in {'MESH', 'LATTICE', 'CURVE'}


def input_object_update_handler(input_: 'Input', _: 'Context') -> None:
    dispatch_event(InputObjectUpdateEvent(input_, input_.object))


def input_rotation_axis(input_: 'Input') -> int:
    return input_.get("rotation_axis", INPUT_ROTATION_AXIS_TABLE['Y'])


def input_rotation_axis_set(input_: 'Input', value: int) -> None:
    oldaxis = input_.rotation_axis
    newaxis = INPUT_ROTATION_AXIS_INDEX[value]
    input_["rotation_axis"] = value
    dispatch_event((InputRotationAxisUpdateEvent(input_, newaxis, oldaxis)))


def input_rotation_mode(input: 'Input') -> int:
    return input.get("rotation_mode", 0)


def input_rotation_mode_set(input_: 'Input', value: int) -> None:
    oldmode = input_.rotation_mode
    newmode = INPUT_ROTATION_MODE_INDEX[value]
    input_["rotation_mode"] = value
    dispatch_event(InputRotationModeUpdateEvent(input_, newmode, oldmode))


def input_transform_space_update_handler(input_: 'Input', value: int) -> None:
    dispatch_event(InputTransformSpaceUpdateEvent(input_, input_.transform_space))


def input_type(input) -> int:
    return input.get("type", 0)


def input_use_mirror_x_update_handler(input: 'Input', _: 'Context') -> None:
    dispatch_event(InputUseMirrorXUpdateEvent(input, input.use_mirror_x))


def input_use_x_update_handler(input_: 'Input', _: 'Context') -> None:
    dispatch_event(InputUseXUpdateEvent(input_, input_.use_x))


def input_use_y_update_handler(input_: 'Input', _: 'Context') -> None:
    dispatch_event(InputUseYUpdateEvent(input_, input_.use_y))


def input_use_z_update_handler(input_: 'Input', _: 'Context') -> None:
    dispatch_event(InputUseZUpdateEvent(input_, input_.use_z))


class Input(Symmetrical, PropertyGroup):

    bone_target: StringProperty(
        name="Bone",
        description="Name of pose bone to read input values from",
        default="",
        options=set(),
        update=input_bone_target_update_handler,
        )

    data_path: StringProperty(
        name="Path",
        default="",
        options=set(),
        update=input_data_path_update_handler
        )

    @property
    def driver(self) -> 'RBFDriver':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".inputs")[0])

    name: StringProperty(
        name="Name",
        description="Input name",
        update=input_name_update_handler,
        options=set()
        )

    name_is_user_defined: BoolProperty(
        name="User Defined Name",
        description="Name is user-defined (internal use)",
        get=input_name_is_user_defined,
        options=set()
        )

    id_type: EnumProperty(
        items=INPUT_ID_TYPE_ITEMS,
        default='OBJECT',
        update=input_id_type_update_handler,
        options=set()
        )

    object: PointerProperty(
        name="Object",
        description="The target object",
        type=Object,
        poll=input_object_validate,
        options=set(),
        update=input_object_update_handler
        )

    rotation_axis: EnumProperty(
        name="Axis",
        description="The axis of rotation",
        items=INPUT_ROTATION_AXIS_ITEMS,
        get=input_rotation_axis,
        set=input_rotation_axis_set,
        options=set(),
        )

    rotation_mode: EnumProperty(
        name="Mode",
        description="Rotation mode",
        items=INPUT_ROTATION_MODE_ITEMS,
        get=input_rotation_mode,
        set=input_rotation_mode_set,
        options=set(),
        )

    rotation_order: EnumProperty(
        name="Order",
        description="Rotation order",
        items=INPUT_ROTATION_ORDER_ITEMS,
        default=INPUT_ROTATION_ORDER_ITEMS[0][0],
        options=set()
        )

    transform_space: EnumProperty(
        name="Space",
        description="The space for transform channels",
        items=INPUT_TRANSFORM_SPACE_ITEMS,
        update=input_transform_space_update_handler,
        options=set(),
        )

    type: EnumProperty(
        name="Type",
        items=INPUT_TYPE_ITEMS,
        get=input_type,
        options=set(),
        )

    ui_show_pose: BoolProperty(
        name="Show",
        description="Show/Hide pose values in the UI",
        default=False,
        options=set()
        )

    use_mirror_x: BoolProperty(
        name="X-Mirror",
        description="Mirror transform values along X-axis",
        default=True,
        options=set(),
        update=input_use_mirror_x_update_handler
        )

    use_x: BoolProperty(
        name="X",
        default=False,
        options=set(),
        update=input_use_x_update_handler
        )

    use_y: BoolProperty(
        name="Y",
        default=False,
        options=set(),
        update=input_use_y_update_handler
        )

    use_z: BoolProperty(
        name="Z",
        default=False,
        options=set(),
        update=input_use_z_update_handler
        )

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'
