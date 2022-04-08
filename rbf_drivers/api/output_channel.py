
from typing import Optional, TYPE_CHECKING
from bpy.types import ID, Object, PropertyGroup
from bpy.props import (BoolProperty,
                       EnumProperty,
                       FloatProperty,
                       IntProperty,
                       PointerProperty,
                       StringProperty)
from .mixins import Symmetrical, Targetable
from .output_channel_data import RBFDriverOutputChannelData
from ..app.events import dataclass, dispatch_event, Event
from ..app.utils import owner_resolve
if TYPE_CHECKING:
    from bpy.types import Context
    from .output import RBFDriverOutput

OUTPUT_CHANNEL_ID_TYPE_ITEMS = [
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

OUTPUT_CHANNEL_ID_TYPE_INDEX = {
    item[0]: item[4] for item in OUTPUT_CHANNEL_ID_TYPE_ITEMS
    }


@dataclass(frozen=True)
class OutputChannelBoneTargetChangeEvent(Event):
    channel: 'RBFDriverOutputChannel'
    value: str
    previous_value: str


@dataclass(frozen=True)
class OutputChannelDataPathUpdateEvent(Event):
    channel: 'RBFDriverOutputChannel'
    value: str


@dataclass(frozen=True)
class OutputChannelIDTypeUpdateEvent(Event):
    channel: 'RBFDriverOutputChannel'
    value: str


@dataclass(frozen=True)
class OutputChannelIsEnabledUpdateEvent(Event):
    channel: 'RBFDriverOutputChannel'
    value: bool


@dataclass(frozen=True)
class OutputChannelIsInvertedUpdateEvent(Event):
    channel: 'RBFDriverOutputChannel'
    value: bool


@dataclass(frozen=True)
class OutputChannelMuteUpdateEvent(Event):
    channel: 'RBFDriverOutputChannel'
    value: bool


@dataclass(frozen=True)
class OutputChannelObjectChangeEvent(Event):
    channel: 'RBFDriverOutputChannel'
    value: Optional[Object]
    previous_value: Optional[Object]


def output_channel_array_index(channel: 'RBFDriverOutputChannel') -> int:
    return channel.get("array_index", 0)


def output_channel_bone_target(channel: 'RBFDriverOutputChannel') -> str:
    return channel.get("bone_target", "")


def output_channel_bone_target_set(channel: 'RBFDriverOutputChannel', value: str) -> None:
    previous_value = output_channel_bone_target(channel)
    channel["bone_target"] = value
    dispatch_event(OutputChannelBoneTargetChangeEvent(channel, value, previous_value))


def output_channel_data_path(channel: 'RBFDriverOutputChannel') -> str:
    return channel.get("data_path", "")


def output_channel_data_path_set(channel: 'RBFDriverOutputChannel', value: str) -> None:
    output: 'RBFDriverOutput' = owner_resolve(channel, ".channels")

    if output.type != 'NONE':
        raise RuntimeError((f'{channel.__class__.__name__}.data_path '
                            f'is not user-editable for {output}'))

    channel["data_path"] = value
    dispatch_event(OutputChannelDataPathUpdateEvent(channel, value))


def output_channel_id_type(channel: 'RBFDriverOutputChannel') -> int:
    return channel.get("id_type", 0)


def output_channel_id_type_set(channel: 'RBFDriverOutputChannel', value: int) -> None:
    output: 'RBFDriverOutput' = owner_resolve(channel, ".channels")

    if output.type != 'NONE':
        raise RuntimeError(f'{channel} id type is not editable for output {output}')

    channel["id_type"] = value
    dispatch_event(OutputChannelIDTypeUpdateEvent(channel, channel.id_type))

    idtype = channel.id_type
    object = channel.object__internal__

    if object is not None and idtype not in {object.type, 'OBJECT'}:
        channel.object = None


def output_channel_is_enabled_update_handler(channel: 'RBFDriverOutputChannel', _: 'Context') -> None:
    dispatch_event(OutputChannelIsEnabledUpdateEvent(channel, channel.is_enabled))


def output_channel_is_inverted_update_handler(channel: 'RBFDriverOutputChannel', _: 'Context') -> None:
    dispatch_event(OutputChannelIsInvertedUpdateEvent(channel, channel.is_inverted))


def output_channel_mute_update_handler(channel: 'RBFDriverOutputChannel', _: 'Context') -> None:
    dispatch_event(OutputChannelMuteUpdateEvent(channel, channel.mute))


def output_channel_object_update_handler(channel: 'RBFDriverOutputChannel', _: 'Context') -> None:
    cache = channel.object__internal__
    value = channel.object
    channel.object__internal__ = value
    dispatch_event(OutputChannelObjectChangeEvent(channel, value, cache))


class RBFDriverOutputChannel(Targetable, Symmetrical, PropertyGroup):

    array_index: IntProperty(
        name='Index',
        description="Output channel array index (read-only)",
        get=output_channel_array_index,
        options=set(),
        )

    bone_target: StringProperty(
        name="Bone",
        description="The pose bone to target",
        get=output_channel_bone_target,
        set=output_channel_bone_target_set,
        options=set(),
        )

    data_path: StringProperty(
        name="Path",
        description="",
        get=output_channel_data_path,
        set=output_channel_data_path_set,
        options=set()
        )

    data: PointerProperty(
        name="Data",
        type=RBFDriverOutputChannelData,
        options=set()
        )

    default_value: FloatProperty(
        name="Default",
        default=0.0,
        options=set()
        )

    id_type: EnumProperty(
        name="Type",
        items=OUTPUT_CHANNEL_ID_TYPE_ITEMS,
        get=output_channel_id_type,
        set=output_channel_id_type_set,
        options=set(),
        )

    @property
    def id(self) -> Optional[ID]:
        object = self.object__internal__
        if object is None or self.id_type == 'OBJECT': return object
        if object.type == self.id_type: return object.data

    is_enabled: BoolProperty(
        name="Enabled",
        description="Include or exclude the channel",
        update=output_channel_is_enabled_update_handler,
        options=set(),
        )

    is_inverted: BoolProperty(
        name="Invert",
        description="Invert the output channel's value when mirroring",
        default=False,
        options=set(),
        update=output_channel_is_inverted_update_handler
        )

    @property
    def is_valid(self) -> bool:
        id = self.id
        if id is None:
            return False
        try:
            value = id.path_resolve(self.data_path)
        except ValueError:
            return False
        else:
            if isinstance(value, (float, int, bool)):
                return True
            if not self.is_property_set("array_index"):
                return False
            try:
                if not isinstance(value, str) and len(value):
                    value = value[self.array_index]
            except (TypeError, IndexError, KeyError):
                return False
            else:
                return isinstance(value, (float, int, bool))

    mute: BoolProperty(
        name="Mute",
        description=("Mute the output channel driver "
                     "(muting the driven allows editing of the driven property)"),
        default=False,
        options=set(),
        update=output_channel_mute_update_handler
        )

    object__internal__: PointerProperty(
        type=Object,
        options={'HIDDEN'}
        )

    object: PointerProperty(
        name="Object",
        type=Object,
        poll=lambda self, object: self.id_type in (object.type, 'OBJECT'),
        options=set(),
        update=output_channel_object_update_handler
        )

    @property
    def value(self) -> float:
        id = self.id
        if id is not None:
            try:
                value = id.path_resolve(self.data_path)
            except ValueError:
                pass
            else:
                if isinstance(value, (float, int, bool)):
                    return float(value)
                if self.is_property_set("array_index"):
                    try:
                        if not isinstance(value, str) and len(value):
                            value = value[self.array_index]
                    except (TypeError, IndexError, KeyError):
                        pass
                    else:
                        if isinstance(value, (float, int, bool)):
                            return float(value)
        return 0.0