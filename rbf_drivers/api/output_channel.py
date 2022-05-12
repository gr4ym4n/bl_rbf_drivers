
from typing import Optional, TYPE_CHECKING
from bpy.types import ID, PropertyGroup
from bpy.props import (BoolProperty,
                       FloatProperty,
                       IntProperty,
                       PointerProperty,
                       StringProperty)
from .mixins import Symmetrical
from .output_channel_data import RBFDriverOutputChannelData
from ..app.events import dataclass, dispatch_event, Event
if TYPE_CHECKING:
    from bpy.types import Context


@dataclass(frozen=True)
class OutputChannelMuteUpdateEvent(Event):
    channel: 'RBFDriverOutputChannel'
    value: bool


@dataclass(frozen=True)
class OutputChannelNameChangeEvent(Event):
    channel: 'RBFDriverOutputChannel'
    value: str
    previous_value: str


def output_channel_array_index(channel: 'RBFDriverOutputChannel') -> int:
    return channel.get("array_index", 0)


def output_channel_data_path(channel: 'RBFDriverOutputChannel') -> str:
    return channel.get("data_path", "")


def output_channel_is_enabled(channel: 'RBFDriverOutputChannel') -> bool:
    return channel.get("is_enabled", False)


def output_channel_mute_update_handler(channel: 'RBFDriverOutputChannel', _: 'Context') -> None:
    dispatch_event(OutputChannelMuteUpdateEvent(channel, channel.mute))


def output_channel_name(channel: 'RBFDriverOutputChannel') -> str:
    return channel.get("name", "")


def output_channel_name_set(channel: 'RBFDriverOutputChannel', value: str) -> None:
    cache = output_channel_name(channel)
    channel["name"] = value
    dispatch_event(OutputChannelNameChangeEvent(channel, value, cache))


class RBFDriverOutputChannel(Symmetrical, PropertyGroup):

    array_index: IntProperty(
        name='Index',
        description="Output channel array index (read-only)",
        get=output_channel_array_index,
        options=set(),
        )

    data_path: StringProperty(
        name="Path",
        description="",
        get=output_channel_data_path,
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

    id__internal__: PointerProperty(
        type=ID,
        options={'HIDDEN'}
        )

    @property
    def id(self) -> Optional[ID]:
        return self.id__internal__

    is_enabled: BoolProperty(
        name="Enabled",
        get=output_channel_is_enabled,
        options=set()
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
        default=True,
        options=set(),
        update=output_channel_mute_update_handler
        )

    name: StringProperty(
        name="Name",
        description="Name of the output channel",
        get=output_channel_name,
        set=output_channel_name_set,
        options=set()
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

    def __repr__(self) -> str:
        result = f'{self.__class__.__name__}(name="{self.name}"'
        result += f', id={self.id}'
        result += f', data_path="{self.data_path}"'
        if self.is_property_set("array_index"):
            result += f', array_index={self.array_index}'
        result += f', default_value={self.default_value}'
        result += f', is_enabled={self.is_enabled}'
        result += f', mute={self.mute}'
        result += ")"
        return result

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".collection__internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'