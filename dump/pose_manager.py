
import dataclasses
from typing import Iterable, Sequence, Tuple, TYPE_CHECKING
from logging import getLogger
from bpy.types import Driver, DriverTarget, DriverVariable, FCurve, Object
import numpy as np
from .events import event_handler
from .utils import idprop_ensure, idprop_remove, idprop_splice, owner_resolve
from ..lib.curve_mapping import BLCMAP_KeyframePointDTO, keyframe_points_assign, to_bezier
from ..lib.driver_utils import (driver_ensure,
                                driver_variables_clear,
                                DriverVariableNameGenerator)
from ..api.input_target import (InputTargetPropertyUpdateEvent,
                                InputTargetBoneTargetUpdateEvent,
                                InputTargetDataPathUpdateEvent,
                                InputTargetIDTypeUpdateEvent,
                                InputTargetObjectUpdateEvent,
                                InputTargetRotationModeUpdateEvent,
                                InputTargetTransformSpaceUpdateEvent,
                                InputTargetTransformTypeUpdateEvent)
from ..api.input_variable import input_variable_is_enabled, InputVariableTypeUpdateEvent
from ..api.input import input_is_valid
from ..api.inputs import InputDisposableEvent
from ..api.pose import PoseNameUpdateEvent
from ..api.poses import PoseNewEvent, PoseDisposableEvent, PoseRemovedEvent
from ...dump.driver_distance_matrix import DriverDistanceMatrixUpdateEvent
from ...dump.driver_variable_matrix import DriverVariableMatrixUpdateEvent
from ..api.drivers import DriverNewEvent, DriverDisposableEvent
if TYPE_CHECKING:
    from ..api.input_target import RBFDriverInputTarget
    from ..api.input_variable import RBFDriverInputVariable
    from ..api.input import RBFDriverInput
    from ..api.pose_interpolation import RBFDriverPoseInterpolation
    from ..api.pose import RBFDriverPose
    from ..api.poses import RBFDriverPoses
    from ...dump.driver_variable_matrix import RBFDriverVariableMatrix
    from ..api.driver import RBFDriver

log = getLogger("rbf_drivers")


def target_assign__singleprop(target: DriverTarget, properties: 'RBFDriverInputTarget') -> None:
    target.id_type = properties.id_type
    target.id = properties.id
    target.data_path = properties.data_path


def target_assign__transforms(target: DriverTarget, properties: 'RBFDriverInputTarget') -> None:
    target.id = properties.object
    target.bone_target = properties.bone_target
    target.transform_type = properties.transform_type
    target.transform_space = properties.transform_space
    target.rotation_mode = properties.rotation_mode


def target_assign__difference(target: DriverTarget, properties: 'RBFDriverInputTarget') -> None:
    target.id = properties.object
    target.bone_target = properties.bone_target
    target.transform_space = properties.transform_space


def variable_targets_assign(variable: DriverVariable, properties: 'RBFDriverInputVariable') -> None:
    type = variable.type

    if type == 'SINGLE_PROP':
        return target_assign__singleprop(variable.targets[0], properties.targets[0])

    if type == 'TRANSFORMS' :
        return target_assign__transforms(variable.targets[0], properties.targets[0])

    for target, properties in zip(variable.targets, properties.targets):
        target_assign__difference(target, properties)


def distance_measure__euclidean(driver: Driver, tokens: Sequence[Tuple[str, str]]) -> None:
    driver.type = 'SCRIPTED'
    driver.expression = f'sqrt({"+".join("pow("+a+"-"+b+",2.0)" for a, b in tokens)})'


def distance_measure__quaternion(driver: Driver, tokens: Sequence[Tuple[str, str]]) -> None:
    if len(tokens) != 4:
        log.error()
        return distance_measure__euclidean(driver, tokens)

    driver.type = 'SCRIPTED'
    driver.expression = f'acos((2.0*pow(clamp({"+".join(["*".join(x) for x in tokens])},-1.0,1.0),2.0))-1.0)/pi'


def distance_measure__swing(driver: Driver, tokens: Sequence[Tuple[str, str]], axis: str) -> None:
    if len(tokens) != 4:
        log.error()
        return distance_measure__euclidean(driver, tokens)

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


def distance_measure__twist(driver: Driver, tokens: Sequence[Tuple[str, str]]) -> None:
    if len(tokens) != 1:
        log.error()
        return distance_measure__euclidean(driver, tokens)

    driver.type = 'SCRIPTED'
    driver.expression = f'fabs({tokens[0][0]}-{str(tokens[0][1])})/pi'


def distance_measure(fcurve: FCurve, input: "RBFDriverInput", index: int) -> None:

    keygen = DriverVariableNameGenerator()
    tokens = []
    driver = fcurve.driver
    driver.type = 'SCRIPTED'
    driver_variables_clear(driver.variables)

    for properties in filter(input_variable_is_enabled, input.variables):
        variable = driver.variables.new()
        variable.type = properties.type
        variable.name = next(keygen)
        variable_targets_assign(variable, properties)

        data = properties.data
        try:
            value = data.value(index, data.is_normalized)
        except IndexError:
            log.warning()
            value = properties.default_value

        if data.is_normalized and data.norm != 0.0:
            param = f'{variable.name}/{data.norm}'
        else:
            param = variable.name

        tokens.append((param, str(value)))

    if len(tokens) == 0:
        driver.expression = "0.0"
        return

    if input.type == 'ROTATION':
        mode = input.rotation_mode
        if mode == 'SWING'      : return distance_measure__swing(driver, tokens, mode[-1])
        if mode == 'TWIST'      : return distance_measure__twist(driver, tokens)
        if mode == 'QUATERNION' : return distance_measure__quaternion(driver, tokens)

    distance_measure__euclidean(driver, tokens)


def fcurve_mirror(fcurve: FCurve) -> None:
    points = []
    for point in fcurve.keyframe_points:
        points.append(BLCMAP_KeyframePointDTO(interpolation=point.interpolation,
                                              easing=point.easing,
                                              co=tuple(point.co),
                                              handle_left_type=point.handle_left_type,
                                              handle_right_type=point.handle_right_type,
                                              handle_left=tuple(point.handle_left),
                                              handle_right=tuple(point.handle_right)))

    point = points[0]
    point.handle_left = (-point.handle_right[0], point.handle_right[1])

    for point in points[1:]:
        points.insert(0, dataclasses.replace(point,
                                             co=(-point.co[0], point.co[1]),
                                             handle_left_type=point.handle_right_type,
                                             handle_right_type=point.handle_left_type,
                                             handle_left=(-point.handle_right[0], point.handle_right[1]),
                                             handle_right=(-point.handle_left[0], point.handle_left[1])))

    keyframe_points_assign(fcurve.keyframe_points, points)


def apply_influence(fcurve: FCurve, influence: 'IDPropertyTarget') -> None:

    driver = fcurve.driver

    variable = driver.variables.new()
    variable.type = 'SINGLE_PROP'
    variable.name = 'i_'

    target = variable.targets[0]
    target.id_type = influence.id_type
    target.id = influence.id
    target.data_path = influence.data_path

    driver.expression = f'{variable.name}*({driver.expression})'


def distance_average(fcurve: FCurve, object: Object, inputs: Sequence[FCurve]) -> None:

    keygen = DriverVariableNameGenerator()
    tokens = []
    driver = fcurve.driver

    for fcurve in inputs:

        variable = fcurve.driver.variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = next(keygen)

        target = variable.targets[0]
        target.id_type = object.type
        target.id = object.data
        target.data_path = f'{fcurve.data_path}[{fcurve.array_index}]'

        tokens.append(variable.name)

    driver.type = 'SCRIPTED'
    driver.expression = f'({"+".join(tokens)})/{float(len(tokens))}'


def weight_solve(fcurve: FCurve,
                 object: Object,
                 distance_data_path: str,
                 variable_data_path: str,
                 indices: Iterable[int]) -> None:

    driver = fcurve.driver
    keygen = DriverVariableNameGenerator()
    tokens = []

    variables = driver.variables
    driver_variables_clear(variables)

    for index, flat_index in enumerate(indices):
        param = variables.new()
        param.type = 'SINGLE_PROP'
        param.name = next(keygen)

        target = param.targets[0]
        target.id_type = object.type
        target.id = object.data
        target.data_path = f'{distance_data_path}[{index}]'

        value = variables.new()
        value.type = 'SINGLE_PROP'
        value.name = next(keygen)

        target = value.targets[0]
        target.id_type = object.type
        target.id = object.data
        target.data_path = f'{variable_data_path}[{flat_index}]'

        tokens.append((param.name, value.name))

    driver.type = 'SCRIPTED'
    driver.expression = "+".join("*".join(token) for token in tokens)


def weight_sum_update(fcurve: FCurve,
                      object: Object,
                      data_path: str,
                      indices: Iterable[int]) -> None:

    driver = fcurve.driver
    driver.type = 'SUM'
    keygen = DriverVariableNameGenerator()

    variables = driver.variables
    driver_variables_clear(driver.variables)

    for index in indices:
        variable = variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = next(keygen)

        target = variable.targets[0]
        target.id_type = object.type
        target.id = object.data
        target.data_path = f'{data_path}[{index}]'


def weight_normalized_update(fcurve: FCurve,
                             object: Object,
                             value_data_path: str,
                             total_data_path: str) -> None:

    driver = fcurve.driver
    driver.type = 'SCRIPTED'
    driver.expression = "value / total if total != 0.0 else value"
    driver_variables_clear(driver.variables)

    for name, data_path in zip(("value", "total"), (value_data_path, total_data_path)):
        variable = driver.variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = name

        target = variable.targets[0]
        target.id_type = object.type
        target.id = object.data
        target.data_path = data_path    


def pose_weight_driver_update(rbfn: 'RBFDriver', pose: 'RBFDriverPose') -> None:
    user = rbfn.id_data
    data = user.data

    poses: 'RBFDriverPoses' = rbfn.poses
    input: 'RBFDriverInput'

    pose_count = len(poses)
    pose_index = poses.find(pose.name)

    distances = []

    for input in filter(input_is_valid, rbfn.inputs):
        propname = f'rbfn_disti_{input.identifier}'
        idprop_ensure(data, propname, pose_count)

        distance = driver_ensure(data, f'["{propname}"]', pose_index)
        distance_measure(distance, input, pose_index)

        # TODO radius should be input.distance.pose_radii[pose_index]*pose.falloff.radius*rbfn.radius
        distance.driver.expression = f'1.0-({distance.driver.expression})/{input.distance.pose_radii[pose_index]}'

        distances.append(distance)

    propname = f'rbfn_dista_{rbfn.identifier}'

    if len(distances) == 0:
        fcurve = driver_ensure(data, idprop_ensure(data, propname, pose_count), pose_index)
        driver = fcurve.driver
        driver.type = 'SCRIPTED'
        driver.expression = "0.0"
        driver_variables_clear(driver.variables)
        pose.weight["name"] = propname
        return

    if len(distances) == 1:
        weight = distances[0]
        idprop_remove(data, propname)
    else:
        weight = driver_ensure(data, idprop_ensure(data, propname, pose_count), pose_index)
        distance_average(weight, user, distances)

    # weight.driver.expression = f'({weight.driver.expression}/{pose.falloff.radius*rbfn.radius})'
    apply_influence(weight, pose.influence)

    points = pose.falloff.curve.points if pose.falloff.use_curve else rbfn.falloff.curve.points

    # if rbfn.smoothing == 'RADIAL':
    #     rangex = (0.0, pose.falloff.radius * rbfn.radius)
    # else: # LINEAR
    #     rangex = (0.0, pose.falloff.radius)

    # points = to_bezier(points, x_range=rangex, y_range=(0.0, 1.0), extrapolate=False)
    # keyframe_points_assign(weight.keyframe_points, points)

    keyframe_points_assign(weight.keyframe_points, to_bezier(points, extrapolate=False))

    propname = f'rbfn_pwgtn_{rbfn.identifier}'
    propnorm = f'rbfn_nwgts_{rbfn.identifier}'

    weight_sum = driver_ensure(data, idprop_ensure(data, propname), 0)
    weight_sum_update(weight_sum, user, weight.data_path, range(pose_count))

    weight_normalized = driver_ensure(data, idprop_ensure(data, propnorm, pose_count), pose_index)
    weight_normalized_update(weight_normalized, user, f'{weight.data_path}[{pose_index}]', f'{weight_sum.data_path}[0]')

    weight = weight_normalized


    propname = f'rbfn_pwgts_{rbfn.identifier}'
    if rbfn.smoothing == 'LINEAR':
        matrix: 'RBFDriverVariableMatrix' = rbfn.variable_matrix
        fcurve = weight
        weight = driver_ensure(data, idprop_ensure(data, propname, pose_count), pose_index)
        weight_solve(weight, user, fcurve.data_path, matrix.data_path, matrix.columns[pose_index].indices)
    else:
        idprop_remove(data, propname)

    pose.weight["name"] = weight.data_path[2:-2]


def pose_weight_driver_update_all(rbfn: 'RBFDriver') -> None:
    pose: 'RBFDriverPose'
    for pose in rbfn.poses:
        pose_weight_driver_update(rbfn, pose)


def pose_weight_driver_remove(rbfn: 'RBFDriver', index: int) -> None:
    id = rbfn.id_data.data

    idprop_splice(id, f'rbfn_nwgts_{rbfn.identifier}', index)
    idprop_splice(id, f'rbfn_pwgtn_{rbfn.identifier}', index)
    idprop_splice(id, f'rbfn_pwgts_{rbfn.identifier}', index)
    idprop_splice(id, f'rbfn_dista_{rbfn.identifier}', index)

    for input in rbfn.inputs:
        idprop_splice(id, f'rbfn_disti_{input.identifier}', index)


def pose_weight_driver_remove_all(rbfn: 'RBFDriver') -> None:
    id = rbfn.id_data.data

    idprop_remove(id, f'rbfn_nwgts_{rbfn.identifier}')
    idprop_remove(id, f'rbfn_pwgtn_{rbfn.identifier}')
    idprop_remove(id, f'rbfn_pwgts_{rbfn.identifier}')
    idprop_remove(id, f'rbfn_dista_{rbfn.identifier}')

    for input in rbfn.inputs:
        idprop_remove(id, f'rbfn_disti_{input.identifier}')


def pose_falloff_radii_update(driver: 'RBFDriver') -> None:
    matrix = driver.distance_matrix.to_array().view(np.ma.MaskedArray)
    matrix.mask = np.identity(len(matrix), dtype=bool)

    pose: 'RBFDriverPose'
    for pose, row in zip(driver.poses, matrix):
        falloff: 'RBFDriverPoseFalloff' = pose.falloff
        if falloff.radius_is_auto_adjusted:
            row = row.compressed()
            falloff["radius"] = 1.0 if len(row) == 0 else np.min(row)


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
    rbfn: 'RBFDriver' = owner_resolve(event.target, ".inputs")
    pose_weight_driver_update_all(rbfn)


@event_handler(InputVariableTypeUpdateEvent)
def on_input_variable_type_update(event: InputVariableTypeUpdateEvent) -> None:
    '''
    Updates pose weight drivers when an input variable type changes. Note that the
    update handlers on the input variable screen invalid update notifications based
    on the input type so no checking is required here.
    '''
    rbfn: 'RBFDriver' = owner_resolve(event.variable, ".inputs")
    pose_weight_driver_update_all(rbfn)


@event_handler(InputDisposableEvent)
def on_input_disposable(event: InputDisposableEvent) -> None:
    '''
    Removes the ID property for an input's distance parameters when the input becomes
    disposable. Note that it is not necessary to update pose weight drivers at this
    point since that will happen when the data manager updates data matrices once the
    input has been removed.
    '''
    idprop_remove(event.input.id_data.data, f'rbfn_disti_{event.input.identifier}')


@event_handler(DriverDistanceMatrixUpdateEvent)
def on_driver_distance_matrix_update(event: DriverDistanceMatrixUpdateEvent) -> None:
    '''
    Updates the pose falloff radii when the driver distance matrix updates.
    Note that the data manager propagates the update from the driver distance matrix
    to the driver variable matrix if the RBF driver's smoothing is linear, so in that
    case pose weight drivers are not updated here, but rather when the update event
    arrives from the driver variable matrix. On the other hand if the RBF driver's
    smoothing is radial the pose weight drivers are updated.

    '''
    rbfn: 'RBFDriver' = owner_resolve(event.matrix, ".")
    pose_falloff_radii_update(rbfn)

    if rbfn.smoothing == 'RADIAL':
        pose_weight_driver_update_all(rbfn)


@event_handler(DriverVariableMatrixUpdateEvent)
def on_driver_variable_matrix_update(event: DriverVariableMatrixUpdateEvent) -> None:
    '''
    Updates the pose weight drivers when the driver variable matrix is updated
    '''
    rbfn: 'RBFDriver' = owner_resolve(event.matrix, ".")
    pose_weight_driver_update_all(rbfn)


@event_handler(PoseFalloffRadiusAdjustEvent)
def on_pose_radius_falloff_adjust(event: PoseFalloffRadiusAdjustEvent) -> None:
    '''
    Adjusts the pose falloff radius when the user requests it
    '''
    pose: 'RBFDriverPose' = owner_resolve(event.falloff, ".")
    rbfn: 'RBFDriver' = owner_resolve(pose, ".poses")

    data = rbfn.distance_matrix.to_array().view(np.ma.MaskedArray)
    data.mask = np.identity(len(data), dtype=bool)

    data = data[rbfn.poses.index(pose)].compressed()
    event.falloff.radius = 1.0 if len(data) == 0 else np.min(data)


@event_handler(PoseNewEvent)
def on_pose_new(event: PoseNewEvent) -> None:
    influence: 'RBFDriverPoseInfluence' = event.pose.influence
    idprop_create(influence.id, influence.name, default=1.0, min=0.0, max=1.0, soft_min=0.0, soft_max=1.0)



@event_handler(PoseNameUpdateEvent)
def on_pose_name_update(event: PoseNameUpdateEvent) -> None:
    '''
    '''
    driver: 'RBFDriver' = owner_resolve(event.pose, ".poses")

    names = [item.name for item in driver.poses if item != event.pose]
    index = 0
    value = event.pose.name

    while value in names:
        index += 1
        value = f'{event.pose.name}.{str(index).zfill(3)}'

    event.pose["name"] = value


@event_handler(PoseDisposableEvent)
def on_pose_disposable(event: PoseDisposableEvent) -> None:
    '''
    Updates ID properties and removes the pose weight driver for a pose when that
    pose becomes disposable. Note that the pose disposable event is dispatched prior
    to the pose removed event, the latter of which will is handled by the input manager
    which propagates the changes through to the data manager, which in turn propagates
    back to the pose manager and results in the pose weight drivers updating.
    '''
    rbfn: 'RBFDriver' = owner_resolve(event.pose, ".poses")
    pose_weight_driver_remove(rbfn, rbfn.poses.index(event.pose))


@event_handler(DriverNewEvent)
def on_driver_new(event: DriverNewEvent) -> None:
    '''
    Adds the rest pose when a new driver is added, or clones poses for symmetrical drivers
    '''
    rbfn = event.driver
    if rbfn.has_symmetry_target:
        #TODO
        raise NotImplementedError()
    else:
        rbfn.poses.new(name="Rest")


@event_handler(DriverDisposableEvent)
def on_driver_disposable(event: DriverDisposableEvent) -> None:
    '''
    Removes all pose weight ID properties and drivers when an RBF driver becomes disposable
    '''
    pose_weight_driver_remove_all(event.driver)


@event_handler(DriverDisposableEvent)
def on_driver_disposable(event: DriverDisposableEvent) -> None:
    '''
    Removes pose weight ID properties and drivers when an RBF driver becomes disposable
    '''
    pose_weight_driver_remove_all(event.driver)
