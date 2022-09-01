
from typing import TYPE_CHECKING, Dict, Iterable, List, Optional, Sequence
from logging import getLogger
from .events import event_handler
from .utils import owner_resolve
from ..api.input_targets import InputTargetBoneTargetUpdateEvent, InputTargetObjectUpdateEvent
from ..api.input_variables import InputVariableNewEvent
from ..api.inputs import InputBoneTargetUpdateEvent, InputNameUpdateEvent, InputObjectUpdateEvent
from ..api.inputs import InputNewEvent
from ..api.poses import PoseNameUpdateEvent
from ..api.output_channels import OutputChannelNameChangeEvent
from ..api.output import OutputBoneTargetChangeEvent, OutputNameUpdateEvent, OutputObjectChangeEvent
from ..api.outputs import OutputNewEvent
from ..api.driver import DriverNameUpdateEvent
from ..api.drivers import DriverNewEvent
if TYPE_CHECKING:
    from bpy.types import PropertyGroup
    from ..api.input_targets import InputTarget
    from ..api.input_variables import InputVariables
    from ..api.inputs import Input
    from ..api.output import Output
    from ..api.driver import RBFDriver

log = getLogger(__name__)

DEFAULT_INPUT_NAMES: Dict[str, str] = {
    'LOCATION'     : "Location",
    'ROTATION'     : "Rotation",
    'SCALE'        : "Scale",
    'LOC_DIFF'     : "Distance",
    'ROTATION_DIFF': "Rotational Difference",
    'SHAPE_KEY'    : "Shape Keys",
    'USER_DEF'     : "Property",
    }

DEFAULT_OUTPUT_NAMES: Dict[str, str] = {
    'LOCATION'     : "Location",
    'ROTATION'     : "Rotation",
    'SCALE'        : "Scale",
    'SHAPE_KEY'    : "Shape Key",
    'SINGLE_PROP'  : "Property"
    }


def siblings(item: 'PropertyGroup', collection: Iterable['PropertyGroup']) -> List[str]:
    return [member.name for member in collection if member != item]


def uniqname(value: str,
             names: Sequence[str],
             separator: Optional[str]=".",
             zfill: Optional[int]=3) -> str:
    i = 0
    k = value
    while k in names:
        i += 1
        k = f'{value}{separator}{str(i).zfill(zfill)}'
    return k


def difftarget(target: 'InputTarget') -> str:
    object = target.object
    if object is None:
        return "?"
    if object.type == 'ARMATURE' and target.bone_target:
        return target.bone_target
    return object.name


def inputname(input: 'Input') -> str:
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
        result = uniqname("Input", siblings(input, driver.inputs))

    return result


def outputname(output: 'Output') -> str:
    type = output.type

    if type in {'LOCATION', 'ROTATION', 'SCALE'}:
        result = type.title()
        object = output.object
        target = output.bone_target
        if object:
            suffix = target if target and object and object.type == "ARMATURE" else object.name
            result = f'{result} ({suffix})'

    elif type == 'SHAPE_KEY':
        result = output.channels[0].name or "Shape Key"
        driver: 'RBFDriver' = owner_resolve(output, ".outputs")
        if driver.type !=  'SHAPE_KEY':
            object = output.object
            if object:
                result = f'{result} ({object.name})'

    else:
        result = "Property"
        object = output.object
        if object:
            result = f'{result} ({object.name})'

    return result


def drivername(driver: 'RBFDriver') -> str:
    if driver.type == 'SHAPE_KEYS':
        return f'Shape Keys ({driver.id_data.name})'
    else:
        return uniqname("Driver", siblings(driver, driver.id_data.rbf_drivers))


@event_handler(DriverNewEvent)
def on_driver_new(event: DriverNewEvent) -> None:
    driver = event.driver
    if not driver.name:
        value = drivername(driver)

        log.debug((f'Assigning auto-generated name "{value}" to new '
                   f'{driver} because no name was supplied by the user.'))
        driver["name"] = value


@event_handler(DriverNameUpdateEvent)
def on_driver_name_update(event: DriverNameUpdateEvent) -> None:
    driver = event.driver
    if not event.value:
        value = drivername(driver)
        log.debug((f'Assigning auto-generated name "{value}" to '
                    f'{driver} because user set name to empty string.'))
        driver["name"] = value


@event_handler(InputNewEvent)
def on_input_new(event: InputNewEvent) -> None:
    input = event.input
    type = input.type

    if type == 'USER_DEF':
        driver: 'RBFDriver' = owner_resolve(input, ".inputs")
        value = uniqname("Input", siblings(input, driver.inputs))
    else:
        value = DEFAULT_INPUT_NAMES[input.type]

    log.debug(f'Assigning auto-generated name "{value}" to new {input}')
    input["name"] = value


@event_handler(InputNameUpdateEvent)
def on_input_name_update(event: InputNameUpdateEvent) -> None:
    input = event.input
    value = event.value
    if value:
        driver: 'RBFDriver' = owner_resolve(input, ".inputs")

        log.debug((f'Setting name_is_user_defined to True for {input}'
                   f'because the user set name to non-empty string.'))
        input["name_is_user_defined"] = True

        value = uniqname(value, siblings(input, driver.inputs))
        if value != event.value:
            log.debug((f'Assigning name "{value}" to {input} because '
                       f'user-defined name "{event.value}" was not unique'))
            input["name"] = value
    else:
        value = inputname(input)

        log.debug((f'Setting name_is_user_defined to False for {input}'
                   f'because the user set name to empty string.'))
        input["name_is_user_defined"] = False

        log.debug((f'Assigning auto-generated name "{value}" to '
                   f'{input} because the user set name to empty string.'))
        input["name"] = value


@event_handler(InputObjectUpdateEvent)
def on_input_object_update(event: InputObjectUpdateEvent) -> None:
    input = event.input
    if not input.name_is_user_defined and input.type != 'USER_DEF':
        value = inputname(input)

        log.debug((f'Assigning auto-generated name "{value}" '
                   f'to {input} due to input object property update'))
        input["name"] = value


@event_handler(InputBoneTargetUpdateEvent)
def on_input_bone_target_update(event: InputBoneTargetUpdateEvent) -> None:
    input = event.input
    if not input.name_is_user_defined and input.type != 'USER_DEF':
        value = inputname(input)

        log.debug((f'Assigning auto-generated name "{value}" '
                   f'to {input} due to input bone_target property update'))
        input["name"] = value


@event_handler(InputTargetObjectUpdateEvent)
def on_input_target_object_update(event: InputTargetObjectUpdateEvent) -> None:
    input: 'Input' = owner_resolve(event.target, ".variables")
    if input.type.endswith('DIFF') and not input.name_is_user_defined:
        value = inputname(input)

        log.debug((f'Assigning auto-generated name "{value}" '
                   f'to {input} due to target object property update'))
        input["name"] = value


@event_handler(InputTargetBoneTargetUpdateEvent)
def on_input_target_bone_target_update(event: InputTargetBoneTargetUpdateEvent) -> None:
    input: 'Input' = owner_resolve(event.target, ".variables")
    if input.type.endswith('DIFF') and not input.name_is_user_defined:
        value = inputname(input)
        log.debug((f'Assigning auto-generated name "{value}" '
                   f'to {input} due to target bone_target property update'))
        input["name"] = value


@event_handler(InputVariableNewEvent)
def on_input_variable_new(event: InputVariableNewEvent) -> None:
    variable = event.variable
    if not variable.name:
        variables: 'InputVariables' = owner_resolve(variable, ".")

        value = "var"
        value = uniqname(value, siblings(variable, variables), separator="_", zfill=2)

        log.debug(f'Assigning auto-generated name "{value}" to new {variable}')
        variable["name"] = value


@event_handler(PoseNameUpdateEvent)
def on_pose_name_update(event: PoseNameUpdateEvent) -> None:
    pose = event.pose
    value = uniqname(event.value, siblings(pose, owner_resolve(pose, ".poses").poses))

    if value != event.value:
        log.debug((f'Assigning name "{value}" to {pose} because '
                   f'user-defined name "{event.value}" was not unique'))

        pose["name"] = value


@event_handler(OutputNewEvent)
def on_output_new(event: OutputNewEvent) -> None:
    output = event.output
    driver: 'RBFDriver' = owner_resolve(output, ".outputs")

    if output.type == 'SHAPE_KEY' and driver.type == 'SHAPE_KEY':
        log.debug((f'Setting name_is_user_defined to True on '
                   f'{output} because driver.type == "SHAPE_KEY"'))
        output["name_is_user_defined"] = True
        return

    value = DEFAULT_OUTPUT_NAMES[output.type]
    value = uniqname(value, siblings(output, driver.outputs))

    log.debug((f'Assigning name "{value}" to new output {output}'))
    output["name"] = value


@event_handler(OutputObjectChangeEvent)
def on_output_object_update(event: OutputObjectChangeEvent) -> None:
    output = event.output

    if not output.name_is_user_defined and output.type != 'SINGLE_PROP':
        value = outputname(output)

        log.debug((f'Assigning auto-generated name "{value}" '
                   f'to {output} due to object property update'))
        output["name"] = value


@event_handler(OutputBoneTargetChangeEvent)
def on_output_bone_target_update(event: OutputBoneTargetChangeEvent) -> None:
    output = event.output
    if not output.name_is_user_defined and output.type != 'SINGLE_PROP':
        value = outputname(output)

        log.debug((f'Assigning auto-generated name "{value}" '
                   f'to {output} due to bone_target property update'))
        output["name"] = value


@event_handler(OutputNameUpdateEvent)
def on_output_name_update(event: OutputNameUpdateEvent) -> None:
    output = event.output
    driver: 'RBFDriver' = owner_resolve(output, ".outputs")

    if event.value:
        log.debug((f'Setting name_is_user_defined to True for {output}'
                   f'because the user set name to non-empty string.'))
        output["name_is_user_defined"] = True

        cache = event.value
        value = uniqname(cache, siblings(output, driver.outputs))

        if value != cache:
            log.debug((f'Assigning name "{value}" to {output} because '
                       f'user-defined name "{cache}" was not unique'))
            output["name"] = value
    else:
        value = outputname(output)

        log.debug((f'Setting name_is_user_defined to False for {output}'
                   f'because the user set name to empty string.'))
        output["name_is_user_defined"] = False

        log.debug((f'Assigning auto-generated name "{value}" to '
                   f'{output} because the user set name to empty string.'))
        output["name"] = value


@event_handler(OutputChannelNameChangeEvent)
def on_output_channel_name_change(event: OutputChannelNameChangeEvent) -> None:
    output: 'Output' = owner_resolve(event.channel, ".channels")

    if output.type == 'SHAPE_KEY' and not output.name_is_user_defined:
        value = outputname(output)

        log.debug((f'Assigning auto-generated name "{value}" '
                   f'to {output} due to channel name property '
                   f'update because output.type is "SHAPE_KEY"'))
        output["name"] = value
