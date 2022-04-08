
from typing import TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, EnumProperty, PointerProperty, StringProperty
from .mixins import Layer
from .property_target import RBFDriverPropertyTarget
from .output_channels import RBFDriverOutputChannels
from ..app.events import dataclass, dispatch_event, Event
if TYPE_CHECKING:
    from bpy.types import Context


OUTPUT_ROTATION_MODE_ITEMS = [
    ('EULER'     , "Euler"     , "Drive the output target's euler rotation values"     , 'NONE', 0),
    ('QUATERNION', "Quaternion", "Drive the output target's quaternion rotation values", 'NONE', 1),
    ('AXIS_ANGLE', "Axis/Angle", "Drive the output target's axis/angle rotation values", 'NONE', 2),
    ]

OUTPUT_ROTATION_MODE_INDEX = {
    item[4]: item[0] for item in OUTPUT_ROTATION_MODE_ITEMS
    }

OUTPUT_ROTATION_MODE_TABLE = {
    item[0]: item[4] for item in OUTPUT_ROTATION_MODE_ITEMS
    }

OUTPUT_TYPE_ITEMS = [
    ('NONE'     , "Single Property" , "RNA property value"         , 'NONE', 0),
    ('LOCATION' , "Location"        , "Location transform channels", 'NONE', 1),
    ('ROTATION' , "Rotation"        , "Rotation transform channels", 'NONE', 2),
    ('SCALE'    , "Scale"           , "Scale transform channels"   , 'NONE', 3),
    ('BBONE'    , "BBone Properties", "BBone property values"      , 'NONE', 4),
    ('SHAPE_KEY', "Shape Key(s)"    , "Shape key values"           , 'NONE', 5),
    ]

OUTPUT_TYPE_INDEX = {
    item[0]: item[4] for item in OUTPUT_TYPE_ITEMS
    }


@dataclass(frozen=True)
class OutputNameUpdateEvent(Event):
    output: 'RBFDriverOutput'
    value: str


@dataclass(frozen=True)
class OutputRotationModeChangeEvent(Event):
    output: 'RBFDriverOutput'
    value: str
    previous_value: str


@dataclass(frozen=True)
class OutputUseLogarithmicMapUpdateEvent(Event):
    output: 'RBFDriverOutput'
    value: str


def output_mute(output: 'RBFDriverOutput') -> bool:
    return any(channel.mute for channel in output.channels if channel.is_enabled)


def output_mute_set(output: 'RBFDriverOutput', value: bool) -> None:
    for channel in output.channels:
        channel.mute = value


def output_name_update_handler(output: 'RBFDriverOutput', _: 'Context') -> None:
    dispatch_event(OutputNameUpdateEvent(output, output.name))


def output_rotation_mode(output: 'RBFDriverOutput') -> int:
    return output.get("rotation_mode", 0)


def output_rotation_mode_set(output: 'RBFDriverOutput', value: int) -> None:
    cache = output_rotation_mode(output)
    output["rotation_mode"] = value
    output["rotation_mode_is_user_defined"] = True
    dispatch_event(OutputRotationModeChangeEvent(output, output.rotation_mode, OUTPUT_ROTATION_MODE_INDEX[cache]))


def output_rotation_mode_is_user_defined(output: 'RBFDriverOutput') -> bool:
    return output.get("rotation_mode_is_user_defined", False)


def output_type(output: 'RBFDriverOutput') -> int:
    return output.get("type", 0)


def output_use_logarithmic_map_update_handler(output: 'RBFDriverOutput', _: 'Context') -> None:
    dispatch_event(OutputUseLogarithmicMapUpdateEvent(output, output.quaternion_interpolation_method))


class RBFDriverOutput(Layer, PropertyGroup):

    kind = 'OUTPUT'

    channels: PointerProperty(
        name="Channels",
        type=RBFDriverOutputChannels,
        options=set()
        )

    influence: PointerProperty(
        name="Influence",
        type=RBFDriverPropertyTarget,
        options=set()
        )

    @property
    def is_valid(self) -> bool:
        if self.type == 'NONE':
            return all(ch.is_valid for ch in self.channels)
        else:
            return self.channels[0].is_valid

    mute: BoolProperty(
        name="Mute",
        description=("Toggle the output drivers "
                     "(muting the output drivers allows editing of the driven values)"),
        get=output_mute,
        set=output_mute_set,
        options=set()
        )

    name: StringProperty(
        name="Name",
        default="Output",
        options=set(),
        update=output_name_update_handler
        )

    rotation_mode: EnumProperty(
        name="Mode",
        description="Rotation channels to drive (should match output target's rotation mode)",
        items=OUTPUT_ROTATION_MODE_ITEMS,
        get=output_rotation_mode,
        set=output_rotation_mode_set,
        options=set(),
        )

    rotation_mode_is_user_defined: BoolProperty(
        get=output_rotation_mode_is_user_defined,
        options={'HIDDEN'}
        )

    type: EnumProperty(
        name="Type",
        items=OUTPUT_TYPE_ITEMS,
        get=output_type,
        options=set()
        )

    use_logarithmic_map: BoolProperty(
        name="Log",
        default=False,
        update=output_use_logarithmic_map_update_handler
        )
