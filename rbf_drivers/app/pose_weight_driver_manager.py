
from typing import Callable, Iterator, Sequence, Tuple, Union, TYPE_CHECKING
from logging import getLogger
from math import acos, asin, fabs, pi, sqrt
import numpy as np
from .events import event_handler
from .utils import owner_resolve, driver_variables_ensure, idprop_array_ensure, idprop_remove
from ..lib.curve_mapping import keyframe_points_assign, to_bezier
from ..api.input_target import (InputTargetPropertyUpdateEvent,
                                InputTargetBoneTargetUpdateEvent,
                                InputTargetDataPathUpdateEvent,
                                InputTargetIDTypeUpdateEvent,
                                InputTargetObjectUpdateEvent,
                                InputTargetRotationModeUpdateEvent,
                                InputTargetTransformSpaceUpdateEvent,
                                InputTargetTransformTypeUpdateEvent)
from ..api.input_variable import (input_variable_is_enabled,
                                  InputVariableNameUpdateEvent,
                                  InputVariableIsEnabledUpdateEvent,
                                  InputVariableTypeUpdateEvent)
from ..api.input import (input_is_valid,
                         InputBoneTargetUpdateEvent,
                         InputDataTypeUpdateEvent,
                         InputObjectUpdateEvent,
                         InputRotationAxisUpdateEvent,
                         InputRotationModeChangeEvent,
                         InputTransformSpaceChangeEvent,
                         InputTypeUpdateEvent,
                         InputUseSwingUpdateEvent,
                         InputRotationModeChangeEvent)
from ..api.inputs import InputNewEvent, InputRemovedEvent
from ..api.pose_interpolation import PoseInterpolationUpdateEvent
from ..api.pose import PoseUpdateEvent
from ..api.poses import PoseMoveEvent, PoseNewEvent, PoseRemovedEvent
from ..api.driver_interpolation import DriverInterpolationUpdateEvent
from ..api.drivers import DriverDisposableEvent
from ..lib.driver_utils import driver_ensure, driver_variables_clear, DriverVariableNameGenerator
if TYPE_CHECKING:
    from bpy.types import Driver, DriverTarget, DriverVariable, FCurve
    from ..api.input_target import RBFDriverInputTarget
    from ..api.input_variable_data import RBFDriverInputVariableData
    from ..api.input_variable import RBFDriverInputVariable
    from ..api.input import RBFDriverInput
    from ..api.pose import RBFDriverPose
    from ..api.driver import RBFDriver

log = getLogger("rbf_drivers")


def distance_euclidean(a: Sequence[float], b: Sequence[float]) -> float:
    return sqrt(sum(pow(ai - bi, 2.0) for ai, bi in zip(a, b)))


def distance_angle(a: Sequence[float], b: Sequence[float]) -> float:
    return fabs(a[0]-b[0])/pi


def distance_quaternion(a: Sequence[float], b: Sequence[float]) -> float:
    return acos((2.0 * pow(min(max(sum(ai * bi for ai, bi in zip(a, b)), -1.0), 1.0), 2.0)) - 1.0) / pi


def distance_direction(a: Sequence[float], b: Sequence[float], axis: str) -> float:
    aw, ax, ay, az = a
    bw, bx, by, bz = b

    if axis == 'X':
        a = (1.0 - 2.0 * (ay * ay + az * az), 2.0 * (ax * ay + aw * az), 2.0 * (ax * az - aw * ay))
        b = (1.0 - 2.0 * (by * by + bz * bz), 2.0 * (bx * by + bw * bz), 2.0 * (bx * bz - bw * by))
    elif axis == 'Y':
        a = (2.0 * (ax * ay - aw * az), 1.0 - 2.0 * (ax * ax + az * az), 2.0 * (ay * az + aw * ax))
        b = (2.0 * (bx * by - bw * bz), 1.0 - 2.0 * (bx * bx + bz * bz), 2.0 * (by * bz + bw * bx))
    else:
        a = (2.0 * (ax * az + aw * ay), 2.0 * (ay * az - aw * ax), 1.0 - 2.0 * (ax * ax + ay * ay))
        b = (2.0 * (bx * bz + bw * by), 2.0 * (by * bz - bw * bx), 1.0 - 2.0 * (bx * bx + by * by))

    return (asin((sum(ai * bi for ai, bi in zip(a, b)))) - -(pi / 2.0)) / pi


def input_distance_metric(input: 'RBFDriverInput') -> Union[Callable[[Sequence[float], Sequence[float]], float],
                                                            Callable[[Sequence[float], Sequence[float], str], float]]:
    type = input.type

    if type == 'ROTATION':
        mode = input.rotation_mode
        if mode == 'QUATERNION': return distance_quaternion
        if mode == 'SWING'     : return distance_direction
        if mode == 'TWIST'     : return distance_angle

    return distance_euclidean

def input_distance_matrix(input: 'RBFDriverInput') -> np.ndarray:
    active = filter(input_variable_is_enabled, input.variables)
    params = np.array([tuple(v.data.values(v.data.is_normalized)) for v in active], dtype=float).T
    matrix = np.empty((len(params), len(params)), dtype=float)
    metric = input_distance_metric(input)

    for a, row in zip(params, matrix):
        for i, b in enumerate(params):
            row[i] = metric(a, b)

    return matrix


def input_pose_radii(matrix: np.ndarray) -> Iterator[float]:
    for row in np.ma.masked_values(matrix, 0.0, atol=0.001):
        row = row.compressed()
        yield 0.0 if len(row) == 0 else np.min(row)


def tgt_assign__prop(tgt: 'DriverTarget', src: 'RBFDriverInputTarget') -> None:
    tgt.id_type = src.id_type
    tgt.id = src.id
    tgt.data_path = src.data_path


def tgt_assign__xform(tgt: 'DriverTarget', src: 'RBFDriverInputTarget') -> None:
    tgt.id = src.object
    tgt.bone_target = src.bone_target
    tgt.transform_type = src.transform_type
    tgt.transform_space = src.transform_space
    tgt.rotation_mode = src.rotation_mode


def tgt_assign__diff(tgt: 'DriverTarget', src: 'RBFDriverInputTarget') -> None:
    tgt.id = src.object
    tgt.bone_target = src.bone_target
    tgt.transform_space = src.transform_space


def tgt_assign(var: 'DriverVariable', src: 'RBFDriverInputVariable') -> None:
    type = var.type
    if type == 'SINGLE_PROP':
        return tgt_assign__prop(var.targets[0], src.targets[0])
    if type == 'TRANSFORMS' :
        return tgt_assign__xform(var.targets[0], src.targets[0])
    for tgt, src in zip(var.targets, src.targets):
        tgt_assign__diff(tgt, src)


def ipw_dist_metric__euclidean(driver: 'Driver', tokens: Sequence[Tuple[str, str]]) -> None:
    driver.type = 'SCRIPTED'
    driver.expression = f'sqrt({"+".join("pow("+a+"-"+b+",2.0)" for a, b in tokens)})'


def ipw_dist_metric__quaternion(driver: 'Driver', tokens: Sequence[Tuple[str, str]]) -> None:
    if len(tokens) != 4:
        log.error()
        return ipw_dist_metric__euclidean(driver, tokens)

    driver.type = 'SCRIPTED'
    driver.expression = f'acos((2.0*pow(clamp({"+".join(["*".join(x) for x in tokens])},-1.0,1.0),2.0))-1.0)/pi'


def ipw_dist_metric__swing(driver: 'Driver', tokens: Sequence[Tuple[str, str]], axis: str) -> None:
    if len(tokens) != 4:
        log.error()
        return ipw_dist_metric__euclidean(driver, tokens)

    w, x, y, z = tokens

    if axis == 'X':
        a = str(1.0-2.0*(y*y+z*z))
        b = str(2.0*(x*y+w*z))
        c = str(2.0*(x*z-w*y))
        expression = f'(asin((1.0-2.0*(y*y+z*z))*{a}+2.0*(x*y+w*z)*{b}+2.0*(x*z-w*y)*{c})-(pi/2.0))/pi'

    elif axis == 'Y':
        a = str(2.0*(x*y-w*z))
        b = str(1.0-2.0*(x*x+z*z))
        c = str(2.0*(y*z+w*x))
        expression = f'(asin(2.0*(x*y-w*z)*{a}+(1.0-2.0*(x*x+z*z))*{b}+2.0*(y*z+w*x)*{c})--(pi/2.0))/pi'

    else:
        a = str(2.0*(x*z+w*y))
        b = str(2.0*(y*z-w*x))
        c = str(1.0-2.0*(x*x+y*y))
        expression = f'(asin(2.0*(x*z+w*y)*{a}+2.0*(y*z-w*x)*{b}+(1.0-2.0*(x*x+y*y))*{c})--(pi/2.0))/pi'

    driver.type = 'SCRIPTED'
    driver.expression = expression


def ipw_dist_metric__twist(driver: 'Driver', tokens: Sequence[Tuple[str, str]]) -> None:
    if len(tokens) != 1:
        log.error()
        return ipw_dist_metric__euclidean(driver, tokens)

    driver.type = 'SCRIPTED'
    driver.expression = f'fabs({tokens[0][0]}-{str(tokens[0][1])})/pi'


def ipw_dist_metric(fcurve: 'FCurve', input: 'RBFDriverInput', index: int) -> None:
    keygen = DriverVariableNameGenerator()
    tokens = []

    dr = fcurve.driver
    dr.type = 'SCRIPTED'
    driver_variables_clear(dr.variables)

    for src in filter(input_variable_is_enabled, input.variables):
        var = dr.variables.new()
        var.type = src.type
        var.name = next(keygen)
        tgt_assign(var, src)

        data: 'RBFDriverInputVariableData' = src.data
        try:
            val = data.value(index, data.is_normalized)
        except IndexError:
            log.warning()
            val = src.default_value

        if data.is_normalized and data.norm != 0.0:
            param = f'{var.name}/{data.norm}'
        else:
            param = var.name

        tokens.append((param, str(val)))

    if len(tokens) == 0:
        dr.expression = "0.0"
        return

    if input.type == 'ROTATION':
        mode = input.rotation_mode
        if   mode == 'SWING'     : ipw_dist_metric__swing(dr, tokens, input.rotation_axis)
        elif mode == 'TWIST'     : ipw_dist_metric__twist(dr, tokens)
        elif mode == 'QUATERNION': ipw_dist_metric__quaternion(dr, tokens)
        else                     : ipw_dist_metric__euclidean(dr, tokens)
    else:
        ipw_dist_metric__euclidean(dr, tokens)


def ipw_dist_weight(fc: 'FCurve', pose: 'RBFDriverPose', rad: float) -> None:
    dr = fc.driver

    var = dr.variables.new()
    var.type = 'SINGLE_PROP'
    var.name = "r_"

    src = pose.radius
    tgt = var.targets[0]
    tgt.id_type = src.id_type
    tgt.id = src.id
    tgt.data_path = src.data_path

    dr.expression = f'1.0-({dr.expression})/{rad if rad > 0.0 else "1.0"}*{var.name}'


def ipw_dist_idprop(rbfn: 'RBFDriver') -> str:
    return f'rbfn_pdst_{rbfn.identifier}'


def ipw_dist_update(rbfn: 'RBFDriver') -> np.ndarray:

    id = rbfn.id_data.data
    name = ipw_dist_idprop(rbfn)
    path = f'["{name}"]'

    fx = []
    ai = 0

    for input in filter(input_is_valid, rbfn.inputs):
        radii = tuple(input_pose_radii(input_distance_matrix(input)))

        row = []
        fx.append(row)

        for i, (pose, rad) in enumerate(zip(rbfn.poses, radii)):
            fc = driver_ensure(id, path, ai)
            row.append(fc)

            ipw_dist_metric(fc, input, i)
            ipw_dist_weight(fc, pose, rad)
            
            ai += 1

    idprop_array_ensure(id, name, ai)
    return np.array(fx, dtype=object)


def ipw_zero_ensure(rbfn: 'RBFDriver') -> Sequence['FCurve']:
    id = rbfn.id_data.data
    fx = []

    name = ipw_dist_idprop(rbfn)
    path = f'["{name}"]'
    size = len(rbfn.poses)

    idprop_array_ensure(id, name, size)

    for i in range(size):
        fc = driver_ensure(id, path, i)
        dr = fc.driver
        dr.expression = "0.0"
        driver_variables_clear(dr.variables)
        fx.append(fc)

    return fx


def ipw_norm_idprop(rbfn: 'RBFDriver') -> str:
    return f'rbfn_pavg_{rbfn.identifier}'


def ipw_norm_update(rbfn: 'RBFDriver', matrix: np.ndarray) -> Sequence['FCurve']:
    matrix = matrix.T

    ob = rbfn.id_data
    id = ob.data

    pk = ipw_norm_idprop(rbfn)
    dp = f'["{pk}"]'
    fx = []

    for i, ipw_fx in enumerate(matrix.T):
        
        fc_avg = driver_ensure(id, dp, i)
        dr_avg = fc_avg.driver
        keygen = DriverVariableNameGenerator()
        params = []

        dvars = dr_avg.variables
        driver_variables_clear(dvars)

        for fc in ipw_fx:

            var = dvars.new()
            var.type = 'SINGLE_PROP'
            var.name = next(keygen)

            tgt = var.targets[0]
            tgt.id_type = ob.type
            tgt.id = ob.data
            tgt.data_path = f'{fc.data_path}[{fc.array_index}]'

            params.append(var.name)

        dr_avg.type = 'SCRIPTED'
        dr_avg.expression = f'({"+".join(params)})/{float(len(params))}'
        fx.append(fc_avg)

    idprop_array_ensure(id, pk, len(fx))
    return fx


def ipw_norm_remove(rbfn: 'RBFDriver') -> None:
    name = ipw_norm_idprop(rbfn)
    idprop_remove(rbfn.id_data.data, name)


def wgt_infl_assign(rbfn: 'RBFDriver', fx: Sequence['FCurve']) -> None:
    for fc, pose in zip(fx, rbfn.poses):
        dr = fc.driver
        pi = pose.influence

        var = dr.variables.new()
        var.type = 'SINGLE_PROP'
        var.name = 'i_'

        tgt = var.targets[0]
        tgt.id_type = pi.id_type
        tgt.id = pi.id
        tgt.data_path = pi.data_path

        dr.expression = f'{var.name}*({dr.expression})'


def wgt_cmap_assign(rbfn: 'RBFDriver', fx: Sequence['FCurve']) -> None:
    dft = rbfn.interpolation.curve.points
    for fc, pose in zip(fx, rbfn.poses):
        opt = pose.interpolation
        pts = opt.curve.points if opt.use_curve else dft
        keyframe_points_assign(fc.keyframe_points, to_bezier(pts, extrapolate=False))


def wgt_summ_idprop(rbfn: 'RBFDriver') -> str:
    return f'rbfn_wsum_{rbfn.identifier}'


def wgt_summ_update(rbfn: 'RBFDriver', wgts: Sequence['FCurve']) -> 'FCurve':

    ob = rbfn.id_data
    id = ob.data

    name = wgt_summ_idprop(rbfn)
    id[name] = 0.0

    fc = driver_ensure(id, f'["{name}"]')
    dr = fc.driver
    dr.type = 'SUM'

    for wgt, var in zip(wgts, driver_variables_ensure(dr.variables, len(wgts))):
        var.type = 'SINGLE_PROP'
        var.name = f'w{wgt.array_index}'

        tgt = var.targets[0]
        tgt.id_type = ob.type
        tgt.id = wgt.id_data
        tgt.data_path = f'{wgt.data_path}[{wgt.array_index}]'

    return fc


def wgt_summ_remove(rbfn: 'RBFDriver') -> None:
    key = wgt_summ_idprop(rbfn)
    idprop_remove(rbfn.id_data.data, key, remove_drivers=True)


def wgt_norm_idprop(rbfn: 'RBFDriver') -> str:
    return f'rbfn_norm_{rbfn.identifier}'


def wgt_norm_update(rbfn: 'RBFDriver', wgts: Sequence['FCurve'], wsum: 'FCurve') -> Sequence['FCurve']:

    ob = rbfn.id_data
    id = ob.data
    fx = []

    name = wgt_norm_idprop(rbfn)
    path = f'["{name}"]'

    idprop_array_ensure(id, name, len(wgts), remove_drivers=True)
    
    for wgt in wgts:
        fc = driver_ensure(id, path, wgt.array_index)
        dr = fc.driver
        dr.type = 'SCRIPTED'
        dr.expression = "w / s if s != 0.0 else w"
        
        vars = driver_variables_ensure(dr.variables, 2)

        w = vars[0]
        w.type = 'SINGLE_PROP'
        w.name = "w"

        tgt = w.targets[0]
        tgt.id_type = ob.type
        tgt.id = wgt.id_data
        tgt.data_path = f'{wgt.data_path}[{wgt.array_index}]'

        s = vars[1]
        s.type = 'SINGLE_PROP'
        s.name = "s"

        tgt = s.targets[0]
        tgt.id_type = ob.type
        tgt.id = wsum.id_data
        tgt.data_path = wsum.data_path

        fx.append(fc)

    return fx


def wgt_norm_remove(rbfn: 'RBFDriver') -> None:
    name = wgt_norm_idprop(rbfn)
    idprop_remove(rbfn.id_data.data, name, remove_drivers=True)


def pose_weight_drivers_update(rbfn: 'RBFDriver') -> None:

    fx = ipw_dist_update(rbfn)

    if not fx.size:
        ipw_norm_remove(rbfn)
        wgt_summ_remove(rbfn)
        wgt_norm_remove(rbfn)
        fx = ipw_zero_ensure(rbfn)
    else:
        if len(fx) == 1:
            fx = fx[0]
            ipw_norm_remove(rbfn)
        else:
            fx = ipw_norm_update(rbfn, fx)

        wgt_infl_assign(rbfn, fx)
        wgt_cmap_assign(rbfn, fx)
        fx = wgt_norm_update(rbfn, fx, wgt_summ_update(rbfn, fx))

    for pose, fc in zip(rbfn.poses, fx):
        prop = pose.weight
        prop["name"] = fc.data_path[2:-2]
        prop["array_index"] = fc.array_index


@event_handler(InputTargetBoneTargetUpdateEvent,
               InputTargetDataPathUpdateEvent,
               InputTargetIDTypeUpdateEvent,
               InputTargetObjectUpdateEvent,
               InputTargetRotationModeUpdateEvent,
               InputTargetTransformSpaceUpdateEvent,
               InputTargetTransformTypeUpdateEvent)
def on_input_target_property_update(event: InputTargetPropertyUpdateEvent) -> None:
    '''
    Updates pose weight drivers when input target properties change. Note that the
    input target property handlers screen invalid property updates based on the input
    type so no checking is required here.
    '''
    pose_weight_drivers_update(owner_resolve(event.target, ".inputs"))


@event_handler(InputVariableIsEnabledUpdateEvent)
def on_input_variable_is_enabled_update(event: InputVariableIsEnabledUpdateEvent) -> None:
    '''
    '''
    pose_weight_drivers_update(owner_resolve(event.variable, ".inputs"))


@event_handler(InputVariableNameUpdateEvent)
def on_input_variable_name_update(event: InputVariableNameUpdateEvent) -> None:
    input: 'RBFDriverInput' = owner_resolve(event.variable, ".variables")
    if input.type == 'SHAPE_KEY':
        pose_weight_drivers_update(owner_resolve(input, ".inputs"))


@event_handler(InputVariableTypeUpdateEvent)
def on_input_variable_type_update(event: InputVariableTypeUpdateEvent) -> None:
    '''
    Updates pose weight drivers when an input variable type changes. Note that the
    update handlers on the input variable screen invalid update notifications based
    on the input type so no checking is required here.
    '''
    pose_weight_drivers_update(owner_resolve(event.variable, ".inputs"))


@event_handler(InputNewEvent)
def on_input_new(event: InputNewEvent) -> None:
    '''
    '''
    pose_weight_drivers_update(owner_resolve(event.input, ".inputs"))


@event_handler(InputRemovedEvent)
def on_input_removed(event: InputRemovedEvent) -> None:
    '''
    '''
    pose_weight_drivers_update(owner_resolve(event.inputs, "."))


@event_handler(InputBoneTargetUpdateEvent)
def on_input_InputBoneTargetUpdate(event: InputBoneTargetUpdateEvent) -> None:
    '''
    '''
    pose_weight_drivers_update(owner_resolve(event.input, ".inputs"))


@event_handler(InputDataTypeUpdateEvent)
def on_input_InputDataTypeUpdate(event: InputDataTypeUpdateEvent) -> None:
    '''
    '''
    pose_weight_drivers_update(owner_resolve(event.input, ".inputs"))


@event_handler(InputObjectUpdateEvent)
def on_input_InputObjectUpdate(event: InputObjectUpdateEvent) -> None:
    '''
    '''
    pose_weight_drivers_update(owner_resolve(event.input, ".inputs"))


@event_handler(InputRotationAxisUpdateEvent)
def on_input_InputRotationAxisUpdate(event: InputRotationAxisUpdateEvent) -> None:
    '''
    '''
    pose_weight_drivers_update(owner_resolve(event.input, ".inputs"))


@event_handler(InputTransformSpaceChangeEvent)
def on_input_InputTransformSpaceChange(event: InputTransformSpaceChangeEvent) -> None:
    '''
    '''
    pose_weight_drivers_update(owner_resolve(event.input, ".inputs"))


@event_handler(InputTypeUpdateEvent)
def on_input_InputTypeUpdate(event: InputTypeUpdateEvent) -> None:
    '''
    '''
    pose_weight_drivers_update(owner_resolve(event.input, ".inputs"))


@event_handler(InputUseSwingUpdateEvent)
def on_input_InputUseSwingUpdate(event: InputUseSwingUpdateEvent) -> None:
    '''
    '''
    pose_weight_drivers_update(owner_resolve(event.input, ".inputs"))


@event_handler(InputRotationModeChangeEvent)
def on_input_rotation_mode_change(event: InputRotationModeChangeEvent) -> None:
    '''
    '''
    pose_weight_drivers_update(owner_resolve(event.input, ".inputs"))


@event_handler(PoseInterpolationUpdateEvent)
def on_pose_interpolation_update(event: PoseInterpolationUpdateEvent) -> None:
    '''
    '''
    pose_weight_drivers_update(owner_resolve(event.interpolation, ".poses"))


@event_handler(PoseMoveEvent)
def on_pose_move(event: PoseMoveEvent) -> None:
    '''
    '''
    pose_weight_drivers_update(owner_resolve(event.pose, ".poses"))


@event_handler(PoseNewEvent)
def on_pose_new(event: PoseNewEvent) -> None:
    '''
    '''
    pose_weight_drivers_update(owner_resolve(event.pose, ".poses"))


@event_handler(PoseRemovedEvent)
def on_pose_removed(event: PoseRemovedEvent) -> None:
    '''
    '''
    pose_weight_drivers_update(owner_resolve(event.poses, "."))


@event_handler(PoseUpdateEvent)
def on_pose_update(event: PoseUpdateEvent) -> None:
    '''
    '''
    pose_weight_drivers_update(owner_resolve(event.pose, ".poses"))


@event_handler(DriverInterpolationUpdateEvent)
def on_driver_interpolation_update(event: DriverInterpolationUpdateEvent) -> None:
    '''
    '''
    pose_weight_drivers_update(owner_resolve(event.interpolation, "."))


@event_handler(DriverDisposableEvent)
def on_driver_disposable(event: DriverDisposableEvent) -> None:
    '''
    '''
    rbfn: 'RBFDriver' = event.driver
    id = rbfn.id_data.data
    for fn in (ipw_dist_idprop, ipw_norm_idprop, wgt_summ_idprop, wgt_norm_idprop):
        idprop_remove(id, fn(rbfn), remove_drivers=True)
