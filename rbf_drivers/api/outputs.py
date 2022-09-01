
#region Imports
#--------------------------------------------------------------------------------------------------

from typing import TYPE_CHECKING, Optional
from bpy.types import Object, PropertyGroup
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    IntProperty,
    PointerProperty,
    StringProperty
    )
from .mixins import (
    Collection,
    Reorderable,
    Searchable,
    Symmetrical,
    IDPropertyController,
    IDPropertyQuaternionController
    )
from .property_target import RBFDriverPropertyTarget
from .output_channels import RBFDriverOutputChannels
from ..app.events import dataclass, dispatch_event, Event
if TYPE_CHECKING:
    from bpy.types import Context, ID

#endregion


#region

class LogarithmicSum(IDPropertyController, PropertyGroup):

    @property
    def output(self) -> 'Output':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])


class Magnitude(IDPropertyController, PropertyGroup):

    @property
    def output(self) -> 'Output':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])


class Sine(IDPropertyController, PropertyGroup):

    @property
    def output(self) -> 'Output':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])


class Exponent(IDPropertyController, PropertyGroup):

    @property
    def output(self) -> 'Output':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])


class ExponentialMap(IDPropertyQuaternionController, PropertyGroup):

    @property
    def output(self) -> 'Output':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])


#endregion


#region Output
#--------------------------------------------------------------------------------------------------

OUTPUT_ID_TYPE_ITEMS = [
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

OUTPUT_ID_TYPE_INDEX = [
    item[0] for item in OUTPUT_ID_TYPE_ITEMS
    ]

OUTPUT_ID_TYPE_TABLE = {
    item[0]: item[4] for item in OUTPUT_ID_TYPE_ITEMS
    }

OUTPUT_ROTATION_MODE_ITEMS = [
    ('EULER'     , "Euler"     , "Drive the output target's euler rotation values"     ),
    ('QUATERNION', "Quaternion", "Drive the output target's quaternion rotation values"),
    ('AXIS_ANGLE', "Axis/Angle", "Drive the output target's axis/angle rotation values"),
    ]

OUTPUT_ROTATION_MODE_INDEX = [
    item[0] for item in OUTPUT_ROTATION_MODE_ITEMS
    ]

OUTPUT_ROTATION_MODE_TABLE = {
    item[0]: index for index, item in enumerate(OUTPUT_ROTATION_MODE_ITEMS)
    }

OUTPUT_TYPE_ITEMS = [
    ('LOCATION'   , "Location"        , "Location transform channels", 'CON_LOCLIMIT' , 0),
    ('ROTATION'   , "Rotation"        , "Rotation transform channels", 'CON_ROTLIMIT' , 1),
    ('SCALE'      , "Scale"           , "Scale transform channels"   , 'CON_SIZELIMIT', 2),
    None,
    ('SHAPE_KEY'  , "Shape Key"       , "Shape key value"            , 'SHAPEKEY_DATA'   , 3),
    ('SINGLE_PROP', "Single Property" , "RNA property value"         , 'RNA'             , 4),
    ]

OUTPUT_TYPE_INDEX = [
    item[0] for item in OUTPUT_TYPE_ITEMS if item is not None
    ]

OUTPUT_TYPE_TABLE = {
    item[0]: item[4] for item in OUTPUT_TYPE_ITEMS if item is not None
    }

OUTPUT_TYPE_ICONS = {
    item[0]: item[3] for item in OUTPUT_TYPE_ITEMS if item is not None
    }


@dataclass(frozen=True)
class OutputPropertyUpdateEvent(Event):
    output: 'Output'


@dataclass(frozen=True)
class OutputBoneTargetUpdateEvent(OutputPropertyUpdateEvent):
    value: str
    previous_value: str


@dataclass(frozen=True)
class OutputDataPathChangeEvent(OutputPropertyUpdateEvent):
    value: str
    previous_value: str


@dataclass(frozen=True)
class OutputIDTypeUpdateEvent(OutputPropertyUpdateEvent):
    value: str


@dataclass(frozen=True)
class OutputNameUpdateEvent(OutputPropertyUpdateEvent):
    value: str


@dataclass(frozen=True)
class OutputObjectUpdateEvent(OutputPropertyUpdateEvent):
    value: Optional[Object]
    previous_value: Optional[Object]


@dataclass(frozen=True)
class OutputRotationModeUpdateEvent(OutputPropertyUpdateEvent):
    value: str
    previous_value: str


@dataclass(frozen=True)
class OutputUseAxisUpdateEvent(OutputPropertyUpdateEvent):
    axis: str
    value: bool


@dataclass(frozen=True)
class OutputUseMirrorXUpdateEvent(OutputPropertyUpdateEvent):
    value: bool


@dataclass(frozen=True)
class OutputUseLogarithmicMapUpdateEvent(OutputPropertyUpdateEvent):
    value: str


def output_bone_target(output: 'Output') -> str:
    return output.get("bone_target", "")


def output_bone_target_set(output: 'Output', value: str) -> str:
    cache = output_bone_target(output)
    output["bone_target"] = value
    if output.type == 'ROTATION' and not output.rotation_mode_is_user_defined:
        dispatch_event(OutputBoneTargetUpdateEvent(output, value, cache))


def output_data_path(output: 'Output') -> str:
    return output.get("data_path", "")


def output_data_path_set(output: 'Output', value: str) -> None:
    if output.type != 'SINGLE_PROP':
        raise RuntimeError((f'{output.__class__.__name__}.data_path '
                            f'is not user-editable for outputs of type {output.type}'))

    cache = output_data_path(output)
    output["data_path"] = value
    dispatch_event(OutputDataPathChangeEvent(output, value, cache))


def output_id_type(output: 'Output') -> int:
    return output.get("id_type", 0)


def output_id_type_set(output: 'Output', value: int) -> None:
    if output.type != 'SINGLE_PROP':
        raise RuntimeError((f'{output.__class__.__name__}.id_type '
                            f'is not editable for outputs of type {output.type}'))

    output["id_type"] = value
    dispatch_event(OutputIDTypeUpdateEvent(output, output.id_type))


def output_is_enabled(output: 'Output') -> bool:
    return any(channel.is_enabled for channel in output.channels)


def output_is_valid(output: 'Output') -> bool:
    object = output.object
    if object is None:
        return False
    if output.type in {'LOCATION', 'ROTATION', 'SCALE'}:
        if object.type == 'ARMATURE' and output.bone_target:
            return output.bone_target in object.data.bones
        else:
            return True
    else:
        return output.channels[0].is_valid


def output_mute(output: 'Output') -> bool:
    return all(channel.mute for channel in output.channels if channel.is_enabled)


def output_mute_set(output: 'Output', value: bool) -> None:
    for channel in output.channels:
        channel.mute = value


def output_name_update_handler(output: 'Output', _: 'Context') -> None:
    dispatch_event(OutputNameUpdateEvent(output, output.name))


def output_name_is_user_defined(output: 'Output') -> bool:
    return output.get("name_is_user_defined", False)


def output_object_update_handler(output: 'Output', _: 'Context') -> None:
    cache = output.object__internal__
    value = output.object
    output.object__internal__ = value
    if output.type != 'SINGLE_PROP':
        dispatch_event(OutputObjectUpdateEvent(output, value, cache))


def output_object_validate(output: 'Output', object: Object) -> bool:
    if output.type == 'SHAPE_KEY':
        return object.type in {'MESH', 'LATTICE', 'CURVE'}
    return output.id_type in {object.type, 'OBJECT'}


def output_rotation_mode(output: 'Output') -> int:
    return output.get("rotation_mode", 0)


def output_rotation_mode_set(output: 'Output', value: int) -> None:
    cache = output_rotation_mode(output)
    output["rotation_mode"] = value
    output["rotation_mode_is_user_defined"] = True
    if output.type == 'ROTATION':
        dispatch_event(OutputRotationModeUpdateEvent(output, output.rotation_mode, OUTPUT_ROTATION_MODE_INDEX[cache]))


def output_rotation_mode_is_user_defined(output: 'Output') -> bool:
    return output.get("rotation_mode_is_user_defined", False)


def output_type(output: 'Output') -> int:
    return output.get("type", 0)


def output_use_mirror_x_update_handler(output: 'Output', _: 'Context') -> None:
    dispatch_event(OutputUseMirrorXUpdateEvent(output, output.use_mirror_x))


def output_use_x_update_handler(output: 'Output', _: 'Context') -> None:
    dispatch_event(OutputUseAxisUpdateEvent(output, 'X', output.use_x))


def output_use_y_update_handler(output: 'Output', _: 'Context') -> None:
    dispatch_event(OutputUseAxisUpdateEvent(output, 'Y', output.use_y))


def output_use_z_update_handler(output: 'Output', _: 'Context') -> None:
    dispatch_event(OutputUseAxisUpdateEvent(output, 'Z', output.use_z))


def output_use_logarithmic_map_update_handler(output: 'Output', _: 'Context') -> None:
    dispatch_event(OutputUseLogarithmicMapUpdateEvent(output, output.quaternion_interpolation_method))


class Output(Symmetrical, PropertyGroup):

    bone_target: StringProperty(
        name="Bone",
        description="Name of pose bone to drive",
        get=output_bone_target,
        set=output_bone_target_set,
        options=set()
        )

    channels: PointerProperty(
        name="Channels",
        type=RBFDriverOutputChannels,
        options=set()
        )

    data_path: StringProperty(
        name="Path",
        description="",
        get=output_data_path,
        set=output_data_path_set,
        options=set()
        )

    exponent: PointerProperty(
        name="Exponent",
        description="Exponent of the summed logarithmic maps",
        type=Exponent,
        options=set()
        )

    exponential_map: PointerProperty(
        name="Exponential Map",
        description="Exponential map of the summed logarithmic maps"
        )

    id_type: EnumProperty(
        name="Type",
        items=OUTPUT_ID_TYPE_ITEMS,
        get=output_id_type,
        set=output_id_type_set,
        options=set(),
        )

    @property
    def id(self) -> Optional['ID']:
        object = self.object__internal__
        if object is not None:
            if self.type == 'SHAPE_KEY':
                return getattr(object.data, "shape_keys", None)
            if self.id_type != 'OBJECT':
                return object.data if object.type == self.id_type else None
        return object

    influence: PointerProperty(
        name="Influence",
        type=RBFDriverPropertyTarget,
        options=set()
        )

    is_enabled: BoolProperty(
        name="Enabled",
        description="Whether the output is currently enabled (read-only)",
        get=output_is_enabled,
        options=set()
        )

    is_valid: BoolProperty(
        name="Valid",
        description="Whether the output has a valid target or not (read-only)",
        get=output_is_valid,
        options=set()
        )

    logarithmic_sum: PointerProperty(
        name="Logsum",
        description="Sum of logarithmic maps",
        type=LogarithmicSum,
        options=set()
        )

    magnitude: PointerProperty(
        name="Magnitude",
        description="Magnitude of the logarithmic sum",
        type=Magnitude,
        options=set()
        )

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
        description="Output name",
        update=output_name_update_handler,
        options=set()
        )

    name_is_user_defined: BoolProperty(
        name="User Defined Name",
        description="Name is user-defined (internal use)",
        get=output_name_is_user_defined,
        options=set()
        )

    object__internal__: PointerProperty(
        type=Object,
        options={'HIDDEN'}
        )

    object: PointerProperty(
        name="Object",
        description="The target object",
        type=Object,
        poll=output_object_validate,
        options=set(),
        update=output_object_update_handler
        )

    rotation_mode: EnumProperty(
        name="Mode",
        description="Rotation channels to drive",
        items=OUTPUT_ROTATION_MODE_ITEMS,
        get=output_rotation_mode,
        set=output_rotation_mode_set,
        options=set(),
        )

    rotation_mode_is_user_defined: BoolProperty(
        get=output_rotation_mode_is_user_defined,
        options={'HIDDEN'}
        )

    sine: PointerProperty(
        name="Sine",
        descroption="Sine of the magnitude",
        type=Sine,
        options=set()
        )

    type: EnumProperty(
        name="Type",
        items=OUTPUT_TYPE_ITEMS,
        get=output_type,
        options=set()
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
        update=output_use_mirror_x_update_handler
        )

    use_x: BoolProperty(
        name="X",
        description="Use X axis",
        default=False,
        options=set(),
        update=output_use_x_update_handler
        )

    use_y: BoolProperty(
        name="Y",
        description="Use Y axis",
        default=False,
        options=set(),
        update=output_use_y_update_handler
        )

    use_z: BoolProperty(
        name="Z",
        description="Use Z axis",
        default=False,
        options=set(),
        update=output_use_z_update_handler
        )

    use_logarithmic_map: BoolProperty(
        name="Log",
        default=False,
        update=output_use_logarithmic_map_update_handler
        )

    def __repr__(self) -> str:
        # TODO
        return super().__repr__()

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'

#endregion

#region Outputs
#--------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class OutputNewEvent(Event):
    output: Output


@dataclass(frozen=True)
class OutputDisposableEvent(Event):
    output: Output


@dataclass(frozen=True)
class OutputRemovedEvent(Event):
    outputs: 'RBFDriverOutputs'
    index: int


@dataclass(frozen=True)
class OutputMoveEvent(Event):
    output: Output
    from_index: int
    to_index: int


def outputs_mute(outputs: 'RBFDriverOutputs') -> bool:
    return all(map(output_mute, outputs))


def outputs_mute_set(outputs: 'RBFDriverOutputs', value: bool) -> None:
    for output in outputs:
        output.mute = value


class RBFDriverOutputs(Reorderable, Searchable[Output], Collection[Output], PropertyGroup):

    internal__: CollectionProperty(
        type=Output,
        options={'HIDDEN'}
        )

    active_index: IntProperty(
        name="Output",
        description="An RBF driver output",
        min=0,
        default=0,
        options=set()
        )

    @property
    def active(self) -> Optional[Output]:
        index = self.active_index
        return self[index] if index < len(self) else None

    mute: BoolProperty(
        name="Mute",
        description="Mute/Unmute output drivers",
        get=outputs_mute,
        set=outputs_mute_set,
        options=set()
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(active_index={self.active_index})'

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'

    def move(self, from_index: int, to_index: int) -> None:
        super().move(from_index, to_index)
        dispatch_event(OutputMoveEvent(self, from_index, to_index))

    def new(self, type: str) -> Output:

        if not isinstance(type, str):
            raise TypeError((f'{self.__class__.__name__}.new(type): '
                             f'Expected type to be str, not {type.__class__.__name__}'))

        if type not in OUTPUT_TYPE_INDEX:
            raise ValueError((f'{self.__class__.__name__}.new(type): '
                              f'type {type} not found in {", ".join(OUTPUT_TYPE_INDEX)}'))

        output: Output = self.internal__.add()
        output["type"] = OUTPUT_TYPE_TABLE[type]

        dispatch_event(OutputNewEvent(output))

        self.active_index = len(self) - 1
        return output

    def remove(self, output: Output) -> None:

        if not isinstance(output, Output):
            raise TypeError((f'{self.__class__.__name__}.remove(output): '
                             f'Expected input to be {Output.__name__}, '
                             f'not {output.__class__.__name__}'))

        index = next((index for index, item in enumerate(self) if item == output), -1)

        if index == -1:
            raise ValueError((f'{self.__class__.__name__}.remove(output): '
                              f'{output} not found in {self}'))

        dispatch_event(OutputDisposableEvent(output))
        self.internal__.remove(index)
        dispatch_event(OutputRemovedEvent(output, index))

#endregion