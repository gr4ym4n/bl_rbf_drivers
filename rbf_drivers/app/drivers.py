
from typing import Iterable, Sequence, Tuple
from logging import getLogger
from bpy.types import Driver, DriverTarget, DriverVariable, FCurve, Object
from rbf_drivers.api.driver_falloff import RBFDriverFalloff
from rbf_drivers.api.mixins import FloatContainer
from rbf_drivers.lib.curve_mapping import keyframe_points_assign, to_bezier
from ..api.input_target import RBFDriverInputTarget
from ..api.input_variable_data import RBFDriverInputVariableData
from ..api.input_variable import RBFDriverInputVariable, input_variable_is_enabled
from ..api.input import RBFDriverInput
from ..api.driver import RBFDriver
from ..lib.driver_utils import driver_ensure, driver_variables_clear, DriverVariableNameGenerator
from .idprops import INPUT_POSE_DISTANCE, INPUT_POSE_DISTANCE_NORMALIZED, POSE_WEIGHT, POSE_WEIGHT_NORMALIZED, POSE_WEIGHT_SUM, idprop_name_format, idprop_path_format

log = getLogger("rbf_drivers")

# distance -> [average] -> [apply_rbf] -> [solve] -> [normalize] -> [interpolate]


def target_assign__singleprop(target: DriverTarget, properties: RBFDriverInputTarget) -> None:
    target.id_type = properties.id_type
    target.id = properties.id
    target.data_path = properties.data_path


def target_assign__transforms(target: DriverTarget, properties: RBFDriverInputTarget) -> None:
    target.id = properties.object
    target.bone_target = properties.bone_target
    target.transform_type = properties.transform_type
    target.transform_space = properties.transform_space
    target.rotation_mode = properties.rotation_mode


def target_assign__difference(target: DriverTarget, properties: RBFDriverInputTarget) -> None:
    target.id = properties.object
    target.bone_target = properties.bone_target
    target.transform_space = properties.transform_space


def variable_targets_assign(variable: DriverVariable, properties: RBFDriverInputVariable) -> None:
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
        distance_measure__euclidean(driver, tokens)

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


def distance_measure(fcurve: FCurve, input: RBFDriverInput, index: int) -> None:

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

        data = variable.data
        try:
            value = data.value(index, data.is_normalized)
        except IndexError:
            log.warning()
            value = variable.default_value

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
    

def distance_average(fcurve: FCurve,
                     object: Object,
                     inputs: Sequence[FCurve]) -> None:

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


def apply_rbf_kernel(fcurve: FCurve, kernel: str, radius: float) -> None:
    driver = fcurve.driver
    expression = driver.expression

    if kernel == 'GAUSSIAN':
        driver.expression = f'exp(-pow({expression},2.0)/{2.0 * radius * radius})'
    elif kernel == 'QUADRATIC':
        driver.expression = f'sqrt(pow({expression},2.0)+pow({radius},2.0))'


def weight_solve(fcurve: FCurve,
                     object: Object,
                     distance_data_path: str,
                     variable_data_path: str,
                     indices: Iterable[int]) -> None:

    driver = fcurve.driver
    keygen = DriverVariableNameGenerator()
    tokens = []

    for index, flat_index in enumerate(indices):
        param = driver.variables.new()
        param.type = 'SINGLE_PROP'
        param.name = next(keygen)

        target = param.targets[0]
        target.id_type = object.type
        target.id = object.data
        target.data_path = f'{distance_data_path}[{index}]'

        value = driver.variables.new()
        value.type = 'SINGLE_PROP'
        value.name = next(keygen)

        target = param.targets[0]
        target.id_type = object.type
        target.id = object.data
        target.data_path = f'{variable_data_path}[{flat_index}]'

        tokens.append((param.name, value.name))

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
    driver.type = 'MULTIPLY'
    driver_variables_clear(driver.variables)

    for data_path in (value_data_path, total_data_path):
        variable = driver.variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = ""

        target = variable.targets[0]
        target.id_type = object.type
        target.id = object.data
        target.data_path = data_path


def calc_radius(network: RBFDriver, index: int) -> None:
    pose = network.poses[index]
    radius = pose.falloff.radius

    if pose.falloff.radius_is_auto_adjusted:
        radius = radius * network.falloff.radius_factor * pose.falloff.radius_factor

    return radius


def pose_weight_driver_update(network: RBFDriver, index: int) -> None:
    object = network.id_data
    id = object.data
    poses = network.poses
    pose = poses[index]

    distances = []
    for input in network.inputs:
        distance = driver_ensure(id, idprop_path_format(input, INPUT_POSE_DISTANCE), index)
        distance_measure(distance, filter(input_variable_is_enabled, input.variables), index)
        distances.append(distance)

    if len(distances) == 1:
        distance = distances[0]
    else:
        distance = driver_ensure(id, idprop_path_format(network, INPUT_POSE_DISTANCE_NORMALIZED), index)
        distance_average(distance, network.id_data, distances)

    kernel = network.smoothing
    if kernel != 'LINEAR':
        apply_rbf_kernel(distance, kernel, calc_radius(network, index))

    if not network.use_linear_equation_solver:
        weight = distance
    else:
        weight = driver_ensure(id, idprop_path_format(network, POSE_WEIGHT), index)
        weight_solve(weight, object, distance.data_path, network.variable_matrix.columns[index].indices)

    if network.pose_weight_is_normalized:
        weight_sum = driver_ensure(id, idprop_path_format(network, POSE_WEIGHT_SUM))
        weight_sum_update(weight_sum, object, weight.data_path, range(len(poses)))

        weight_normalized = driver_ensure(id, idprop_path_format(network, POSE_WEIGHT_NORMALIZED, index))
        weight_normalized_update(weight_normalized, object, f'{weight.data_path}[{index}]', weight_sum.data_path)

        weight = weight_normalized

    falloff = pose.falloff
    points = falloff.curve.points if falloff.use_curve else network.falloff.curve.points
    keyframe_points_assign(weight.keyframe_points, to_bezier(points, extrapolate=not network.pose_weight_is_clamped))


def on_driver_falloff_updated(driver: RBFDriver, _: RBFDriverFalloff) -> None:
    for index in range(len(driver.poses)):
        pose_weight_driver_update(driver, index)


def on_driver_smoothing_updated(driver: RBFDriver, _: str) -> None:
    for index in range(len(driver.poses)):
        pose_weight_driver_update(driver, index)


def on_driver_pose_weight_is_clamped_updated(driver: RBFDriver, _: bool) -> None:
    for index in range(len(driver.poses)):
        pose_weight_driver_update(driver, index)


def on_driver_pose_weight_is_normalized_updated(driver: RBFDriver, _: bool) -> None:
    for index in range(len(driver.poses)):
        pose_weight_driver_update(driver, index)


def on_driver_use_linear_equation_updated(driver: RBFDriver, _: bool) -> None:
    for index in range(len(driver.poses)):
        pose_weight_driver_update(driver, index)


RBFDriver.handlers.falloff_update.append(on_driver_falloff_updated)
RBFDriver.handlers.pose_weight_is_clamped_update.append(on_driver_pose_weight_is_clamped_updated)
RBFDriver.handlers.pose_weight_is_normalized_update.append(on_driver_pose_weight_is_normalized_updated)
RBFDriver.handlers.smoothing_update.append(on_driver_smoothing_updated)
RBFDriver.handlers.use_linear_equation_solver_update.append(on_driver_use_linear_equation_updated)
