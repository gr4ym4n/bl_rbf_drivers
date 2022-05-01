
from itertools import repeat
from math import floor
from typing import Iterable, List, Optional, Sequence, Tuple, TYPE_CHECKING, Union
from mathutils import Quaternion
import numpy as np
from .events import event_handler
from .utils import driver_variables_ensure, idprop_remove, owner_resolve
from ..lib.rotation_utils import quaternion_to_logarithmic_map
from ..lib.driver_utils import (driver_ensure,
                                driver_find,
                                driver_remove,
                                driver_variables_clear,
                                DriverVariableNameGenerator)
from ..api.pose import PoseUpdateEvent
from ..api.poses import PoseNewEvent, PoseRemovedEvent
from ..api.output_channel import (OutputChannelMuteUpdateEvent,
                                  OutputChannelNameChangeEvent,
                                  output_channel_is_enabled)
from ..api.output import (OutputBoneTargetChangeEvent,
                          OutputDataPathChangeEvent,
                          OutputIDTypeUpdateEvent,
                          OutputObjectChangeEvent,
                          OutputRotationModeChangeEvent,
                          OutputUseAxisUpdateEvent,
                          OutputUseLogarithmicMapUpdateEvent)
if TYPE_CHECKING:
    from bpy.types import FCurve, Object
    from ..api.output_channel import RBFDriverOutputChannel
    from ..api.output_channels import RBFDriverOutputChannels
    from ..api.output import RBFDriverOutput
    from ..api.driver import RBFDriver

EPSILON = 10 * np.finfo(float).resolution
MAX_PARAMS = 32


def output_assign_channel_data_targets__singleprop(output: 'RBFDriverOutput') -> None:
    path = output.data_path
    channel = output.channels[0]

    if path.endswith(']'):
        index = path.rfind("[")
        if index != -1:
            token = path[index+1:-1]
            if token.isdigit():
                channel["data_path"] = path[:index]
                channel["array_index"] = int(token)
                return
    
    channel["data_path"] = path
    channel.property_unset("array_index")


def output_assign_channel_data_targets__shapekey(output: 'RBFDriverOutput') -> None:
    channel = output.channels[0]
    channel["data_path"] = f'key_blocks["{channel.name}"].value'
    channel.property_unset("array_index")


def output_assign_channel_data_targets__transforms(output: 'RBFDriverOutput') -> None:
    if output.type == 'ROTATION':
        suffix = f'rotation_{output.rotation_mode.lower()}'
        offset = -int(output.rotation_mode == 'EULER')
    else:
        suffix = output.type.lower()
        offset = 0

    prefix = ""
    object = output.object
    if object is not None and object.type == 'ARMATURE' and output.bone_target:
        prefix = f'pose.bones["{output.bone_target}"].'

    for index, channel in enumerate(output.channels):
        index += offset
        channel["data_path"] = f'{prefix}{suffix}'

        if index >= 0:
            channel["array_index"] = index
        else:
            channel.property_unset("array_index")


def output_assign_channel_data_targets(output: 'RBFDriverOutput') -> None:
    type = output.type
    if type == 'SHAPE_KEY':
        output_assign_channel_data_targets__shapekey(output)
    elif type == 'SINGLE_PROP':
        output_assign_channel_data_targets__singleprop(output)
    elif type in {'LOCATION', 'ROTATION', 'SCALE'}:
        output_assign_channel_data_targets__transforms(output)


def output_channel_data_target(channel: 'RBFDriverOutputChannel') -> Union[Tuple[str], Tuple[str, int]]:
    if channel.is_property_set("array_index"):
        return (channel.data_path, channel.array_index)
    return (channel.data_path,)


def idprop_cdata(channel: 'RBFDriverOutputChannel') -> str:
    return f'rbfn_cdata_{channel.identifier}'


def idprop_cnode(channel: 'RBFDriverOutputChannel') -> str:
    return f'rbfn_cnode_{channel.identifier}'


def idprop_qlend_magnitude(output: 'RBFDriverOutput') -> str:
    return f'rbfn_qbmag_{output.identifier}'


def idprop_qblend_logsum(output: 'RBFDriverOutput') -> str:
    return f'rbfn_qbsum_{output.identifier}'


def idprop_qlend_sine(output: 'RBFDriverOutput') -> str:
    return f'rbfn_qbsin_{output.identifier}'


def idprop_qlend_exponent(output: 'RBFDriverOutput') -> str:
    return f'rbfn_qbexp_{output.identifier}'


def idprop_qlend_exponential_map(output: 'RBFDriverOutput') -> str:
    return f'rbfn_qbmap_{output.identifier}'


def output_driver_init__qblend_magnitude(fcurve: 'FCurve',
                                         object: 'Object',
                                         tokens: Sequence[str]) -> None:
    driver = fcurve.driver
    driver.type = 'SCRIPTED'
    driver.expression = f'sqrt(pow(x, 2.0) + pow(y, 2.0) + pow(z, 2.0))'

    for variable, axis, path in zip(driver_variables_ensure(driver.variables, 3), "xyz", tokens[1:]):
        variable.type = 'SINGLE_PROP'
        variable.name = axis

        target = variable.targets[0]
        target.id_type = object.type
        target.id = object.data
        target.data_path = path


def output_driver_init__qblend_sine(fcurve: 'FCurve',
                                    object: 'Object',
                                    magnitude: str) -> None:
    driver = fcurve.driver
    driver.type = 'SCRIPTED'
    driver.expression = f'sin(n) / n if n != 0.0 else sin(n)'

    variable = driver_variables_ensure(driver.variables, 1)[0]
    variable.type = 'SINGLE_PROP'
    variable.name = "n"

    target = variable.targets[0]
    target.id_type = object.type
    target.id = object.data
    target.data_path = magnitude


def output_driver_init__qblend_exponent(fcurve: 'FCurve',
                                        object: 'Object',
                                        tokens: Sequence[str]) -> None:
    driver = fcurve.driver
    driver.type = 'SCRIPTED'
    driver.expression = f'exp(w)'

    variable = driver_variables_ensure(driver.variables, 1)[0]
    variable.type = 'SINGLE_PROP'
    variable.name = "w"

    target = variable.targets[0]
    target.id_type = object.type
    target.id = object.data
    target.data_path = tokens[0]


def output_channel_driver_init__qblend_exponential_map(fcurve: 'FCurve',
                          object: 'Object',
                          logsum: Sequence[str],
                          magnitude: str,
                          sine: str,
                          exponent: str) -> None:
    driver = fcurve.driver
    driver.type = 'SCRIPTED'

    variables = driver.variables
    driver_variables_clear(variables)

    for name, path in zip("se", (sine, exponent)):
        variable = variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = name

        target = variable.targets[0]
        target.id_type = object.type
        target.id = object.data
        target.data_path = path

    if fcurve.array_index == 0:
        variable = variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = "n"

        target = variable.targets[0]
        target.id_type = object.type
        target.id = object.data
        target.data_path = magnitude

        driver.expression = f'e * cos(n) if n > {EPSILON} else e'
    else:
        variable = variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = "q"

        target = variable.targets[0]
        target.id_type = object.type
        target.id = object.data
        target.data_path = logsum[fcurve.array_index]

        driver.expression = f'e * s * q'


def output_channel_driver_init__qblend_final(fcurve: 'FCurve',
                          object: 'Object',
                          mean: Sequence[float],
                          expmap: Sequence[str]) -> None:
    
    driver = fcurve.driver
    driver.type = 'SCRIPTED'

    for variable, key, path in zip(driver_variables_ensure(driver.variables, 4), "wxyz", expmap):
        variable.type = 'SINGLE_PROP'
        variable.name = key

        target = variable.targets[0]
        target.id_type = object.type
        target.id = object.data
        target.data_path = path

    i = fcurve.array_index
    w, x, y, z = mean

    if   i == 0: driver.expression = f'{w}*w - {x}*x - {y}*y - {z}*z'
    elif i == 1: driver.expression = f'{w}*x + {x}*w + {y}*z - {z}*y'
    elif i == 2: driver.expression = f'{w}*y - {x}*z + {y}*w + {z}*x'
    elif i == 3: driver.expression = f'{w}*z + {x}*y - {y}*x + {z}*w'


def output_channel_driver_init__dot(fcurve: 'FCurve',
                                    object: 'Object',
                                    weights: Sequence[str],
                                    samples: Sequence[str],
                                    influence: Optional[str]="") -> None:

    keygen = DriverVariableNameGenerator()
    tokens = []
    driver = fcurve.driver
    driver.type = 'SCRIPTED'

    variables = driver.variables
    driver_variables_clear(variables)

    for weight, sample in zip(weights, samples):

        weight_variable = variables.new()
        weight_variable.type = 'SINGLE_PROP'
        weight_variable.name = next(keygen)

        target = weight_variable.targets[0]
        target.id_type = object.type
        target.id = object.data
        target.data_path = weight

        sample_variable = variables.new()
        sample_variable.type = 'SINGLE_PROP'
        sample_variable.name = next(keygen)

        target = sample_variable.targets[0]
        target.id_type = object.type
        target.id = object.data
        target.data_path = sample

        tokens.append(f'{weight_variable.name}*{sample_variable.name}')

    driver.type = 'SCRIPTED'
    driver.expression = "+".join(tokens)

    if influence:
        influence_variable = variables.new()
        influence_variable.type = 'SINGLE_PROP'
        influence_variable.name = next(keygen)

        target = influence_variable.targets[0]
        target.id_type = object.type
        target.id = object.data
        target.data_path = influence

        driver.expression = f'{influence_variable.name}*({driver.expression})'


def output_channel_driver_init__sum(fcurve: 'FCurve',
                                    object: 'Object',
                                    params: Sequence[str],
                                    influence: Optional[str]="") -> None:
    
    keygen = DriverVariableNameGenerator()
    driver = fcurve.driver
    driver.type = 'SUM'

    variables = driver.variables
    driver_variables_clear(variables)

    for param in params:
        variable = variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = next(keygen)

        target = variable.targets[0]
        target.id_type = object.type
        target.id = object.data
        target.data_path = param

    if influence:
        variable = variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = next(keygen)

        target = variable.targets[0]
        target.id_type = object.type
        target.id = object.data
        target.data_path = influence

        driver.type = 'SCRIPTED'
        driver.expression = f'{variable.name}*({"+".join(variables[:-1])})'


def output_channel_activate__weighted_average(output: 'RBFDriverOutput',
                                              channel: 'RBFDriverOutputChannel') -> None:
    object = output.id_data
    id = object.data
    propname = idprop_cdata(channel)
    id[propname] = list(channel.data.values())

    weights = [pose.weight for pose in owner_resolve(output, ".outputs").poses]
    weights = [f'{weight.data_path}[{weight.array_index}]' for weight in weights]
    samples = [f'["{propname}"][{index}]' for index in range(len(weights))]

    if len(samples) > MAX_PARAMS:
        length = len(samples)
        offset = 0
        blocks: List[Tuple[Sequence[str], Sequence[str]]] = []

        for _ in range(floor(length/MAX_PARAMS)):
            blocks.append((weights[offset: offset + MAX_PARAMS], samples[offset: offset + MAX_PARAMS]))
            offset += MAX_PARAMS

        if offset < length:
            blocks.append((weights[offset:], samples[offset:]))

        propname = idprop_cnode(channel)
        id[propname] = [0.0] * len(blocks)

        fcurves = []
        for index, (weights, samples) in enumerate(blocks):
            fcurve = driver_ensure(output.id_data.data, f'["{propname}"]', index)
            fcurves.append(fcurve)
            output_channel_driver_init__dot(fcurve, object, weights, samples)

        tokens = tuple(f'{fc.data_path}[{fc.array_index}]' for fc in fcurves)
        fcurve = driver_ensure(channel.id, *output_channel_data_target(channel))
        fcurve.mute = channel.mute
        output_channel_driver_init__sum(fcurve, object, tokens, output.influence.data_path)
    else:
        fcurve = driver_ensure(channel.id, *output_channel_data_target(channel))
        fcurve.mute = channel.mute
        output_channel_driver_init__dot(fcurve, object, weights, samples, output.influence.data_path)


def output_activate__weighted_average(output: 'RBFDriverOutput') -> None:
    for channel in filter(output_channel_is_enabled, output.channels):
        if channel.id:
            output_channel_activate__weighted_average(output, channel)


def output_activate__quaternion_blend(output: 'RBFDriverOutput') -> None:
    object = output.object

    if object:
        id = object.data

        data = np.array([tuple(ch.data.values()) for ch in output.channels], dtype=float)
        mean = np.mean(data, axis=1)

        for column in data.T:
            column[:] = quaternion_to_logarithmic_map(mean @ Quaternion(tuple(column)))

        for channel, row in zip(output.channels, data):
            id[idprop_cdata(channel)] = list(row)

        weights = [pose.weight for pose in owner_resolve(output, ".outputs").poses]
        weights = [f'{weight.data_path}[{weight.array_index}]' for weight in weights]
        indices = np.ndarray([list(range(len(weights)))] * 4, dtype=int)

        # Compute the sum of the logarithmic maps
        logarithmic_sum = idprop_qblend_logsum(output)
        id[logarithmic_sum] = [0.0] * 4

        if len(weights) > MAX_PARAMS:
            length = len(weights)
            offset = 0
            blocks: List[Tuple[Sequence[str], np.ndarray]] = []

            for _ in range(floor(length/MAX_PARAMS)):
                index = offset + MAX_PARAMS
                blocks.append(weights[offset:index], indices.T[offset:index].T)
                offset = index

            if offset < length:
                blocks.append(weights[offset:], indices.T[offset:].T)

            for channel_index, channel in output.channels:
                cdata = idprop_cdata(channel)
                cnode = idprop_cnode(channel)
                count = len(blocks)
                id[cnode] = [0.0] * count

                for index, (weights, indices) in enumerate(blocks):
                    fcurve = driver_ensure(id, f'["{cnode}"]', index)
                    tokens = [f'["{cdata}"][{index}]' for index in indices[channel_index]]
                    output_channel_driver_init__dot(fcurve, object, weights, tokens)

                tokens = [f'["{cnode}"][{index}]' for index in range(count)]
                fcurve = driver_ensure(id, f'["{logarithmic_sum}"]', channel_index)
                output_channel_driver_init__sum(fcurve, object, tokens)
        else:
            for index, channel in enumerate(output.channels):
                idprop = idprop_cdata(channel)
                tokens = [f'["{idprop}"][{i}' for i in range(len(weights))]
                fcurve = driver_ensure(id, f'["{logarithmic_sum}"]', index)
                output_channel_driver_init__dot(fcurve, object, weights, tokens)

        tokens = [f'["{logarithmic_sum}"][{i}]' for i in range(4)]

        # Add a driver to compute the vector magnitude for the summed logarithmic maps
        propname = idprop_qlend_magnitude(output)
        id[propname] = 0.0

        magnitude = driver_ensure(id, f'["{propname}"]')
        output_driver_init__qblend_magnitude(magnitude, object, tokens)

        # Add a driver to compute the sine of the magnitude
        propname = idprop_qlend_sine(output)
        id[propname] = 0.0

        sine = driver_ensure(id, f'["{propname}"]')
        output_driver_init__qblend_sine(sine, object, magnitude.data_path)

        # Add a driver to compute the exponent of the summed logarithmic maps
        propname = idprop_qlend_exponent(output)
        id[propname] = 0.0

        exponent = driver_ensure(id, f'["{propname}"]')
        output_driver_init__qblend_exponent(exponent, object, tokens)

        # Add a driver to compute the exponential map of the summed logarithmic maps
        propname = idprop_qlend_exponential_map(output)
        id[propname] = list(repeat(0.0, 4))

        exponential_map = []
        for index in range(4):
            fcurve = driver_ensure(id, f'["{propname}"]', index)
            exponential_map.append(fcurve)
            output_channel_driver_init__qblend_exponential_map(fcurve,
                                                               object,
                                                               tokens,
                                                               magnitude.data_path,
                                                               sine.data_path,
                                                               exponent.data_path)

        # Final driver multiplies the exponential map by the mean quaternion
        for channel in output.channels:
            tokens = [f'{fc.data_path}[{fcurve.array_index}]' for fc in exponential_map]
            fcurve = driver_ensure(channel.id, channel.data_path, channel.array_index)
            fcurve.mute = channel.mute
            output_channel_driver_init__qblend_final(fcurve, object, mean, tokens)


def output_deactivate__quaternion_blend(output: 'RBFDriverOutput') -> None:
    object = output.object
    if object:
        for channel in output.channels:
            driver_remove(object, channel.data_path, channel.array_index)
            idprop_remove(id, idprop_cnode(channel), remove_drivers=True)
            idprop_remove(id, idprop_cdata(channel), remove_drivers=False)
    id = output.id_data.data
    for idprop in (
        idprop_qblend_logsum,
        idprop_qlend_magnitude,
        idprop_qlend_sine,
        idprop_qlend_exponent,
        idprop_qlend_exponential_map,
        ):
        idprop_remove(id, idprop(output), remove_drivers=True)


def output_activate(output: 'RBFDriverOutput') -> None:
    if output_uses_logarithmic_map(output):
        output_activate__quaternion_blend(output)
    else:
        output_activate__weighted_average(output)


def output_channel_deactivate__weighted_average(output: 'RBFDriverOutput',
                                                channel: 'RBFDriverOutputChannel') -> None:
    id = channel.id
    if id:
        driver_remove(id, *output_channel_data_target(channel))
    id = output.id_data.data
    idprop_remove(id, idprop_cnode(channel), remove_drivers=True)
    idprop_remove(id, idprop_cdata(channel), remove_drivers=False)


def output_deactivate__weighted_average(output: 'RBFDriverOutput') -> None:
    for channel in filter(output_channel_is_enabled, output.channels):
        output_channel_deactivate__weighted_average(output, channel)


def output_uses_logarithmic_map(output: 'RBFDriverOutput') -> bool:
    return (output.type == 'ROTATION'
            and output.rotation_mode == 'QUATERNION'
            and output.use_logarithmic_map)


def output_deactivate(output: 'RBFDriverOutput') -> None:
    if output_uses_logarithmic_map(output):
        output_deactivate__quaternion_blend(output)
    else:
        output_deactivate__weighted_average(output)


def outputs_activate_valid(outputs: Iterable['RBFDriverOutput']) -> None:
    for output in outputs:
        if output.is_valid:
            output_activate(output)


def output_logmap_matrix(output: 'RBFDriverOutput') -> np.ndarray:
    assert output.type == 'ROTATION' and output.rotation_mode == 'QUATERNION' and output.use_logarithmic_map
    data = np.array([tuple(ch.values()) for ch in output.channels], dtype=float)
    mean = np.mean(data, axis=1)
    for column in data.T:
        column[:] = quaternion_to_logarithmic_map(mean @ Quaternion(tuple(column)))
    return data


@event_handler(OutputChannelNameChangeEvent)
def on_output_channel_name_change(event: OutputChannelNameChangeEvent) -> None:
    channel = event.channel
    driver: 'RBFDriver' = owner_resolve(channel, ".outputs")
    if driver.type == 'SHAPE_KEY':
        output: 'RBFDriverOutput' = owner_resolve(channel, ".channels")
        output_deactivate(output)
        output_assign_channel_data_targets(output)
        if output.is_valid:
            output_activate(output)


@event_handler(OutputBoneTargetChangeEvent)
def on_output_bone_target_change(event: OutputBoneTargetChangeEvent) -> None:
    output = event.output
    if output.type in {'LOCATION', 'ROTATION', 'SCALE'}:
        output_deactivate(output)
        output_assign_channel_data_targets(output)
        if output.is_valid:
            output_activate(output)


@event_handler(OutputDataPathChangeEvent)
def on_output_data_path_change(event: OutputDataPathChangeEvent) -> None:
    output = event.output
    if output.type == 'SINGLE_PROP':
        output_deactivate(output)
        output_assign_channel_data_targets(output)
        if output.is_valid:
            output_activate(output)


@event_handler(OutputIDTypeUpdateEvent)
def on_output_id_type_update(event: OutputIDTypeUpdateEvent) -> None:
    output = event.output
    if output.type == 'SINGLE_PROP':
        object = output.object
        if object:
            # Trigger object change event and let corresponding event handler handle this
            if event.value != 'OBJECT' and object.type != event.value:
                output.object = None
            else:
                output.object = object


@event_handler(OutputObjectChangeEvent)
def on_output_object_change(event: OutputObjectChangeEvent) -> None:
    output = event.output
    output_deactivate(output)

    id = output.id
    for channel in output.channels:
        channel.id__internal__ = id

    if output.is_valid:
        output_activate(output)


@event_handler(OutputChannelMuteUpdateEvent)
def on_output_channel_mute_update(event: OutputChannelMuteUpdateEvent) -> None:
    channel = event.channel
    if channel.is_enabled:
        id = channel.id
        if id:
            fcurve = driver_find(id, *output_channel_data_target(channel))
            if fcurve:
                fcurve.mute = event.value


@event_handler(OutputRotationModeChangeEvent)
def on_output_rotation_mode_change(event: OutputRotationModeChangeEvent) -> None:
    '''
    '''
    output = event.output
    if output.type == 'ROTATION':
        if event.previous_value == 'QUATERNION' and output.use_logarithmic_map:
            output_deactivate__quaternion_blend(output)
        else:
            output_deactivate__weighted_average(output)

        channels: 'RBFDriverOutputChannels' = output.channels

        if event.value == 'EULER':            
            channels[0]["is_enabled"] = False
            channels[1]["is_enabled"] = output.use_x
            channels[2]["is_enabled"] = output.use_y
            channels[3]["is_enabled"] = output.use_z
        else:
            for channel in channels:
                channel["is_enabled"] = True

        output_assign_channel_data_targets__transforms(output)

        if output.is_valid:
            output_activate(output)


@event_handler(OutputUseAxisUpdateEvent)
def on_output_use_axis_update(event: OutputUseAxisUpdateEvent) -> None:
    output = event.output
    if output.is_valid:
        channel = None

        if output.type in {'LOCATION', 'SCALE'}:
            channel = output.channels['XYZ'.index(event.axis)]
        elif output.type == 'ROTATION' and output.rotation_mode == 'EULER':
            channel = output.channels['WXYZ'.index(event.axis)]
        
        if channel is not None:
            if event.value:
                channel["is_enabled"] = True
                output_channel_activate__weighted_average(output, channel)
            else:
                if channel.is_enabled:
                    output_channel_deactivate__weighted_average(output, channel)
                channel["is_enabled"] = False


@event_handler(OutputUseLogarithmicMapUpdateEvent)
def on_output_use_logarithmic_map_update(event: OutputUseLogarithmicMapUpdateEvent) -> None:
    output = event.output
    if output.type == 'ROTATION' and output.rotation_mode == 'QUATERNION':
        if event.value:
            output_deactivate__weighted_average(output)
            output_activate__quaternion_blend(output)
        else:
            output_deactivate__quaternion_blend(output)
            output_activate__weighted_average(output)


@event_handler(PoseNewEvent)
def on_pose_new(event: PoseNewEvent) -> None:
    outputs_activate_valid(owner_resolve(event.pose, ".poses").outputs)


@event_handler(PoseRemovedEvent)
def on_pose_removed(event: PoseRemovedEvent) -> None:
    outputs_activate_valid(owner_resolve(event.pose, ".poses").outputs)


@event_handler(PoseUpdateEvent)
def on_pose_update(event: PoseUpdateEvent) -> None:
    outputs_activate_valid(owner_resolve(event.pose, ".poses").outputs)
