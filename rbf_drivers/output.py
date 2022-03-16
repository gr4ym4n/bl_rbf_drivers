
#region Imports
###################################################################################################

import re
import sys
import logging
from functools import partial
from typing import Any, Iterator, List, Match, Optional, Tuple, Union, TYPE_CHECKING
from math import floor

from bpy.app import version
from bpy.types import ID, Object, PropertyGroup
from bpy.props import (BoolProperty,
                       CollectionProperty,
                       EnumProperty,
                       FloatProperty,
                       IntProperty,
                       PointerProperty,
                       StringProperty)
from rbf_drivers.lib.symmetry import symmetrical_target
import rna_prop_ui
import numpy as np

from .lib.driver_utils import (DriverVariableNameGenerator,
                               driver_ensure,
                               driver_find,
                               driver_remove,
                               driver_variables_clear)

from .lib.rotation_utils import (axis_angle_to_euler,
                                 axis_angle_to_quaternion,
                                 euler_to_axis_angle,
                                 euler_to_quaternion,
                                 quaternion_to_axis_angle,
                                 quaternion_to_euler,
                                 quaternion_to_logarithmic_map)

from .pose import RBFDriverPoses
from .posedata import ACTIVE_POSE_DATA_ROTATION_CONVERSION_LUT, RBFDriverPoseDataVector, ActivePoseData
from .mixins import ID_TYPE_ITEMS, LAYER_TYPE_ITEMS, Identifiable, Symmetrical

if TYPE_CHECKING:
    from .driver import RBFDriver

#endregion Imports

#region Configuration
###################################################################################################

log = logging.getLogger("rbf_drivers")

DEBUG = 'DEBUG_MODE' in sys.argv

MAX_PARAMS = 36

OUTPUT_CHANNEL_DEFINITIONS = {
    'LOCATION': [
        {
            "name": "x",
            "default": 0.0,
            "data_path": "location",
            "array_index": 0
        },{
            "name": "y",
            "default": 0.0,
            "data_path": "location",
            "array_index": 1
        },{
            "name": "z",
            "default": 0.0,
            "data_path": "location",
            "array_index": 2
        }
        ],
    'ROTATION': [
        {
            "name": "w",
            "default": 1.0,
            "data_path": "rotation_quaternion",
            "array_index": 0
        },{
            "name": "x",
            "default": 0.0,
            "data_path": "rotation_quaternion",
            "array_index": 1
        },{
            "name": "y",
            "default": 0.0,
            "data_path": "rotation_quaternion",
            "array_index": 2
        },{
            "name": "z",
            "default": 0.0,
            "data_path": "rotation_quaternion",
            "array_index": 3
        }
        ],
    'SCALE': [
        {
            "name": "x",
            "default": 1.0,
            "data_path": "scale",
            "array_index": 0
        },{
            "name": "y",
            "default": 1.0,
            "data_path": "scale",
            "array_index": 1
        },{
            "name": "z",
            "default": 1.0,
            "data_path": "scale",
            "array_index": 2
        }
        ],
    'BBONE': [
        {
            "name": "bbone_curveinx",
            "default": 0.0,
            "data_path": 'pose.bones[""].bbone_curveinx',
        },{
            "name": "bbone_curveoutz",
            "default": 0.0,
            "data_path": 'pose.bones[""].bbone_curveoutz',
        },{
            "name": "bbone_curveoutx",
            "default": 0.0,
            "data_path": 'pose.bones[""].bbone_curveoutx',
        },{
            "name": "bbone_curveoutz",
            "default": 0.0,
            "data_path": 'pose.bones[""].bbone_curveoutz',
        },{
            "name": "bbone_easein",
            "default": 0.0,
            "data_path": 'pose.bones[""].bbone_easein',
        },{
            "name": "bbone_easeout",
            "default": 0.0,
            "data_path": 'pose.bones[""].bbone_easeout',
        },{
            "name": "bbone_rollin",
            "default": 0.0,
            "data_path": 'pose.bones[""].bbone_rollin',
        },{
            "name": "bbone_rollout",
            "default": 0.0,
            "data_path": 'pose.bones[""].bbone_rollout',
        },{
            "name": "bbone_scaleinx",
            "default": 1.0,
            "data_path": f'pose.bones[""].bbone_scalein[0]',
        },{
            "name": "bbone_scaleiny",
            "default": 1.0,
            "data_path":'pose.bones[""].bbone_scalein[1]',
        },{
            "name": "bbone_scaleinz",
            "default": 1.0,
            "data_path": f'pose.bones[""].bbone_scalein[2]',
        },{
            "name": "bbone_scaleoutx",
            "default": 1.0,
            "data_path": f'pose.bones[""].bbone_scaleout[0]',
        },{
            "name": "bbone_scaleouty",
            "default": 1.0,
            "data_path": f'pose.bones[""].bbone_scaleout[1]',
        },{
            "name": "bbone_scaleoutz",
            "default": 1.0,
            "data_path": f'pose.bones[""].bbone_scaleout[2]',
        }
        ],
    'SHAPE_KEY': [
        {
            "name": "",
            "default": 0.0,
            "data_path": 'key_blocks[""].value',
        }
        ],
    'NONE': [
        {
            "name": "",
            "default": 0.0,
            "data_path": ""
        }
        ]
    }

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

ROTATION_CONVERSION_LUT = {
    'EULER': {
        'QUATERNION': euler_to_quaternion,
        'AXIS_ANGLE': partial(euler_to_axis_angle, vectorize=True)
        },
    'QUATERNION': {
        'EULER': quaternion_to_euler,
        'AXIS_ANGLE': partial(quaternion_to_axis_angle, vectorize=True)
        },
    'AXIS_ANGLE': {
        'EULER': axis_angle_to_euler,
        'QUATERNION': axis_angle_to_quaternion
        }
    }

#endregion Configuration

#region Data Layer
###################################################################################################

#region Output Channel Range
###################################################################################################

class RBFDriverOutputChannelRange(PropertyGroup):

    start: IntProperty(
        min=0,
        get=lambda self: self.get("start", 0),
        options={'HIDDEN'}
        )

    stop: IntProperty(
        min=0,
        get=lambda self: self.get("stop", 0),
        options={'HIDDEN'}
        )

    def __init__(self, start: int, stop: int) -> None:
        self["start"] = start
        self["stop"] = stop

#endregion Output Channel Range

#region Output Channel
###################################################################################################

def output_channel_bone_target_get(channel: 'RBFDriverOutputChannel') -> str:
    return channel.get("bone_target", "")


def output_channel_bone_target_set(channel: 'RBFDriverOutputChannel', value: str) -> None:
    output = channel.output

    if output.type not in {'LOCATION', 'ROTATION', 'SCALE', 'BBONE'}:
        channel["bone_target"] = value
        return

    updating_rot = not output.rotation_mode_is_user_defined and output.type == 'ROTATION'
    prev_rotmode = ""
    curr_rotmode = ""

    output_drivers_remove(output)

    if updating_rot:
        prev_rotmode = output_channel_target_rotation_mode(channel, output)

    output_foreach_channel_update_property(output, "bone_target", value)
    output_foreach_channel_update_datapath(output)

    if updating_rot:
        curr_rotmode = output_channel_target_rotation_mode(channel, output)
        if prev_rotmode != curr_rotmode:
            output_rotdata_update(output, prev_rotmode, curr_rotmode)
            output_idprops_update(output, output.pose_count)

    output_drivers_update(output)

    if channel.has_symmetry_target:
        mirror = symmetrical_target(value)
        output_channel_mirror_property(channel, "bone_target", mirror or value)


def data_path_split(path: str) -> Tuple[str, int]:
    if path.endswith("]"):
        idx = path.rfind("[")
        key = path[idx+1:-1]
        if key.isdigit():
            return path[:idx], int(key)
    return path, -1


def output_channel_data_path_get(channel: 'RBFDriverOutputChannel') -> str:
    return channel.get("data_path", "")


def output_channel_data_path_set(channel: 'RBFDriverOutputChannel', value: str) -> None:
    output = channel.output
    if output.type != 'NONE':
        raise RuntimeError((f'{channel.__class__.__name__}.data_path '
                            f'is not user-editable for this output type'))
    else:
        output_drivers_remove(output)
        channel["data_path"] = value
        output_drivers_update(output, output.pose_count)

    if channel.has_symmetry_target:
        def replace(match: Match):
            value = match.group()
            return symmetrical_target(value) or value

        output_channel_mirror_property(channel, "data_path", re.findall(r'\["(.*?)"\]', replace, value))


def output_channel_enabled_update_handler(channel: 'RBFDriverOutputChannel', _) -> None:
    output = channel.output
    poses = output.rbf_driver.poses
    output_idprops_update(output, len(poses))
    output_drivers_remove(output)
    output_drivers_update(output, poses)
    output_channel_mirror_property(channel, "enabled")


def output_channel_invert_update_handler(channel: 'RBFDriverOutputChannel', _) -> None:
    if channel.has_symmetry_target:
        # TODO
        output_channel_mirror_property(channel, "invert")


def output_channel_mute_update_handler(channel: 'RBFDriverOutputChannel', _) -> None:
    if channel.enabled:
        id = channel.id
        if id:
            type = channel.output.type

            if type == 'NONE':
                path, index = data_path_split(channel.data_path)
            else:
                path = channel.data_path
                index = channel.array_index if type in {'LOCATION', 'ROTATION', 'SCALE'} else -1

            if index >= 0:
                fcurve = driver_find(id, path, index)
            else:
                fcurve = driver_find(id, path)

            if fcurve:
                fcurve.mute = channel.mute

    if channel.has_symmetry_target:
        output_channel_mirror_property(channel, "mute")


def output_channel_id_type_update_handler(channel: 'RBFDriverOutputChannel', _) -> None:
    output = channel.output

    if output.type != 'NONE':
        raise RuntimeError((f'{channel} id_type is not editable for outputs of type {output.type}'))

    idtype = channel.id_type
    object = channel.object__internal__

    if object is not None and object.type != idtype:
        channel.object = None

    if channel.has_symmetry_target:
        output_channel_mirror_property(channel, "id_type")


def output_channel_object_update_handler(channel: 'RBFDriverOutputChannel', _) -> None:
    object = channel.object

    if object != channel.object__internal__:
        output = channel.output

        updating_rot = not output.rotation_mode_is_user_defined and output.type == 'ROTATION'
        prev_rotmode = ""
        curr_rotmode = ""

        output_drivers_remove(output)

        if updating_rot:
            prev_rotmode = output_channel_target_rotation_mode(channel, output)

        if output.type == 'NONE':
            channel.object__internal__ = object
        else:
            for channel in output.channels:
                channel.object__internal__ = object
                channel.object = object

        if updating_rot:
            curr_rotmode = output_channel_target_rotation_mode(channel, output)
            if prev_rotmode != curr_rotmode:
                output_idprops_remove(output)
                output_rotdata_update(output, prev_rotmode, curr_rotmode)
                output["rotation_mode"] = OUTPUT_ROTATION_MODE_TABLE[curr_rotmode]
                output_foreach_channel_update_datapath(output)
                output_idprops_update(output, output.pose_count)

        output_drivers_update(output, output.rbf_driver.poses)

        if channel.has_symmetry_target:
            output_channel_mirror_property(channel, "object")


class RBFDriverOutputChannel(Symmetrical, PropertyGroup):

    array_index: IntProperty(
        name='Index',
        description="Channel data array index (read-only)",
        get=lambda self: self.get("array_index", 0),
        options=set(),
        )

    bone_target: StringProperty(
        name="Bone",
        description="The pose bone to target",
        get=output_channel_bone_target_get,
        set=output_channel_bone_target_set,
        options=set(),
        )

    data: PointerProperty(
        name="Data",
        type=RBFDriverPoseDataVector,
        options=set()
        )

    data_path: StringProperty(
        name="Data",
        description="Path to the driven property",
        get=output_channel_data_path_get,
        set=output_channel_data_path_set,
        options=set(),
        )

    default: FloatProperty(
        name="Default",
        default=0.0,
        options=set(),
        )

    enabled: BoolProperty(
        name="Enabled",
        default=False,
        options=set(),
        update=output_channel_enabled_update_handler
        )

    id_type: EnumProperty(
        name="Type",
        items=ID_TYPE_ITEMS,
        default='OBJECT',
        options=set(),
        update=output_channel_id_type_update_handler
        )

    @property
    def id(self) -> Optional[ID]:
        object = self.object__internal__
        if object is None or self.id_type == 'OBJECT': return object
        if object.type == self.id_type: return object.data

    invert: BoolProperty(
        name="Invert",
        description="Invert the output channel's value when mirroring",
        default=False,
        options=set(),
        update=output_channel_invert_update_handler
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
    def output(self) -> 'RBFDriverOutput':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".channels.")[0])

    @property
    def pose_data_property_name(self) -> str:
        return f'rbfo_data_{self.identifier}'

    @property
    def pose_data_property_path(self) -> str:
        return f'["{self.pose_data_property_name}"]'

    @property
    def driven_property_name(self) -> str:
        return f'rbfo_prod_{self.identifier}'

    @property
    def driven_property_path(self) -> str:
        return f'["{self.driven_property_name}"]'

    ranges__internal__: CollectionProperty(
        type=RBFDriverOutputChannelRange,
        options={'HIDDEN'}
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
                try:
                    if not isinstance(value, str) and len(value):
                        value = value[self.array_index]
                except (TypeError, IndexError, KeyError):
                    pass
                else:
                    if isinstance(value, (float, int, bool)):
                        return float(value)
        return 0.0


#endregion Output Channel

#region Output Channels
###################################################################################################

class RBFDriverOutputChannels(PropertyGroup):

    collection__internal__: CollectionProperty(
        type=RBFDriverOutputChannel,
        options={'HIDDEN'}
        )

    def __len__(self) -> int:
        return len(self.collection__internal__)

    def __iter__(self) -> Iterator[RBFDriverOutputChannel]:
        return iter(self.collection__internal__)

    def __getitem__(self, key: Union[str, int, slice]) -> Union[RBFDriverOutputChannel, List[RBFDriverOutputChannel]]:
        return self.collection__internal__[key]

    def find(self, name: str) -> int:
        return self.collection__internal__.find(name)

    def get(self, name: str) -> Optional[RBFDriverOutputChannel]:
        return self.collection__internal__.get(name)

    def keys(self) -> Iterator[str]:
        return self.collection__internal__.keys()

    def items(self) -> Iterator[Tuple[str, RBFDriverOutputChannel]]:
        return self.collection__internal__.items()

    def search(self, identifier: str) -> Optional[RBFDriverOutputChannel]:
        return next((channel for channel in self if channel.identifier == identifier), None)

    def values(self) -> Iterator[RBFDriverOutputChannel]:
        return iter(self)

#endregion Output Channels

#region Output Active Pose Data
###################################################################################################

class RBFDriverOutputActivePoseData(ActivePoseData['RBFDriverOutput'], PropertyGroup):

    def __init__(self, output: 'RBFDriverOutput', pose_index: int) -> None:
        self["type"] = output.get("type")
        chans = output.channels
        keys = chans.keys()
        vals = [ch.data[pose_index].value for ch in chans]

        if output.type == 'ROTATION':
            outputmode = output.rotation_mode
            activemode = self.rotation_mode

            if outputmode != activemode:
                cast = ACTIVE_POSE_DATA_ROTATION_CONVERSION_LUT[outputmode][activemode]
                vals = cast(vals)

        data = self.data__internal__
        data.clear()

        for key, val in zip(keys, vals):
            item = data.add()
            item["name"] = key
            item["value"] = val

    def update(self) -> None:
        output = self.layer
        values = list(self.values())

        if output.type == 'ROTATION':
            activemode = self.rotation_mode
            outputmode = output.rotation_mode
            if activemode != outputmode:
                values = ACTIVE_POSE_DATA_ROTATION_CONVERSION_LUT[activemode][outputmode](values)
        
        pose_index = output.rbf_driver.poses.active_index

        for channel, value in zip(output.channels, values):
            channel.data[pose_index]["value"] = value

        output_pose_data_idprops_update(output)

#endregion Output Active Pose Data

#region Output
###################################################################################################

def output_mute_get(output: 'RBFDriverOutput') -> bool:
    return all(channel.mute for channel in output.channels)


def output_mute_set(output: 'RBFDriverOutput', value: bool) -> None:
    for channel in output.channels:
        channel.mute = value


def output_name_update_handler(output: 'RBFDriverOutput', _) -> None:
    names = [output.name for output in output.id_data.path_resolve(output.path_from_id.rpartition(".")[0])]
    value = output.name
    index = 0
    while value in names:
        index += 1
        value = f'{output.name}.{str(index).zfill(3)}'
    output["name"] = value

    if output.has_symmetry_target:
        output_mirror_property(output, "name")


def output_use_logarithmic_map_update_handler(output: 'RBFDriverOutput', _) -> None:
    if output.type == 'ROTATION' and output.rotation_mode == 'QUATERNION':
        output_drivers_update(output, output.rbf_driver.poses)

    if output.has_symmetry_target:
        output_mirror_property(output, "use_logarithmic_map")


def output_rotation_mode_get(output: 'RBFDriverOutput') -> int:
    return output.get("rotation_mode", 0)


def output_rotation_mode_set(output: 'RBFDriverOutput', value: int) -> None:
    cache = output_rotation_mode_get(output)
    if cache != value:
        output["rotation_mode_is_user_defined"] = True

        if output.type != 'ROTATION':
            output["rotation_mode"] = value
        else:
            output_idprops_remove(output)
            output_drivers_remove(output)

            output["rotation_mode"] = value
            channels = output.channels

            if (OUTPUT_ROTATION_MODE_INDEX[cache] == 'EULER'
                and all(channel.enabled for channel in channels[1:])
                ):
                channels[0]["enabled"] = True

            elif OUTPUT_ROTATION_MODE_INDEX[value] == 'EULER':
                channels[0]["enabled"] = False
                channels = channels[1:]

            output_foreach_channel_update_datapath(output)

            for index, channel in enumerate(channels):
                channel["array_index"] = index

            output_rotdata_update(output,
                                  OUTPUT_ROTATION_MODE_INDEX[cache],
                                  OUTPUT_ROTATION_MODE_INDEX[value])

            poses = output.rbf_driver.poses
            output_idprops_update(output, len(poses))
            output_drivers_update(output, poses)

    if output.has_symmetry_target:
        output_mirror_property(output, "rotation_mode")


class RBFDriverOutput(Symmetrical, PropertyGroup):

    active_pose: PointerProperty(
        name="Pose",
        type=RBFDriverOutputActivePoseData,
        options=set()
        )

    channels: PointerProperty(
        name="Channels",
        type=RBFDriverOutputChannels,
        options=set()
        )

    @property
    def influence_property_name(self) -> str:
        return f'rbfo_infl_{self.identifier}'

    @property
    def influence_property_path(self) -> str:
        return f'["{self.influence_property_name}"]'

    mute: BoolProperty(
        name="Mute",
        description=("Toggle the output drivers "
                     "(muting the output drivers allows editing of the driven values)"),
        get=output_mute_get,
        set=output_mute_set,
        options=set()
        )

    name: StringProperty(
        name="Name",
        default="Output",
        options=set(),
        update=output_name_update_handler
        )

    @property
    def logmap_property_name(self) -> str:
        return f'rbfo_expn_{self.identifier}'

    @property
    def logmap_property_path(self) -> str:
        return f'["{self.logmap_property_name}"]'

    @property
    def logmap_magnitude_property_name(self) -> str:
        return f'rbfo_magn_{self.identifier}'

    @property
    def logmap_magnitude_property_path(self) -> str:
        return f'["{self.logmap_magnitude_property_name}"]'

    @property
    def pose_count(self) -> int:
        return len(self.rbf_driver.poses)

    @property
    def rbf_driver(self) -> 'RBFDriver':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".outputs.")[0])

    rotation_mode: EnumProperty(
        name="Mode",
        description="Rotation channels to drive (should match output target's rotation mode)",
        items=OUTPUT_ROTATION_MODE_ITEMS,
        get=output_rotation_mode_get,
        set=output_rotation_mode_set,
        options=set(),
        )

    rotation_mode_is_user_defined: BoolProperty(
        get=lambda self: self.get("rotation_mode_is_user_defined", False),
        options=set()
        )

    type: EnumProperty(
        name="Type",
        items=LAYER_TYPE_ITEMS,
        get=lambda self: self.get("type", 0),
        options=set()
        )

    use_logarithmic_map: BoolProperty(
        name="Logarithmic Map",
        description=("Use a logarithmic map for rotation interpolation "
                     "(Provides more stable rotation but has a slight performance cost)"),
        default=False,
        options=set(),
        update=output_use_logarithmic_map_update_handler
        )

    def update(self) -> None:
        poses = self.rbf_driver.poses
        output_influence_idprop_ensure(self)
        output_pose_data_idprops_update(self)
        output_idprops_update(self, len(poses))
        output_drivers_update(self, poses)

#endregion Output

#region Outputs
###################################################################################################

class RBFDriverOutputs(Identifiable, PropertyGroup):

    active_index: IntProperty(
        name="Index",
        description="Index of the active pose",
        min=0,
        default=0,
        options=set(),
        )

    @property
    def active(self) -> Optional[RBFDriverOutput]:
        index = self.active_index
        return self[index] if index < len(self) else None

    collection__internal__: CollectionProperty(
        type=RBFDriverOutput,
        options={'HIDDEN'}
        )

    def __len__(self) -> int:
        return len(self.collection__internal__)

    def __getitem__(self, key: Union[str, int, slice]) -> Union[RBFDriverOutput, List[RBFDriverOutput]]:
        return self.collection__internal__[key]

    def __contains__(self, name: str) -> bool:
        return name in self.collection__internal__

    def __iter__(self) -> Iterator[RBFDriverOutput]:
        return iter(self.collection__internal__)

    def find(self, name: str) -> int:
        return self.collection__internal__.find(name)

    def get(self, name: str, default: Optional[object]=None) -> Any:
        return self.collection__internal__.get(name, default)

    def keys(self) -> List[str]:
        return self.collection__internal__.keys()

    def items(self) -> List[Tuple[str, RBFDriverOutput]]:
        return self.collection__internal__.items()

    def search(self, identifier: str) -> Optional[RBFDriverOutput]:
        return next((output for output in self if output.identifier == identifier), None)

    def values(self) -> List[RBFDriverOutput]:
        return list(self)

#endregion Outputs

#endregion Data Layer

#region Service Layer
###################################################################################################

#region Service Layer > Symmetry
###################################################################################################

def output_symmetry_target(output: RBFDriverOutput) -> Optional[RBFDriverOutput]:
    """
    """
    if DEBUG:
        assert isinstance(output, RBFDriverOutput)
        assert output.has_symmetry_target

    driver = output.rbf_driver
    if not driver.has_symmetry_target:
        log.warning(f'Symmetry target defined for component {output} but not for {driver}')
        return

    m_driver = driver.id_data.rbf_drivers.search(driver.symmetry_identifier)
    if m_driver is None:
        log.warning(f'Search failed for symmetry target of {driver}.')
        return

    return m_driver.outputs.search(output.symmetry_identifier)


def output_channel_symmetry_target(channel: RBFDriverOutputChannel) -> Optional[RBFDriverOutputChannel]:
    """
    """
    if DEBUG:
        assert isinstance(channel, RBFDriverOutputChannel)
        assert channel.has_symmetry_target

    output = channel.output
    if not output.has_symmetry_target:
        log.warning((f'Symmetry target defined for sub-component {channel} but not for '
                     f'parent component {output}'))
        return

    m_output = output_symmetry_target(output)
    if m_output is None:
        log.warning(f'Search failed for symmetry target of {output}.')
        return

    return m_output.channels.search(channel.symmetry_identifier)


def output_symmetry_assign(a: RBFDriverOutput, b: RBFDriverOutput) -> None:
    """
    """
    if DEBUG:
        assert isinstance(a, RBFDriverOutput)
        assert isinstance(b, RBFDriverOutput)
        assert a.rbf_driver != b.rbf_driver

    a['symmetry_identifier'] = b.identifier
    b['symmetry_identifier'] = a.identifier

    if len(a.channels) != len(b.channels):
        log.warning(f'Assigning symmetry across outputs {a} and {b} with unequal channel counts')

    for a, b in zip(a.channels, b.channels):
        output_channel_symmetry_assign(a, b)


def output_mirror_property(output: RBFDriverOutput, propname: str) -> None:
    """
    """
    if DEBUG:
        assert isinstance(output, RBFDriverOutput)
        assert isinstance(propname, str)
        assert hasattr(output, propname)

    if not output.has_symmetry_target:
        return

    driver = output.rbf_driver

    if not driver.has_symmetry_target:
        log.warning(f'Symmetry target defined for component {output} but not for {driver}')
        return

    if driver.symmetry_lock__internal__:
        return

    m_driver = driver.id_data.rbf_drivers.search(driver.symmetry_identifier)
    if m_driver is None:
        log.warning(f'Search failed for symmetry target of {driver}.')
        return

    m_output = driver.outputs.search(output.symmetry_identifier)
    if m_output is None:
        log.warning(f'Search failed for symmetry target of {output}.')
        return

    log.info(f'Mirroring {output} property {propname}')
    m_driver.symmetry_lock__internal__ = True

    try:
        setattr(m_output, propname, getattr(output, propname))
    finally:
        m_driver.symmetry_lock__internal__ = False


def output_channel_mirror_property(channel: RBFDriverOutputChannel, propname: str, value: Optional[Any]=None) -> None:
    """
    """
    if DEBUG:
        assert isinstance(channel, RBFDriverOutputChannel)
        assert isinstance(propname, str)
        assert hasattr(channel, propname)

    if not channel.has_symmetry_target:
        return

    output = channel.output

    if not output.has_symmetry_target:
        log.warning(f'Symmetry target defined for component {channel} but not for {output}')
        return

    driver = output.rbf_driver

    if not driver.has_symmetry_target:
        log.warning(f'Symmetry target defined for component {output} but not for {driver}')
        return

    if driver.symmetry_lock__internal__:
        return

    m_driver = driver.id_data.rbf_drivers.search(driver.symmetry_identifier)
    if m_driver is None:
        log.warning(f'Search failed for symmetry target of {driver}.')
        return

    m_output = driver.outputs.search(output.symmetry_identifier)
    if m_output is None:
        log.warning(f'Search failed for symmetry target of {output}.')
        return

    m_channel = m_output.variables.search(channel.symmetry_identifier)
    if m_channel is None:
        log.warning((f'Search failed for symmetry target of {channel}.'))
        return

    log.info(f'Mirroring {channel} property {propname}')
    m_driver.symmetry_lock__internal__ = True

    try:
        setattr(m_channel, propname, getattr(channel, propname) if value is None else value)
    finally:
        m_driver.symmetry_lock__internal__ = False


def output_channel_symmetry_assign(a: RBFDriverOutputChannel, b: RBFDriverOutputChannel) -> None:
    """
    """
    if DEBUG:
        assert isinstance(a, RBFDriverOutputChannel)
        assert isinstance(b, RBFDriverOutputChannel)
        assert a.output.rbf_driver != b.output.rbf_driver

    a['symmetry_identifier'] = b.identifier
    b['symmetry_identifier'] = a.identifier

#endregion Service Layer > Symmetry

def output_foreach_channel_update_property(output: 'RBFDriverOutput', key: str, value: Any) -> None:
    for channel in output.channels:
        channel[key] = value


def output_foreach_channel_update_datapath(output: 'RBFDriverOutput') -> None:
    type = output.type

    if type in {'LOCATION', 'ROTATION', 'SCALE'}:
        propname = f'rotation_{output.rotation_mode.lower()}' if type == 'ROTATION' else type.lower()
        for channel in output.channels:
            if channel.object is not None and channel.object.type == 'ARMATURE' and channel.bone_target:
                channel["data_path"] = f'pose.bones["{channel.bone_target}"].{propname}'
            else:
                channel["data_path"] = propname

    elif type == 'BBONE':
        for channel in output.channels:
            channel["data_path"] = f'pose.bones["{channel.bone_target}"].{channel.name}'

    elif type == 'SHAPE_KEY':
        for channel in output.channels:
            channel["data_path"] = f'key_blocks["{channel.name}"].value'


def output_channel_target_rotation_mode(channel: 'RBFDriverOutputChannel', output: Optional['RBFDriverOutput']=None) -> str:
    output = output or channel.output
    target = channel.object__internal__
    result = output.rotation_mode
    if target is not None:
        if target.type == 'ARMATURE' and channel.bone_target:
            target = target.pose.bones.get(channel.bone_target)
        if target is not None:
            result = 'EULER' if len(target.rotation_mode) < 5 else target.rotation_mode
    return result


def output_influence_idprop_create(output: RBFDriverOutput) -> None:
    rna_prop_ui.rna_idprop_ui_create(output.id_data.data, output.influence_property_name,
                                     default=1.0,
                                     min=0.0,
                                     max=1.0,
                                     soft_min=0.0,
                                     soft_max=1.0,
                                     description="RBF driver input influence")


def output_influence_idprop_ensure(output: RBFDriverOutput) -> None:
    if not isinstance(output.id_data.data.get(output.influence_property_name), float):
        output_influence_idprop_create(output)


def output_influence_idprop_remove(output: RBFDriverOutput) -> None:
    try:
        del output.id_data.data[output.influence_property_name]
    except KeyError: pass


def output_influence_idprop_remove_all(outputs: RBFDriverOutputs) -> None:
    for output in outputs:
        output_influence_idprop_remove(output)


def output_logmap_idprops_ensure(output: RBFDriverOutput) -> None:
    id = output.id_data.data
    id[output.logmap_property_name] = [0.0] * 4
    id[output.logmap_magnitude_property_name] = 0.0


def output_logmap_idprops_remove(output: RBFDriverOutput) -> None:
    id = output.id_data.data
    try:
        del id[output.logmap_property_name]
    except KeyError: pass
    try:
        del id[output.logmap_magnitude_property_name]
    except KeyError: pass


def output_pose_data_idprops_update(output: RBFDriverOutput) -> None:
    channels = output.channels
    posedata = [tuple(scalar.value for scalar in channel.data) for channel in channels]

    if output_uses_logmap(output):
        posedata = np.array(posedata, dtype=np.float)
        for pose in posedata.T:
            pose[:] = quaternion_to_logarithmic_map(pose)

    for channel, data in zip(channels, posedata):
        channel.id_data.data[channel.pose_data_property_name] = data


def output_pose_data_idprops_remove(output: RBFDriverOutput) -> None:
    for channel in output.channels:
        try:
            del channel.id_data.data[channel.pose_data_property_name]
        except KeyError: pass


def output_driver_update_magnitude(output: RBFDriverOutput) -> None:

    fcurve = driver_ensure(output.id_data.data, output.logmap_magnitude_property_path)
    driver = fcurve.driver
    driver.type = 'SCRIPTED'
    # driver.expression = f'sqrt(w*w+x*x+y*y+z*z)'
    driver.expression = f'sqrt(x*x+y*y+z*z)'
    driver_variables_clear(driver.variables)

    for index, axis in enumerate("wxyz"):
        variable = driver.variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = axis

        target = variable.targets[0]
        target.id_type = output.id_data.type
        target.id = output.id_data.data
        target.data_path = f'{output.logmap_property_path}[{index}]'


def output_channel_driver_update_exp(output: RBFDriverOutput, channel: RBFDriverOutputChannel) -> None:

    fcurve = driver_ensure(channel.object, channel.data_path, channel.array_index)
    fcurve.mute = channel.mute
    driver = fcurve.driver
    driver.type = 'SCRIPTED'
    driver_variables_clear(driver.variables)

    magnitude = driver.variables.new()
    magnitude.type = 'SINGLE_PROP'
    magnitude.name = "magnitude"

    target = magnitude.targets[0]
    target.id_type = output.id_data.type
    target.id = output.id_data.data
    target.data_path = output.logmap_magnitude_property_path
    
    w = driver.variables.new()
    w.type = 'SINGLE_PROP'
    w.name = "w"
    
    target = w.targets[0]
    target.id_type = output.id_data.type
    target.id = output.id_data.data
    target.data_path = f'{output.logmap_property_path}[0]'

    if channel.array_index == 0:
        driver.expression = f'exp(w)*cos(magnitude) if magnitude > 1.0000000000000002e-14 else exp(w)'
    else:
        axis = "wxyz"[channel.array_index]

        component = driver.variables.new()
        component.type = 'SINGLE_PROP'
        component.name = axis
        
        target = component.targets[0]
        target.id_type = output.id_data.type
        target.id = output.id_data.data
        target.data_path = f'{output.logmap_property_path}[{channel.array_index}]'

        driver.expression = f'exp(w)*(sin(magnitude)/magnitude)*{axis} if magnitude > 1.0000000000000002e-14 else 0.0'


def output_channel_driver_update_dot(output: RBFDriverOutput,
                                     channel: RBFDriverOutputChannel,
                                     poses: RBFDriverPoses,
                                     driven_property: Union[Tuple[ID, str], Tuple[ID, str, int]],
                                     data_range: Optional[Tuple[int, ...]]=None) -> None:

    fcurve = driver_ensure(*driven_property)
    fcurve.mute = channel.mute
    driver = fcurve.driver
    varkey = DriverVariableNameGenerator()
    tokens = []
    driver_variables_clear(driver.variables)

    for pose_index in (range(*data_range) if data_range is not None else range(len(channel.data))):

        parameter = driver.variables.new()
        parameter.type = 'SINGLE_PROP'
        parameter.name = next(varkey)

        target = parameter.targets[0]
        target.id_type = channel.id_data.type
        target.id = channel.id_data.data
        target.data_path = f'{channel.pose_data_property_path}[{pose_index}]'

        weight = driver.variables.new()
        weight.type = 'SINGLE_PROP'
        weight.name = next(varkey)

        target = weight.targets[0]
        target.id_type = poses.id_data.type
        target.id = poses.id_data.data
        target.data_path = f'{poses.normalized_weight_property_path}[{pose_index}]'

        influence = driver.variables.new()
        influence.type = 'SINGLE_PROP'
        influence.name = next(varkey)

        target = influence.targets[0]
        target.id_type = output.id_data.type
        target.id = output.id_data.data
        target.data_path = output.influence_property_path

        tokens.append(f'{parameter.name}*{weight.name}*{influence.name}')

    driver.type = 'SCRIPTED'
    driver.expression = "+".join(tokens)


def output_idprops_update(output: RBFDriverOutput, pose_count: int) -> None:
    output_influence_idprop_ensure(output)

    if output_uses_logmap(output):
        output_logmap_idprops_ensure(output)
    else:
        output_logmap_idprops_remove(output)

    for channel in output.channels:

        if not channel.enabled:
            channel.ranges__internal__.clear()
            try:
                del channel.id_data.data[channel.driven_property_name]
            except KeyError: pass
        else:
            offset = 0
            ranges = channel.ranges__internal__
            ranges.clear()

            for _ in range(floor(pose_count/MAX_PARAMS)):
                ranges.add().__init__(offset, offset + MAX_PARAMS)
                offset += MAX_PARAMS

            if offset < pose_count:
                ranges.add().__init__(offset, pose_count)

            if len(ranges):
                channel.id_data.data[channel.driven_property_name] = [0.0] * len(ranges)
            else:
                try:
                    del channel.id_data.data[channel.driven_property_name]
                except KeyError: pass


def output_uses_logmap(output: RBFDriverOutput) -> bool:
    return (output.type == 'ROTATION'
            and output.rotation_mode == 'QUATERNION'
            and output.use_logarithmic_map)


def output_pose_data_append(output: RBFDriverOutput) -> None:
    """
    """
    for channel in output.channels:
        channel.data.data__internal__.add()["value"] = channel.value


def output_pose_data_update(output: RBFDriverOutput, pose_index: int) -> None:
    for channel in output.channels:
        channel.data[pose_index]["value"] = channel.value
    output_pose_data_idprops_update(output)


def output_pose_data_remove(output: RBFDriverOutput, pose_index: int) -> None:
    """
    """
    for channel in output.channels:
        # bpy_prop_collection.remove() does not raise exceptions if index is out of bounds.
        channel.data.data__internal__.remove(pose_index)
    output_pose_data_idprops_update(output)


def output_rotdata_update(output: 'RBFDriverOutput', from_mode: str, to_mode: str) -> None:
    convert = ROTATION_CONVERSION_LUT[from_mode][to_mode]

    matrix = np.array([
        tuple(scalar.value for scalar in channel.data) for channel in output.channels
        ], dtype=np.float)

    for vector, column in zip(matrix.T if from_mode != 'EULER' else matrix[1:].T,
                              matrix.T if to_mode   != 'EULER' else matrix[1:].T):
        column[:] = convert(vector)

    if to_mode == 'EULER':
        matrix[0] = 0.0

    for channel, data in zip(output.channels, matrix):
        channel.data.__init__(data)


def output_drivers_update(output: RBFDriverOutput, poses: RBFDriverPoses) -> None:
    
    channels = output.channels
    pose_count = len(poses)

    if output_uses_logmap(output):
        output_driver_update_magnitude(output)
        root = output.id_data.data
        path = output.logmap_magnitude_property_path
        driven_properties = [(root, path, i) for i in range(4)]
    else:
        type = output.type
        driven_properties = []

        for channel in channels:
            id = channel.id

            if type == 'NONE':
                path, index = data_path_split(channel.data_path)
            else:
                path = channel.data_path
                index = channel.array_index if type in {'LOCATION', 'ROTATION', 'SCALE'} else -1
            
            if index >= 0:
                driven_properties.append((id, path, index))
            else:
                driven_properties.append((id, path))

    for channel, driven_property in zip(channels, driven_properties):

        if not channel.enabled or not channel.is_valid:
            continue

        ranges = channel.ranges__internal__

        if len(ranges):
            type = channel.id_data.type
            root = channel.id_data.data
            path = channel.driven_property_path
            
            fcurve = driver_ensure(*driven_property)
            driver = fcurve.driver
            driver.type = 'SUM'
            driver_variables_clear(driver.variables)
            
            for index, item in enumerate(ranges):
                output_channel_driver_update_dot(output, channel, poses,
                                                 (root, path, index), (item.start, item.stop))

                variable = driver.variables.new()
                variable.type = 'SINGLE_PROP'
                variable.name = f'var_{str(index).zfill(3)}'

                target = variable.targets[0]
                target.id_type = type
                target.id = root
                target.data_path = f'{path}[{index}]'

        else:
            output_channel_driver_update_dot(output, channel, poses,
                                             driven_property, (0, pose_count))

    if output_uses_logmap(output):
        for channel in channels:
            if channel.is_valid:
                output_channel_driver_update_exp(output, channel)


def output_idprops_remove(output: RBFDriverOutput) -> None:
    output_influence_idprop_remove(output)
    output_pose_data_idprops_remove(output)

    if output_uses_logmap(output):
        output_logmap_idprops_remove(output)

    for channel in output.channels:
        try:
            del channel.id_data.data[channel.driven_property_name]
        except KeyError: pass


def output_drivers_remove(output: RBFDriverOutput) -> None:

    root = output.id_data.data
    type = output.type

    driver_remove(root, output.logmap_magnitude_property_path)

    for index in range(4):
        driver_remove(root, output.logmap_property_path, index)

    for channel in output.channels:
        id = channel.id
        if id:
            if type == 'NONE':
                path, index = data_path_split(channel.data_path)
            else:
                path = channel.data_path
                index = channel.array_index if type in {'LOCATION', 'ROTATION', 'SCALE'} else -1

            if index >= 0:
                driver_remove(id, path, index)
            else:
                driver_remove(id, path)

            for index in range(len(channel.ranges__internal__)):
                driver_remove(root, channel.driven_property_path, index)

#endregion Service Layer