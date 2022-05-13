
from typing import TYPE_CHECKING, Optional, Sequence
from .events import event_handler
from .utils import owner_resolve
from ..api.input_target import InputTargetBoneTargetUpdateEvent, InputTargetObjectUpdateEvent
from ..api.input_variables import InputVariableNewEvent
from ..api.input import InputBoneTargetUpdateEvent, InputNameUpdateEvent, InputObjectUpdateEvent
from ..api.inputs import InputNewEvent
from ..api.pose import PoseNameUpdateEvent
from ..api.output import OutputBoneTargetChangeEvent, OutputNameUpdateEvent, OutputObjectChangeEvent
from ..api.outputs import OutputNewEvent
from ..api.driver import DriverNameUpdateEvent
from ..api.drivers import DriverNewEvent
if TYPE_CHECKING:
    from ..api.input_target import RBFDriverInputTarget
    from ..api.input_variables import RBFDriverInputVariables
    from ..api.input import RBFDriverInput
    from ..api.output import RBFDriverOutput
    from ..api.driver import RBFDriver

DEFAULT_INPUT_NAMES = {
    'LOCATION'     : "Location",
    'ROTATION'     : "Rotation",
    'SCALE'        : "Scale",
    'LOC_DIFF'     : "Distance",
    'ROTATION_DIFF': "Rotational Difference",
    'SHAPE_KEY'    : "Shape Keys",
    'USER_DEF'     : "Property",
    }

DEFAULT_OUTPUT_NAMES = {
    'LOCATION'     : "Location",
    'ROTATION'     : "Rotation",
    'SCALE'        : "Scale",
    'SHAPE_KEY'    : "Shape Key",
    'SINGLE_PROP'  : "Property"
    }


def uniqname(value: str, names: Sequence[str], separator: Optional[str]=".", zfill: Optional[int]=3) -> str:
    i = 0
    k = value
    while k in names:
        i += 1
        k = f'{value}{separator}{str(i).zfill(zfill)}'
    return k


def difftarget(target: 'RBFDriverInputTarget') -> str:
    object = target.object
    if object is None:
        return "?"
    if object.type == 'ARMATURE' and target.bone_target:
        return target.bone_target
    return object.name


def inputname(input: 'RBFDriverInput') -> str:
    type = input.type

    if type in {'LOCATION', 'ROTATION', 'SCALE'}:
        result = type.title()
        object = input.object
        target = input.bone_target
        if object:
            suffix = target if target and object and object.type == "ARMATURE" else object.name
            result = f'{result} ({suffix})'

    elif type.endswith('DIFF'):
        result = "Distance" if type == 'LOC_DIFF' else "Rotational Difference"
        origin = difftarget(input.variables[0].targets[0])
        target = difftarget(input.variables[0].targets[1])
        result = f'{result} ({origin} - {target})'

    elif type == 'SHAPE_KEY':
        result = "Shape Keys"
        object = input.object
        if object:
            result = f'{result} ({object.name})'

    else:
        driver: 'RBFDriver' = owner_resolve(input, ".inputs")
        result = uniqname("Input", [x.name for x in driver.inputs if x != input])

    return result


def outputname(output: 'RBFDriverOutput') -> str:
    type = output.type

    if type in {'LOCATION', 'ROTATION', 'SCALE'}:
        result = type.title()
        object = output.object
        target = output.bone_target
        if object:
            suffix = target if target and object and object.type == "ARMATURE" else object.name
            result = f'{result} ({suffix})'

    else:
        result = "Shape Key" if type == 'SHAPE_KEY' else "Property"
        object = output.object
        if object:
            result = f'{result} ({object.name})'

    return result


def drivername(driver: 'RBFDriver') -> str:
    if driver.type == 'SHAPE_KEYS':
        return f'Shape Keys ({driver.id_data.name})'
    else:
        return uniqname("Driver", [x.name for x in driver.id_data.rbf_drivers if x != driver])


@event_handler(DriverNewEvent)
def on_driver_new(event: DriverNewEvent) -> None:
    if not event.driver.name:
        event.driver["name"] = drivername(event.driver)


@event_handler(DriverNameUpdateEvent)
def on_driver_name_update(event: DriverNameUpdateEvent) -> None:
    if not event.value:
        event.driver["name"] = drivername(event.driver)


@event_handler(InputNewEvent)
def on_input_new(event: InputNewEvent) -> None:
    type = event.input.type
    if type == 'USER_DEF':
        driver: 'RBFDriver' = owner_resolve(event.input, ".inputs")
        event.input["name"] = uniqname("Input", [x.name for x in driver.inputs if x != input])
    else:
        event.input["name"] = DEFAULT_INPUT_NAMES[event.input.type]


@event_handler(InputNameUpdateEvent)
def on_input_name_update(event: InputNameUpdateEvent) -> None:
    input = event.input
    value = event.value
    if value:
        driver: 'RBFDriver' = owner_resolve(input, ".inputs")
        input["name_is_user_defined"] = True
        input["name"] = uniqname(value, [x.name for x in driver.inputs if x != input])
    else:
        input["name_is_user_defined"] = False
        input["name"] = inputname(input)


@event_handler(InputObjectUpdateEvent)
def on_input_object_update(event: InputObjectUpdateEvent) -> None:
    input = event.input
    if not input.name_is_user_defined and input.type != 'USER_DEF':
        input["name"] = inputname(input)


@event_handler(InputBoneTargetUpdateEvent)
def on_input_bone_target_update(event: InputBoneTargetUpdateEvent) -> None:
    input = event.input
    if not input.name_is_user_defined and input.type != 'USER_DEF':
        input["name"] = inputname(input)


@event_handler(InputTargetObjectUpdateEvent)
def on_input_target_object_update(event: InputTargetObjectUpdateEvent) -> None:
    input: 'RBFDriverInput' = owner_resolve(event.target, ".variables")
    if input.type.endswith('DIFF') and not input.name_is_user_defined:
        input["name"] = inputname(input)


@event_handler(InputTargetBoneTargetUpdateEvent)
def on_input_target_bone_target_update(event: InputTargetBoneTargetUpdateEvent) -> None:
    input: 'RBFDriverInput' = owner_resolve(event.target, ".variables")
    if input.type.endswith('DIFF') and not input.name_is_user_defined:
        input["name"] = inputname(input)


@event_handler(InputVariableNewEvent)
def on_input_variable_new(event: InputVariableNewEvent) -> None:
    variable = event.variable
    if not variable.name:
        variables: 'RBFDriverInputVariables' = owner_resolve(variable, ".")
        variable["name"] = uniqname("var", [x.name for x in variables if x != variable], separator="_", zfill=2)


@event_handler(PoseNameUpdateEvent)
def on_pose_name_update(event: PoseNameUpdateEvent) -> None:
    pose = event.pose
    driver: 'RBFDriver' = owner_resolve(pose, ".poses")
    pose["name"] = uniqname(event.value, [x.name for x in driver.poses if x != pose])


@event_handler(OutputNewEvent)
def on_output_new(event: OutputNewEvent) -> None:
    if event.output.type == 'SHAPE_KEY':
        driver: 'RBFDriver' = owner_resolve(event.output, ".outputs")
        if driver.type == 'SHAPE_KEY':
            event.output["name_is_user_defined"] = True
            return
    event.output["name"] = DEFAULT_OUTPUT_NAMES[event.output.type]


@event_handler(OutputObjectChangeEvent)
def on_output_object_update(event: OutputObjectChangeEvent) -> None:
    output = event.output
    if not output.name_is_user_defined and output.type != 'SINGLE_PROP':
        output["name"] = outputname(output)


@event_handler(OutputBoneTargetChangeEvent)
def on_output_bone_target_update(event: OutputBoneTargetChangeEvent) -> None:
    output = event.output
    if not output.name_is_user_defined and output.type != 'SINGLE_PROP':
        output["name"] = outputname(output)


@event_handler(OutputNameUpdateEvent)
def on_output_name_update(event: OutputNameUpdateEvent) -> None:
    output = event.output
    driver: 'RBFDriver' = owner_resolve(output, ".outputs")

    if driver.type == 'SHAPE_KEY':
        # Use dot notation to trigger OutputChannelNameChangeEvent
        output.channels[0].name = event.value
    elif event.value:
        output["name_is_user_defined"] = True
        output["name"] = uniqname(event.value, [x.name for x in driver.outputs if x != output])
    else:
        output["name_is_user_defined"] = False
        output["name"] = outputname(output)
