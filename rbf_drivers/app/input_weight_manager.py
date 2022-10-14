
from typing import TYPE_CHECKING, Callable, Sequence, Tuple
from string import ascii_letters
from functools import partial
from .events import dataclass, event_handler, Event
from .input_manager import InputSourcesUpdatedEvent
from .input_data_manager import InputDataInitializedEvent
from .input_radii_manager import INPUT_RADII, InputPoseRadiiInitializedEvent, InputPoseRadiusUpdatedEvent
from ..api.pose_data_ import (
    pose_data_component_driver,
    pose_data_component_fcurve,
    pose_data_container_append,
    pose_data_container_update,
    pose_data_group_remove
    )
from ..api.input_variables import input_variable_is_enabled
from ..api.inputs import InputDisposableEvent
from ..api.poses import PoseNewEvent, PoseRemovedEvent
if TYPE_CHECKING:
    from ..api.pose_data_ import PoseDataComponent
    from ..api.input import Input

INPUT_WEIGHT = "input_pose_weights"


@dataclass
class InputPoseWeightsInitialiazedEvent(Event):
    input: 'Input'


def distance_euclidean(tokens: Sequence[Tuple[str, str]]) -> str:
    return f'sqrt({"+".join("pow("+a+"-"+b+",2.0)" for a, b in tokens)})'


def distance_quaternion(tokens: Sequence[Tuple[str, str]]) -> str:
    return f'acos((2.0*pow(clamp({"+".join(["*".join(x) for x in tokens])},-1.0,1.0),2.0))-1.0)/pi'


def distance_swing(tokens: Sequence[Tuple[str, str]], axis: str) -> str:
    w, x, y, z = tokens
    if axis == 'X':
        a = str(1.0-2.0*(y*y+z*z))
        b = str(2.0*(x*y+w*z))
        c = str(2.0*(x*z-w*y))
        e = f'(asin((1.0-2.0*(y*y+z*z))*{a}+2.0*(x*y+w*z)*{b}+2.0*(x*z-w*y)*{c})-(pi/2.0))/pi'
    elif axis == 'Y':
        a = str(2.0*(x*y-w*z))
        b = str(1.0-2.0*(x*x+z*z))
        c = str(2.0*(y*z+w*x))
        e = f'(asin(2.0*(x*y-w*z)*{a}+(1.0-2.0*(x*x+z*z))*{b}+2.0*(y*z+w*x)*{c})--(pi/2.0))/pi'
    else:
        a = str(2.0*(x*z+w*y))
        b = str(2.0*(y*z-w*x))
        c = str(1.0-2.0*(x*x+y*y))
        e = f'(asin(2.0*(x*z+w*y)*{a}+2.0*(y*z-w*x)*{b}+(1.0-2.0*(x*x+y*y))*{c})--(pi/2.0))/pi'
    return e


def distance_twist(tokens: Sequence[Tuple[str, str]]) -> str:
    return f'fabs({tokens[0][0]}-{str(tokens[0][1])})/pi'


def distance_function(input_: Input) -> Callable[[Sequence[Tuple[str, str]]], str]:
    if input_.type == 'ROTATION':
        mode = input_.rotation_mode
        if mode == 'SWING'      : return partial(distance_swing, axis=input_.rotation_axis)
        if mode == 'TWIST'      : return distance_twist
        if mode == 'QUATERNION' : return distance_quaternion
    return distance_euclidean


def input_pose_weight_driver_update(input_: 'Input', weight: PoseDataComponent) -> None:
    driver = pose_data_component_driver(weight, ensure=True, clear_variables=True)
    inputs = filter(input_variable_is_enabled, input_.variables)
    params = input_.parameters["pose_data"][weight.array_index]
    tokens = []
    offset = 0

    for variable, component in zip(inputs, params):

        current_value = driver.variables.new()
        current_value.type = variable.type
        current_value.name = ascii_letters[offset]

        for target, source in zip(current_value.targets, variable.targets):
            target.id_type = source.id_type
            target.id = source.id
            target.bone_target = source.bone_target
            target.data_path = source.data_path
            target.transform_space = source.transform_space
            target.transform_type = source.transform_type
            target.rotation_mode = source.rotation_mode

        sampled_value = driver.variables.new()
        sampled_value.type = 'SINGLE_PROP'
        sampled_value.name = ascii_letters[offset + 1]

        target = sampled_value.targets[0]
        target.id_type = component.id_type
        target.id = component.id
        target.data_path = component.value_path

        offset += 2
        tokens.append((current_value, sampled_value))

    driver.type = 'SCRIPTED'
    if tokens:
        driver.expression = distance_function(input_)(tokens)
    else:
        driver.expression = "0.0"


def input_pose_weight_fcurve_update(input_: 'Input', weight: 'PoseDataComponent', radius: float) -> None:
    fcurve = pose_data_component_fcurve(weight, ensure=True)
    points = fcurve.keyframe_points
    length = len(points)

    while length > 2:
        points.remove(points[-1])
        length -= 1

    while length < 2:
        points.insert(float(length), 0.0)
        length += 1

    for point in points:
        point.interpolation = 'BEZIER'
        point.easing = 'AUTO'
        point.handle_left_type = 'AUTO_CLAMPED'
        point.handle_right_type = 'AUTO_CLAMPED'

    points[0].co_ui = (0.0, 1.0)
    points[1].co_ui = (radius, 0.0)


def input_pose_weight_dataframe_create(input_: 'Input', pose_count: int) -> None:
    params = input_.parameters.internal__.add()
    params["name"] = INPUT_WEIGHT
    params["id_property_name"] = f'input_{input_.identifier}_pose_weights'
    pose_data_container_update(params, [0.0] * pose_count)


def input_pose_weight_dataframe_delete(input_: 'Input') -> None:
    pose_data_group_remove(input_.parameters, "")


@event_handler(InputDataInitializedEvent)
def on_input_data_initialized(event: InputDataInitializedEvent) -> None:
    input_pose_weight_dataframe_create(event.input, len(event.data))


@event_handler(InputSourcesUpdatedEvent)
def on_input_sources_updated(event: InputSourcesUpdatedEvent) -> None:
    input_ = event.input
    for weight in input_.parameters[INPUT_WEIGHT]:
        input_pose_weight_driver_update(input_, weight)


@event_handler(InputPoseRadiiInitializedEvent)
def on_input_pose_radii_initialized(event: InputPoseRadiiInitializedEvent) -> None:
    input_ = event.input
    params = input_.parameters
    for weight, radius in zip(params[INPUT_WEIGHT], params[INPUT_RADII]):
        input_pose_weight_fcurve_update(input_, weight, radius.value)


@event_handler(InputPoseRadiusUpdatedEvent)
def on_input_pose_radius_update(event: InputPoseRadiusUpdatedEvent) -> None:
    input_ = event.input
    params = input_.parameters[INPUT_WEIGHT][event.index]
    input_pose_weight_fcurve_update(input_, params, event.value)


@event_handler(InputDisposableEvent)
def on_input_disposable(event: InputDisposableEvent) -> None:
    input_pose_weight_dataframe_delete(event.input)


@event_handler(PoseNewEvent)
def on_pose_new(event: PoseNewEvent) -> None:
    for input_ in event.pose.driver.inputs:
        params = input_.parameters
        weight = params[INPUT_WEIGHT].internal__.add()
        radius = params[INPUT_RADII][-1].value
        input_pose_weight_fcurve_update(input_, weight, radius)
        input_pose_weight_driver_update(input_, weight)


@event_handler(PoseRemovedEvent)
def on_pose_removed(event: PoseRemovedEvent) -> None:

