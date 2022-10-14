
from ctypes import Union
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple, Type
from logging import getLogger
from bpy.types import ID, Object, PropertyGroup
from bpy.props import CollectionProperty, EnumProperty, StringProperty, PointerProperty
from .mixins import Collection, Searchable, Symmetrical
from ..app.events import dataclass, dispatch_event, Event
from ..app.utils import owner_resolve
if TYPE_CHECKING:
    from logging import Logger
    from bpy.types import Context
    from .input_variables import InputVariable
    from .input import Input

log = getLogger(__name__)

#region Enums
#--------------------------------------------------------------------------------------------------

INPUT_TARGET_ROTATION_MODE_ITEMS: List[Tuple[str, str, str]] = [
    ('AUTO'         , "Auto Euler"       , "Euler using the rotation order of the target"                                  ),
    ('XYZ'          , "XYZ Euler"        , "Euler using the XYZ rotation order"                                            ),
    ('XZY'          , "XZY Euler"        , "Euler using the XZY rotation order"                                            ),
    ('YXZ'          , "YXZ Euler"        , "Euler using the YXZ rotation order"                                            ),
    ('YZX'          , "YZX Euler"        , "Euler using the YZX rotation order"                                            ),
    ('ZXY'          , "ZXY Euler"        , "Euler using the ZXY rotation order"                                            ),
    ('ZYX'          , "ZYX Euler"        , "Euler using the ZYX rotation order"                                            ),
    ('QUATERNION'   , "Quaternion"       , "Quaternion rotation"                                                           ),
    ('SWING_TWIST_X', "Swing and X Twist", "Decompose into a swing rotation to aim the X axis, followed by twist around it"),
    ('SWING_TWIST_Y', "Swing and Y Twist", "Decompose into a swing rotation to aim the Y axis, followed by twist around it"),
    ('SWING_TWIST_Z', "Swing and Z Twist", "Decompose into a swing rotation to aim the Z axis, followed by twist around it"),
    ]

INPUT_TARGET_ROTATION_MODE_INDEX: List[str] = [
    _item[0] for _item in INPUT_TARGET_ROTATION_MODE_ITEMS
    ]

INPUT_TARGET_ROTATION_MODE_TABLE: Dict[str, int] = {
    _item[0]: _index for _index, _item in enumerate(INPUT_TARGET_ROTATION_MODE_ITEMS)
    }

INPUT_TARGET_ID_TYPE_ITEMS: List[Tuple[str, str, str, str, int]] = [
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

INPUT_TARGET_ID_TYPE_INDEX: List[str] = [
    item[1] for item in INPUT_TARGET_ID_TYPE_ITEMS
    ]

INPUT_TARGET_ID_TYPE_TABLE: Dict[str, int] = {
    item[0]: item[4] for item in INPUT_TARGET_ID_TYPE_ITEMS
    }

INPUT_TARGET_TRANSFORM_SPACE_ITEMS: list[str, str, str] = [
    ('WORLD_SPACE'    , "World Space"    , "Transforms include effects of parenting/restpose and constraints"    ),
    ('TRANSFORM_SPACE', "Transform Space", "Transforms don't include parenting/restpose or constraints"          ),
    ('LOCAL_SPACE'    , "Local Space"    , "Transforms include effects of constraints but not parenting/restpose"),
    ]

INPUT_TARGET_TRANSFORM_SPACE_INDEX: List[str] = [
    _item[0] for _item in INPUT_TARGET_TRANSFORM_SPACE_ITEMS
    ]

INPUT_TARGET_TRANSFORM_SPACE_TABLE: Dict[str, int] = {
    _item[0]: _index for _index, _item in enumerate(INPUT_TARGET_TRANSFORM_SPACE_ITEMS)
    }

INPUT_TARGET_TRANSFORM_TYPE_ITEMS: List[Tuple[str, str, str]] = [
    ('LOC_X'  , "X Location", ""),
    ('LOC_Y'  , "Y Location", ""),
    ('LOC_Z'  , "Z Location", ""),
    ('ROT_W'  , "W Rotation", ""),
    ('ROT_X'  , "X Rotation", ""),
    ('ROT_Y'  , "Y Rotation", ""),
    ('ROT_Z'  , "Z Rotation", ""),
    ('SCALE_X', "X Scale"   , ""),
    ('SCALE_Y', "Y Scale"   , ""),
    ('SCALE_Z', "Z Scale"   , ""),
    ]

INPUT_TARGET_TRANSFORM_TYPE_INDEX: List[str] = [
    _item[0] for _item in INPUT_TARGET_TRANSFORM_TYPE_ITEMS
    ]

INPUT_TARGET_TRANSFORM_TYPE_TABLE: Dict[str, int] = {
    _item[0]: _index for _index, _item in enumerate(INPUT_TARGET_TRANSFORM_TYPE_ITEMS)
    }

#endregion Enums

#region Events
#--------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class InputTargetPropertyUpdateEvent(Event):
    target: 'InputTarget'
    value: Any


@dataclass(frozen=True)
class InputTargetBoneTargetUpdateEvent(InputTargetPropertyUpdateEvent):
    value: str


@dataclass(frozen=True)
class InputTargetDataPathUpdateEvent(InputTargetPropertyUpdateEvent):
    value: str


@dataclass(frozen=True)
class InputTargetIDTypeUpdateEvent(InputTargetPropertyUpdateEvent):
    value: str


@dataclass(frozen=True)
class InputTargetObjectUpdateEvent(InputTargetPropertyUpdateEvent):
    value: Optional[Object]


@dataclass(frozen=True)
class InputTargetRotationModeUpdateEvent(InputTargetPropertyUpdateEvent):
    value: str


@dataclass(frozen=True)
class InputTargetTransformSpaceUpdateEvent(InputTargetPropertyUpdateEvent):
    value: str


@dataclass(frozen=True)
class InputTargetTransformTypeUpdateEvent(InputTargetPropertyUpdateEvent):
    value: str

#endregion Events

#region Handlers

def _input_target_bone_target_get(target: 'InputTarget') -> str:
    return target.get("bone_target", "")


def _input_target_bone_target_set(target: 'InputTarget', value: str) -> None:
    input = target.input
    if input.type in {'LOCATION', 'ROTATION', 'SCALE'}:
        raise AttributeError((f'{target}.bone_target is not writable because '
                              f'it\'s input has type \'{input.type}\'. Use '
                              f'{input.__class__.__name__}.bone_target instead'))
    target["bone_target"] = value
    dispatch_event(InputTargetBoneTargetUpdateEvent(target, value))


def _input_target_data_path_get(target: 'InputTarget') -> str:
    return target.get("data_path", "")


def _input_target_data_path_set(target: 'InputTarget', value: str) -> None:
    input = target.input
    if input.type != 'USER_DEF':
        raise AttributeError((f'{target}.data_path is not writable because '
                              f'it\'s input has type \'{input.type}\'.'))
    target["data_path"] = value
    dispatch_event(InputTargetDataPathUpdateEvent(target, value))


def _input_target_id_type_get(target: 'InputTarget') -> int:
    return target.get("id_type", 0)


def _input_target_id_type_set(target: 'InputTarget', value: int) -> None:
    input = target.input
    if input.type != 'USER_DEF':
        raise AttributeError((f'{target.__class__.__name__}.id_type is not writable '
                              f'for {input} with type \'{input.type}\''))
    target["id_type"] = value
    dispatch_event(InputTargetIDTypeUpdateEvent(target, target.id_type))


def _input_target_object_update_handler(target: 'InputTarget', _: 'Context') -> None:
    dispatch_event(InputTargetObjectUpdateEvent(target, target.object))


def _input_target_rotation_mode_update_handler(target: 'InputTarget', _: 'Context') -> None:
    dispatch_event(InputTargetObjectUpdateEvent(target, target.object))


def _input_target_transform_space_get(target: 'InputTarget') -> int:
    return target.get('transform_space', INPUT_TARGET_TRANSFORM_SPACE_INDEX[0])


def _input_target_transform_space_set(target: 'InputTarget', value: int) -> None:
    input: 'Input' = owner_resolve(target, ".variables")

    if input.type in {'LOCATION', 'ROTATION', 'SCALE'}:
        raise RuntimeError((f'{target}.transform_space is not writable for {input} '
                            f'with type {input.type}. Use Input.transform_space.'))

    target["transform_space"] = value
    dispatch_event(InputTargetTransformSpaceUpdateEvent(target, target.transform_space))


def _input_target_transform_type_get(target: 'InputTarget') -> int:
    return target.get("transform_type", 0)


def _input_target_transform_type_set(target: 'InputTarget', value: int) -> None:
    input: 'Input' = owner_resolve(target, ".variables")
    if input.type in {'LOCATION', 'ROTATION', 'SCALE'}:
        raise RuntimeError((f'{target}.transform_type is not writable '
                            f'for {input} because {input} type is {input.type}'))
    target["transform_type"] = value
    dispatch_event(InputTargetTransformTypeUpdateEvent(target, target.transform_type))

#endregion Handlers

#region Input
#--------------------------------------------------------------------------------------------------

class InputTarget(Symmetrical, PropertyGroup):

    bone_target: StringProperty(
        name="Bone",
        description="The pose bone to target",
        get=_input_target_bone_target_get,
        set=_input_target_bone_target_set,
        options=set(),
        )

    data_path: StringProperty(
        name="Path",
        description="The path to the target property",
        get=_input_target_data_path_get,
        set=_input_target_data_path_set,
        options=set(),
        )

    id_type: EnumProperty(
        name="Type",
        description="The type of ID to target",
        items=INPUT_TARGET_ID_TYPE_ITEMS,
        get=_input_target_id_type_get,
        set=_input_target_id_type_set,
        options=set(),
        )

    @property
    def id(self) -> Optional[ID]:
        """The target's ID data-block (read-only)"""
        object = self.object
        if object is None or self.id_type == 'OBJECT': return object
        if object.type == self.id_type: return object.data

    @property
    def input(self) -> 'Input':
        '''The input to which this input-target belongs (read-only)'''
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".variables")[0])

    object: PointerProperty(
        name="Object",
        description="The target object",
        type=Object,
        poll=lambda self, object: self.id_type in (object.type, 'OBJECT'),
        options=set(),
        update=_input_target_object_update_handler
        )

    rotation_mode: EnumProperty(
        name="Rotation",
        description="The rotation mode for the input target data",
        items=INPUT_TARGET_ROTATION_MODE_ITEMS,
        default=INPUT_TARGET_ROTATION_MODE_ITEMS[0][0],
        options=set(),
        update=_input_target_rotation_mode_update_handler
        )

    transform_space: EnumProperty(
        name="Space",
        description="The transform space for transform channels",
        items=INPUT_TARGET_TRANSFORM_SPACE_ITEMS,
        get=_input_target_transform_space_get,
        set=_input_target_transform_space_set,
        options=set(),
        )

    transform_type: EnumProperty(
        name="Type",
        description="The transform channel to target",
        items=INPUT_TARGET_TRANSFORM_TYPE_ITEMS,
        get=_input_target_transform_type_get,
        set=_input_target_transform_type_set,
        options=set(),
        )

    @property
    def variable(self) -> 'InputVariable':
        '''The input-variable to which this input-target belongs (read-only)'''
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".targets")[0])

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'

#endregion Input

#region Inputs
#--------------------------------------------------------------------------------------------------

class InputTargets(Searchable[InputTarget], Collection[InputTarget], PropertyGroup):

    internal__: CollectionProperty(
        type=InputTarget,
        options={'HIDDEN'}
        )

    @property
    def input(self) -> 'Input':
        '''The input to which the input-targets belong (read-only)'''
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".variables")[0])

    def __getitem__(self, key: Union[int, slice]) -> Union[InputTarget, List[InputTarget]]:
        return self.internal__[key]

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'

#endregion Inputs