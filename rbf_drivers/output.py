
from functools import partial
from re import L
from typing import Any, Iterator, List, Optional, Tuple, Union, TYPE_CHECKING
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

import rna_prop_ui
import numpy as np
from .lib.driver_utils import DriverVariableNameGenerator, driver_ensure, driver_find, driver_remove, driver_variables_clear
from .lib.rotation_utils import axis_angle_to_euler, axis_angle_to_quaternion, euler_to_axis_angle, euler_to_quaternion, noop, quaternion_to_axis_angle, quaternion_to_euler, quaternion_to_logarithmic_map
from .pose import RBFDriverPoses
from .posedata import RBFDriverPoseDataVector
from .mixins import ID_TYPE_ITEMS, LAYER_TYPE_ITEMS, Identifiable
from rbf_drivers.lib import rotation_utils

if TYPE_CHECKING:
    from .driver import RBFDriver

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
            "array_index": 4
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
            "name": "bbone_curveiny",
            "default": 0.0,
            "data_path": 'pose.bones[""].bbone_curveiny',
        },{
            "name": "bbone_curveoutz",
            "default": 0.0,
            "data_path": 'pose.bones[""].bbone_curveoutz',
        },{
            "name": "bbone_curveoutx",
            "default": 0.0,
            "data_path": 'pose.bones[""].bbone_curveoutx',
        },{
            "name": "bbone_curveouty",
            "default": 0.0,
            "data_path": 'pose.bones[""].bbone_curveouty',
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
            "default": 0.0,
            "data_path": f'pose.bones[""].bbone_{"scaleinx" if version[0] < 3 else "scalein[0]"}',
        },{
            "name": "bbone_scaleiny",
            "default": 0.0,
            "data_path": f'pose.bones[""].bbone_{"scaleiny" if version[0] < 3 else "scalein[1]"}',
        },{
            "name": "bbone_scaleinz",
            "default": 0.0,
            "data_path": f'pose.bones[""].bbone_{"scaleinz" if version[0] < 3 else "scalein[2]"}',
        },{
            "name": "bbone_scaleoutx",
            "default": 0.0,
            "data_path": f'pose.bones[""].bbone_{"scaleoutx" if version[0] < 3 else "scaleout[0]"}',
        },{
            "name": "bbone_scaleouty",
            "default": 0.0,
            "data_path": f'pose.bones[""].bbone_{"scaleoutx" if version[0] < 3 else "scaleout[1]"}',
        },{
            "name": "bbone_scaleoutz",
            "default": 0.0,
            "data_path": f'pose.bones[""].bbone_{"scaleoutx" if version[0] < 3 else "scaleout[2]"}',
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


def output_channel_bone_target_get(channel: 'RBFDriverOutputChannel') -> str:
    return channel.get("boen_target", "")


def output_channel_bone_target_set(channel: 'RBFDriverOutputChannel', value: str) -> None:
    cache = output_channel_bone_target_get(channel)
    if cache != value:
        channel["bone_target"] = value

        output = channel.output
        if output.type in ('LOCATION', 'ROTATION', 'SCALE'):

            if output.type == 'ROTATION':
                prop = f'rotation_{output.rotation_mode.lower()}'
            else:
                prop = output.type.lower()

            for channel in output.channels:
                channel["bone_target"] = value

                if (value
                    and channel.object is not None
                    and channel.object.type == 'ARMATURE'
                    ):
                    output_channel_data_path_update(channel, f'pose.bones["{value}"].{prop}')
                else:
                    output_channel_data_path_update(channel, prop)

        elif output.type == 'BBONE':
            pass


def output_channel_data_path_get(channel: 'RBFDriverOutputChannel') -> str:
    return channel.get("data_path", "")


def output_channel_data_path_set(channel: 'RBFDriverOutputChannel', value: str) -> None:
    output = channel.output
    if output.type != 'NONE':
        raise RuntimeError((f'{channel.__class__.__name__}.data_path '
                            f'is not user-editable for this output type'))
    else:
        output_channel_data_path_update(channel, value)


def output_channel_data_path_update(channel: 'RBFDriverOutputChannel', value: str) -> None:
    cache = output_channel_data_path_get(channel)
    valid = channel.is_valid
    if cache != value:
        channel["data_path"] = value
        if channel.enabled:
            if valid:
                if channel.is_valid:
                    animdata = channel.id.animation_data
                    if animdata:
                        for fcurve in animdata.drivers:
                            if fcurve.data_path == cache:
                                fcurve.data_path = value
                elif channel.is_property_set("array_index"):
                    driver_remove(channel.id, cache, channel.array_index)
                else:
                    driver_remove(channel.id, cache)
            elif channel.is_valid:
                output = channel.output
                output_drivers_update(output, output.rbf_driver.poses)


def output_channel_enabled_update_handler(channel: 'RBFDriverOutputChannel', _) -> None:
    output = channel.output
    output_drivers_update(output, output.rbf_driver.poses)


def output_channel_mute_update_handler(channel: 'RBFDriverOutputChannel', _) -> None:
    if channel.enabled:
        id = channel.id
        if id:
            if channel.is_property_set("array_index"):
                fcurve = driver_find(id, channel.data_path, channel.array_index)
            else:
                fcurve = driver_find(id, channel.data_path)
            if fcurve:
                fcurve.mute = channel.mute


def output_channel_object_update_handler(channel: 'RBFDriverOutputChannel', _) -> None:
    cache = channel.object__internal__
    value = channel.object

    if cache != value:
        prev_id = channel.id
        prev_valid = prev_id is not None and channel.is_valid

        channel.object__internal__ = value

        curr_id = channel.id
        curr_valid = curr_id is not None and channel.is_valid
        
        output = channel.output
        if output.type != 'NONE':
            for other in output.channels:
                if other != channel:
                    other.object__internal__ = value
                    other.object = value

        if prev_valid and curr_valid:
            for channel in output.channels:
                if channel.enabled:
                    if channel.is_property_set("array_index"):
                        fcurve = driver_find(prev_id, channel.data_path, channel.array_index)
                    else:
                        fcurve = driver_find(prev_id, channel.data_path)
                    if fcurve:
                        curr_id.animation_data_create().drivers.from_existing(src_driver=fcurve)
                        fcurve.id_data.animation_data.drivers.remove(fcurve)
        elif prev_valid:
            for channel in output.channels:
                if channel.enabled:
                    if channel.is_property_set("array_index"):
                        driver_remove(prev_id, channel.data_path, channel.array_index)
                    else:
                        driver_remove(prev_id, channel.data_path)
        elif curr_valid:
            output_drivers_update(output, output.rbf_driver.poses)


            



class RBFDriverOutputChannel(Identifiable, PropertyGroup):

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
        update=lambda self, _: self.update("id_type"),
        )

    @property
    def id(self) -> Optional[ID]:
        object = self.object__internal__
        if object is None or self.id_type == 'OBJECT': return object
        if object.type == self.id_type: return object.data

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


def output_mute_get(output: 'RBFDriverOutput') -> bool:
    return all(channel.mute for channel in output.channels)


def output_mute_set(output: 'RBFDriverOutput', value: bool) -> None:
    for channel in output.channels:
        channel.mute = value


def output_use_logarithmic_map_update_handler(output: 'RBFDriverOutput', _) -> None:
    if output.type == 'ROTATION' and output.rotation_mode == 'QUATERNION':
        output_drivers_update(output, output.rbf_driver.poses)


def output_rotation_mode_get(output: 'RBFDriverOutput') -> int:
    return output.get("rotation_mode", 0)


def output_rotation_mode_set(output: 'RBFDriverOutput', value: int) -> None:
    cache = output_rotation_mode_get(output)
    if cache == value:
        return

    output["rotation_mode"] = value
    if output.type != 'ROTATION':
        return

    prevmode = OUTPUT_ROTATION_MODE_INDEX[cache]
    currmode = OUTPUT_ROTATION_MODE_INDEX[value]
    convert = ROTATION_CONVERSION_LUT[prevmode][currmode]

    matrix = np.array([
        tuple(scalar.value for scalar in variable.data) for variable in input.variables
        ], dtype=np.float)

    for vector, column in zip(matrix.T if prevmode != 'EULER' else matrix[1:].T,
                              matrix.T if currmode != 'EULER' else matrix[1:].T):
        column[:] = convert(vector)

    if currmode == 'EULER':
        matrix[0] = 0.0

    for channel, data in zip(output.channels, matrix):
        channel.data.__init__(data)

    output.update()

class RBFDriverOutput(Identifiable, PropertyGroup):

    def update(self, context: Optional[Any]=None) -> None:
        poses = self.rbf_driver.poses
        output_pose_data_idprops_update(self)
        output_idprops_update(self, len(poses))
        output_drivers_update(self, self.rbf_driver.poses)

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
        update=lambda self, _: self.update("name")
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
    def rbf_driver(self) -> 'RBFDriver':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".outputs.")[0])

    rotation_mode: EnumProperty(
        items=OUTPUT_ROTATION_MODE_ITEMS,
        default='EULER',
        options=set(),
        update=lambda self, _: self.update("rotation_mode")
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

    def values(self) -> List[RBFDriverOutput]:
        return list(self)


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

    if (output.type == 'ROTATION'
            and output.rotation_mode == 'QUATERNION'
            and output.use_logarithmic_map):

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
        target.data_path = f'{poses.weight_property_path}[{pose_index}]'

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


def output_drivers_update(output: RBFDriverOutput, poses: RBFDriverPoses) -> None:
    
    channels = output.channels
    pose_count = len(poses)

    if output_uses_logmap(output):
        output_driver_update_magnitude(output)
        root = output.id_data.data
        path = output.logmap_magnitude_property_path
        driven_properties = [(root, path, i) for i in range(4)]
    else:
        driven_properties = [(ch.id, ch.data_path, ch.array_index) for ch in channels]

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
    driver_remove(output.id_data.data, output.logmap_magnitude_property_path)
    for index in range(4):
        driver_remove(output.id_data.data, output.logmap_property_path, index)
    for channel in output.channels:
        id = channel.id
        if id:
            if channel.is_property_set("array_index"):
                driver_remove(id, channel.data_path, channel.array_index)
            else:
                driver_remove(id, channel.data_path)
            for index in range(len(channel.ranges)):
                driver_remove(channel.id_data.data, channel.driven_property_path, index)

