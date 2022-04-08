
from itertools import chain, repeat
from math import floor
from operator import attrgetter
from typing import List, Optional, Sequence, Tuple, TYPE_CHECKING
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
from ..api.output_channel_data_sample import OutputChannelDataSampleUpdateEvent
from ..api.output_channel import (OutputChannelBoneTargetChangeEvent,
                                  OutputChannelDataPathUpdateEvent,
                                  OutputChannelIsEnabledUpdateEvent,
                                  OutputChannelMuteUpdateEvent,
                                  OutputChannelObjectChangeEvent)
from ..api.output_channels import OutputChannelRemovedEvent
from ..api.output import (OutputRotationModeChangeEvent,
                          OutputUseLogarithmicMapUpdateEvent)
if TYPE_CHECKING:
    from bpy.types import FCurve, Object
    from ..api.output_channel import RBFDriverOutputChannel
    from ..api.output import RBFDriverOutput
    from ..api.driver import RBFDriver

EPSILON = 10 * np.finfo(float).resolution


def output_channel_driver_update__dot_product(fcurve: 'FCurve',
                                              object: 'Object',
                                              pose_weight_data_paths: Sequence[str],
                                              param_data_paths: Sequence[str],
                                              influence_data_path: str) -> None:
    driver = fcurve.driver
    keygen = DriverVariableNameGenerator()
    tokens = []

    variables = driver.variables
    driver_variables_clear(variables)

    for w, x in zip(pose_weight_data_paths, param_data_paths):

        weight = variables.new()
        weight.type = 'SINGLE_PROP'
        weight.name = next(keygen)

        target = weight.targets[0]
        target.id_type = object.type
        target.id = object.data
        target.data_path = w

        param = variables.new()
        param.type = 'SINGLE_PROP'
        param.name = next(keygen)

        target = param.targets[0]
        target.id_type = object.type
        target.id = object.data
        target.data_path = x

        tokens.append(f'{weight.name}*{param.name}')

    influence = variables.new()
    influence.type = 'SINGLE_PROP'
    influence.name = next(keygen)

    target = influence.targets[0]
    target.id_type = object.type
    target.id = object.data
    target.data_path = influence_data_path

    driver.type = 'SCRIPTED'
    driver.expression = f'{influence.name}*({"+".join(tokens)})'


import numpy as np
MAX_PARAMS = 32


def output_channel_data_target(output: 'RBFDriverOutput', channel: 'RBFDriverOutputChannel') -> Tuple[str, Optional[int]]:

    if channel.is_property_set("array_index"):
        return channel.data_path, channel.array_index

    if output.type == 'NONE' and channel.data_path.endswith("]"):
        index = channel.data_path[channel.data_path.rfind("[")+1:-1]
        if index.isdigit():
            return channel.data_path, index

    return channel.data_path, None

def idprop_params(output: 'RBFDriverOutput') -> str:
    return f'rbfn_odata_{output.identifier}'

def output_params(channels: Sequence['RBFDriverOutputChannel']) -> np.ndarray:

    data = []
    index = 0
    for channel in channels:
        row = []
        for value in channel.data.values():
            row.append((index, value))
            index += 1
        data.append(row)

    return np.array(data, dtype=[("index", int), ("value", float)])

def output_ranges(params: np.ndarray) -> List[np.ndarray]:
    offset = 0
    ranges = []
    length = params.shape[1]
    params = params.T

    for _ in range(floor(length/MAX_PARAMS)):
        ranges.append(params[offset:offset + MAX_PARAMS].T)

    if offset < length:
        ranges.append(params[offset:length].T)

    return ranges

# params  = quaternion -> identity * quaternion -> log
# driver1 = wa * qa[i] + wb * qb[i] ...
# driver2 = vnorm
# driver3 = sin(vnorm) / vnorm
# driver4 = exp(q[0])
# driver5 = identity * exp: w, x, y, z

def idprop_logsum(output: 'RBFDriverOutput') -> str:
    return f'rbfn_ologs_{output.identifier}'


def output_drivers_logsum(fcurve: 'FCurve',
                          object: 'Object',
                          params: Sequence[str],
                          weights: Sequence[str]) -> None:

    keygen = DriverVariableNameGenerator()
    driver = fcurve.driver
    driver.type = 'SCRIPTED'

    size = len(weights)
    vars = driver_variables_ensure(driver.variables, size*2)

    for var, path in zip(vars, chain(params, weights)):
        var.type = 'SINGLE_PROP'
        var.name = next(keygen)

        tgt = var.targets[0]
        tgt.id_type = object.type
        tgt.id = object.data
        tgt.data_path = path

    driver.expression = "+".join(f'{w.name}*{p.name}' for w, p in zip(vars[:size], vars[size:]))


def idprop_norm(output: 'RBFDriverOutput') -> str:
    return f'rbfn_onorm_{output.identifier}'


def output_drivers_norm(fcurve: 'FCurve', object: 'Object', logsum: Sequence['FCurve']) -> None:

    driver = fcurve.driver
    driver.type = 'SCRIPTED'
    driver.expression = f'sqrt(pow(x, 2.0) + pow(y, 2.0) + pow(z, 2.0))'

    for var, key, fc in zip(driver_variables_ensure(driver.variables, 3), "xyz", logsum):
        var.type = 'SINGLE_PROP'
        var.name = key

        tgt = var.targets[0]
        tgt.id_type = object.type
        tgt.id = object.data
        tgt.data_path = f'{fc.data_path}[{fc.array_index}]'

def idprop_sine(output: 'RBFDriverOutput') -> str:
    return f'rbfn_osine_{output.identifier}'


def output_drivers_sine(fcurve: 'FCurve', object: 'Object', norm: 'FCurve') -> None:

    driver = fcurve.driver
    driver.type = 'SCRIPTED'
    driver.expression = f'sin(n) / n if n != 0.0 else sin(n)'

    var = driver_variables_ensure(driver.variables, 1)[0]
    var.type = 'SINGLE_PROP'
    var.name = "n"

    tgt = var.targets[0]
    tgt.id_type = object.type
    tgt.id = object.data
    tgt.data_path = norm.data_path

def idprop_exponent(output: 'RBFDriverOutput') -> str:
    return f'rbfn_oexpn_{output.identifier}'

def output_drivers_exponent(fcurve: 'FCurve',
                            object: 'Object',
                            logsum: Sequence['FCurve']) -> None:

    driver = fcurve.driver
    driver.type = 'SCRIPTED'
    driver.expression = f'exp(w)'

    var = driver_variables_ensure(driver.variables, 1)[0]
    var.type = 'SINGLE_PROP'
    var.name = "w"

    tgt = var.targets[0]
    tgt.id_type = object.type
    tgt.id = object.data
    tgt.data_path = f'{logsum[0].data_path}[0]'

def idprop_expmap(output: 'RBFDriverOutput') -> str:
    return f'rbfn_oemap_{output.identifier}'

def output_drivers_expmap(fcurve: 'FCurve',
                          object: 'Object',
                          logsum: Sequence['FCurve'],
                          norm: 'FCurve',
                          sine: 'FCurve',
                          exponent: 'FCurve') -> None:
    driver = fcurve.driver
    driver.type = 'SCRIPTED'

    vars = driver.variables
    driver_variables_clear(vars)

    for name, fc in zip("se", (sine, exponent)):
        var = vars.new()
        var.type = 'SINGLE_PROP'
        var.name = name

        tgt = var.targets[0]
        tgt.id_type = object.type
        tgt.id = object.data
        tgt.data_path = fc.data_path

    if fcurve.array_index == 0:
        var = vars.new()
        var.type = 'SINGLE_PROP'
        var.name = "n"

        tgt = var.targets[0]
        tgt.id_type = object.type
        tgt.id = object.data
        tgt.data_path = norm.data_path

        driver.expression = f'e * cos(n) if n > {EPSILON} else e'
    else:
        var = vars.new()
        var.type = 'SINGLE_PROP'
        var.name = "q"

        tgt = var.targets[0]
        tgt.id_type = object.type
        tgt.id = object.data
        tgt.data_path = f'{logsum[fcurve.array_index].data_path}[{fcurve.array_index}]'

        driver.expression = f'e * s * q'


def output_drivers_expmul(fcurve: 'FCurve',
                          object: 'Object',
                          identity: Sequence[float],
                          expmap: Sequence['FCurve']) -> None:
    
    driver = fcurve.driver
    driver.type = 'SCRIPTED'

    for var, key, fc in zip(driver_variables_ensure(driver.variables, 4), "wxyz", expmap):
        var.type = 'SINGLE_PROP'
        var.name = key

        tgt = var.targets[0]
        tgt.id_type = object.type
        tgt.id = object.data
        tgt.data_path = f'{fc.data_path}[{fc.array_index}]'

    i = fcurve.array_index
    w, x, y, z = identity

    if   i == 0: driver.expression = f'{w}*w - {x}*x - {y}*y - {z}*z'
    elif i == 1: driver.expression = f'{w}*x + {x}*w + {y}*z - {z}*y'
    elif i == 2: driver.expression = f'{w}*y - {x}*z + {y}*w + {z}*x'
    elif i == 3: driver.expression = f'{w}*z + {x}*y - {y}*x + {z}*w'


weight = attrgetter("weight")


def output_drivers_exp(output: 'RBFDriverOutput') -> None:
    ob = output.id_data
    id = ob.data

    poses = owner_resolve(output, ".outputs").poses
    pname = idprop_params(output)
    pdata = output_params(output.channels)
    qmean = np.mean(pdata, axis=1)

    for q in pdata.T:
        q["value"][:] = quaternion_to_logarithmic_map(qmean @ Quaternion(q["value"]))
    
    id[pname] = list(pdata["value"].flat)

    # logsum
    name = idprop_logsum(output)
    id[name] = list(repeat(0.0, 4))

    logsum = []
    ws = [f'{x.data_path}[{x.array_index}]' for x in map(weight, poses)]
    for i, row in enumerate(pdata):
        fc = driver_ensure(id, f'["{name}"]', i)
        logsum.append(fc)
        output_drivers_logsum(fc, ob, [f'["{pname}"][{i}]' for i in row["index"]], ws)

    # norm
    name = idprop_norm(output)
    id[name] = 0.0

    norm = driver_ensure(id, f'["{name}"]')
    output_drivers_norm(norm, ob, logsum)

    # sine
    name = idprop_sine(output)
    id[name] = 0.0

    sine = driver_ensure(id, f'["{name}"]')
    output_drivers_sine(sine, ob, norm)

    # exponent
    name = idprop_exponent(output)
    id[name] = 0.0

    exponent = driver_ensure(id, f'["{name}"]')
    output_drivers_exponent(exponent, ob, logsum)

    # expmap
    name = idprop_expmap(output)
    id[name] = list(repeat(0.0, 4))

    expmap = []
    for i in range(4):
        fc = driver_ensure(id, f'["{name}"]', i)
        expmap.append(fc)
        output_drivers_expmap(fc, ob, logsum, norm, sine, exponent)

    # expmul
    for ch in output.channels:
        fc = driver_ensure(ch.id, ch.data_path, ch.array_index)
        output_drivers_expmul(fc, ob, qmean, expmap)


def output_drivers_update(output: 'RBFDriverOutput') -> None:

    if output.type == 'ROTATION' and output.use_logarithmic_map:
        output_drivers_exp(output)
        return

    channels = [c for c in output.channels if c.is_enabled and c.is_valid]

    id = output.id_data.data
    id_type = output.id_data.type
    params = output_params(channels)
    idprop = f'rbfn_odata_{output.identifier}'

    if not params.size:
        # TODO lots more stuff
        idprop_remove(id, idprop)
        return

    # TODO remove idprop if no params???

    output.id_data.data[idprop] = list(params["value"].flat)

    if params.shape[1] > MAX_PARAMS:
        # TODO
        pass
        # ranges = output_ranges(params)
        # for range_ in ranges:



    driver = owner_resolve(output, ".outputs")

    wpaths = [f'{pose.weight.data_path}[{pose.weight.array_index}]' for pose in driver.poses]
    inpath = output.influence.data_path

    for channel, data in zip(channels, params):
        dpaths = [f'["{idprop}"][{i}]' for i in data["index"]]
        fcurve = driver_ensure(channel.id, *output_channel_data_target(output, channel))
        fcurve.mute = channel.mute
        output_channel_driver_update__dot_product(fcurve, output.id_data, wpaths, dpaths, inpath)


def output_drivers_remove(output: 'RBFDriverOutput') -> None:
    channel: 'RBFDriverOutputChannel'
    for channel in output.channels:
        id = channel.id
        if id:
            driver_remove(id, *output_channel_data_target(output, channel))


@event_handler(OutputChannelDataSampleUpdateEvent)
def on_output_channel_data_sample_update(event: OutputChannelDataSampleUpdateEvent) -> None:
    '''
    '''
    output: 'RBFDriverOutput' = owner_resolve(event.sample, ".channels")
    output_drivers_update(output)


@event_handler(OutputChannelBoneTargetChangeEvent)
def on_output_channel_bone_target_change(event: OutputChannelBoneTargetChangeEvent) -> None:
    '''
    The bone target change event is only dispatched if the channel has an armature id and
    the output is either location, rotation, scale or bbone
    '''
    output: 'RBFDriverOutput' = owner_resolve(event.channel, ".channels")
    output_drivers_update(output)


@event_handler(OutputChannelDataPathUpdateEvent)
def on_output_channel_data_path_update(event: OutputChannelDataPathUpdateEvent) -> None:
    '''
    '''
    output: 'RBFDriverOutput' = owner_resolve(event.channel, ".channels")
    output_drivers_update(output)


@event_handler(OutputChannelIsEnabledUpdateEvent)
def on_output_channel_is_enabled_update(event: OutputChannelIsEnabledUpdateEvent) -> None:
    '''
    '''
    output: 'RBFDriverOutput' = owner_resolve(event.channel, ".channels")
    if not event.value:
        id = event.channel.id
        if id:
            driver_remove(id, *output_channel_data_target(output, event.channel))
    output_drivers_update(output)


@event_handler(OutputChannelMuteUpdateEvent)
def on_output_channel_mute_update(event: OutputChannelMuteUpdateEvent) -> None:
    '''
    '''
    channel = event.channel
    if channel.is_enabled and channel.is_valid:
        output = owner_resolve(channel, ".channels")
        fcurve = driver_find(channel.id, *output_channel_data_target(output, channel))
        if fcurve:
            fcurve.mute = event.value


@event_handler(OutputChannelObjectChangeEvent)
def on_output_channel_object_change(event: OutputChannelObjectChangeEvent) -> None:
    '''
    '''
    output: 'RBFDriverOutput' = owner_resolve(event.channel, ".channels")
    output_drivers_update(output)


@event_handler(OutputChannelRemovedEvent)
def on_output_channel_removed(event: OutputChannelRemovedEvent) -> None:
    '''
    '''
    output: 'RBFDriverOutput' = owner_resolve(event.channels, ".")
    output_drivers_update(output)


def remove_logmap_drivers(output: 'RBFDriverOutput') -> None:
    id = output.id_data.data
    for fn in (idprop_logsum, idprop_norm, idprop_sine, idprop_exponent, idprop_expmap):
        idprop_remove(id, fn(output), remove_drivers=True)


@event_handler(OutputRotationModeChangeEvent)
def on_output_rotation_mode_change(event: OutputRotationModeChangeEvent) -> None:
    '''
    '''
    output = event.output
    if event.previous_value == 'QUATERNION' and output.use_logarithmic_map:
        remove_logmap_drivers(output)
    output_drivers_update(output)


@event_handler(OutputUseLogarithmicMapUpdateEvent)
def on_output_use_logarithmic_map_update(event: OutputUseLogarithmicMapUpdateEvent) -> None:
    '''
    '''
    output = event.output
    if output.type == 'ROTATION':
        if not event.value: remove_logmap_drivers(output)
        output_drivers_update(output)


@event_handler(PoseNewEvent)
def on_pose_new(event: PoseNewEvent) -> None:
    '''
    '''
    driver: 'RBFDriver' = owner_resolve(event.pose, ".poses")
    for output in driver.outputs:
        output_drivers_update(output)


@event_handler(PoseRemovedEvent)
def on_pose_removed(event: PoseRemovedEvent) -> None:
    '''
    '''
    driver: 'RBFDriver' = owner_resolve(event.poses, ".")
    for output in driver.outputs:
        output_drivers_update(output)


@event_handler(PoseUpdateEvent)
def on_pose_update(event: PoseUpdateEvent) -> None:
    '''
    '''
    for output in event.outputs:
        output_drivers_update(output)
