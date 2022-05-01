
#region Imports

import re
from typing import TYPE_CHECKING, Any, Dict, Match, Tuple
from logging import getLogger

from rbf_drivers.lib import rotation_utils
from .utils import owner_resolve
from .events import event_handler
from ..lib.symmetry import symmetrical_target
from ..api.mixins import Symmetrical
from ..api.input_target import (InputTargetBoneTargetUpdateEvent,
                                InputTargetDataPathUpdateEvent,
                                InputTargetObjectUpdateEvent,
                                InputTargetRotationModeUpdateEvent,
                                InputTargetTransformSpaceUpdateEvent,
                                InputTargetTransformTypeUpdateEvent)
from ..api.input_variable_data import InputVariableDataUpdateEvent
from ..api.input_variable import (InputVariableDefaultValueUpdateEvent,
                                  InputVariableIsEnabledUpdateEvent,
                                  InputVariableIsInvertedUpdateEvent,
                                  InputVariableNameUpdateEvent,
                                  InputVariableTypeUpdateEvent)
from ..api.input_variables import InputVariableDisposableEvent, InputVariableNewEvent
from ..api.inputs import InputDisposableEvent, InputNewEvent, InputMoveEvent
from ..api.poses import PoseNewEvent, PoseDisposableEvent
from ..api.output_channel import OutputChannelMuteUpdateEvent
from ..api.output import (OutputBoneTargetChangeEvent,
                          OutputDataPathChangeEvent,
                          OutputIDTypeUpdateEvent,
                          OutputNameUpdateEvent,
                          OutputObjectChangeEvent,
                          OutputRotationModeChangeEvent,
                          OutputUseAxisUpdateEvent,
                          OutputUseLogarithmicMapUpdateEvent)
from ..api.drivers import DriverDisposableEvent
if TYPE_CHECKING:
    from ..api.input_target import RBFDriverInputTarget
    from ..api.input_variable import RBFDriverInputVariable
    from ..api.input import RBFDriverInput
    from ..api.inputs import RBFDriverInputs
    from ..api.pose import RBFDriverPose
    from ..api.output_channel import RBFDriverOutputChannel
    from ..api.output import RBFDriverOutput
    from ..api.driver import RBFDriver

#endregion Imports

log = getLogger("rbf_drivers")


class SymmetryError(Exception):
    pass


class SymmetryLock(Exception):
    pass


def symmetrical_datapath_replace(match: Match):
    value = match.group()
    return symmetrical_target(value) or value


def symmetrical_datapath(path: str) -> str:
    return re.findall(r'\["(.*?)"\]', symmetrical_datapath_replace, path)


def set_attribute(driver: 'RBFDriver', struct: object, name: str, value: Any) -> None:
    driver["symmetry_lock"] = True
    try:
        setattr(struct, name, value)
    finally:
        driver["symmetry_lock"] = False


def call_method(driver: 'RBFDriver', struct: object, name: str, *args: Tuple[Any], **kwargs: Dict[str, Any]) -> Any:
    driver["symmetry_lock"] = True
    try:
        return getattr(struct, name)(*args, **kwargs)
    finally:
        driver["symmetry_lock"] = False


def set_symmetry_target(object: Symmetrical, mirror: Symmetrical) -> None:
    object["symmetry_identifier"] = mirror.identifier
    mirror["symmetry_identifier"] = object.identifier


#region Input Symmetry Utilties
###################################################################################################

def resolve_input_target_mirror(target: 'RBFDriverInputTarget') -> Tuple['RBFDriver', 'RBFDriverInputTarget']:

    variable: 'RBFDriverInputVariable' = owner_resolve(target, ".targets")
    if not variable.has_symmetry_target:
        raise SymmetryError(f'Symmetry target defined for {target} but not for {variable}')

    m_driver, m_variable = resolve_input_variable_mirror(variable)

    m_target = m_variable.targets.search(target.symmetry_identifier)
    if m_target is None:
        raise SymmetryError(f'Search failed for {target} symmetry identifier')

    return m_driver, m_target


def resolve_input_variable_mirror(variable: 'RBFDriverInputVariable') -> Tuple['RBFDriver', 'RBFDriverInputVariable']:

    input: 'RBFDriverInput' = owner_resolve(variable, ".variables")
    if not input.has_symmetry_target:
        raise SymmetryError(f'Symmetry target defined for {variable} but not for {input}')

    m_driver, m_input = resolve_input_mirror(input)

    m_variable = m_input.variables.search(variable.symmetry_identifier)
    if m_variable is None:
        raise SymmetryError(f'Search failed for {variable} symmetry identifier')

    return m_driver, m_variable


def resolve_input_mirror(input: 'RBFDriverInput') -> Tuple['RBFDriver', 'RBFDriverInput']:

    driver: 'RBFDriver' = owner_resolve(input, ".inputs")
    if not driver.has_symmetry_target:
        raise SymmetryError(f'Symmetry target defined for {input} but not for {driver}')

    m_driver = resolve_driver_mirror(driver)

    m_input = m_driver.inputs.search(input.symmetry_identifier)
    if m_input is None:
        raise SymmetryError(f'Search failed for {input} symmetry target')

    return m_driver, m_input

#endregion Input Symmetry Utilities

#region Output Symmetry Utilities
###################################################################################################

def resolve_output_channel_mirror(channel: 'RBFDriverOutputChannel') -> Tuple['RBFDriver', 'RBFDriverOutputChannel']:

    output: 'RBFDriverInput' = owner_resolve(channel, ".channels")
    if not output.has_symmetry_target:
        raise SymmetryError(f'Symmetry target defined for {channel} but not for {output}')

    m_driver, m_output = resolve_input_mirror(output)

    m_channel = m_output.channels.search(channel.symmetry_identifier)
    if m_channel is None:
        raise SymmetryError(f'Search failed for {channel} symmetry identifier')

    return m_driver, m_channel


def resolve_output_mirror(output: 'RBFDriverOutput') -> Tuple['RBFDriver', 'RBFDriverOutput']:
    
    driver: 'RBFDriver' = owner_resolve(output, ".outputs")
    if not driver.has_symmetry_target:
        raise SymmetryError(f'Symmetry target defined for {output} but not for {driver}')

    m_driver = resolve_driver_mirror(driver)

    m_output = m_driver.outputs.search(output.symmetry_identifier)
    if m_output is None:
        raise SymmetryError(f'Search failed for {output} symmetry target')

    return m_driver, m_output

#endregion Output Symmetry Utilities

#region Pose Symmetry Utilities
###################################################################################################

def resolve_pose_mirror(pose: 'RBFDriverPose') -> Tuple['RBFDriver', 'RBFDriverPose']:

    driver: 'RBFDriver' = owner_resolve(pose, ".poses")
    if not driver.has_symmetry_target:
        raise SymmetryError(f'Symmetry target defined for {pose} but not for {driver}')

    m_driver = resolve_driver_mirror(driver)

    m_pose = m_driver.poses.search(pose.symmetry_identifier)
    if m_pose is None:
        raise SymmetryError(f'Search failed for {pose} symmetry identifier')

    return m_driver, m_pose


def resolve_driver_mirror(driver: 'RBFDriver') -> 'RBFDriver':

    if driver["symmetry_lock"]:
        raise SymmetryLock()

    m_driver = driver.id_data.rbf_drivers.search(driver.symmetry_identifier)
    if m_driver is None:
        raise SymmetryError(f'Search failed for {driver} symmetry target')

    return m_driver

#endregion Pose Symmetry Utilities

#region Input Target Event Handlers
###################################################################################################

@event_handler(InputTargetBoneTargetUpdateEvent)
def on_input_target_bone_target_update(event: InputTargetBoneTargetUpdateEvent) -> None:
    if event.target.has_symmetry_target:
        try:
            driver, mirror = resolve_input_target_mirror(event.target)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            value = symmetrical_target(event.value) or event.value
            set_attribute(driver, mirror, "bone_target", value)


@event_handler(InputTargetDataPathUpdateEvent)
def on_input_target_data_path_update(event: InputTargetDataPathUpdateEvent) -> None:
    if event.target.has_symmetry_target:
        try:
            driver, mirror = resolve_input_target_mirror(event.target)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            value = symmetrical_datapath(event.value)
            set_attribute(driver, mirror, "data_path", value)


@event_handler(InputTargetObjectUpdateEvent)
def on_input_target_object_update(event: InputTargetObjectUpdateEvent) -> None:
    if event.target.has_symmetry_target:
        try:
            driver, mirror = resolve_input_target_mirror(event.target)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            value = event.value
            if value is not None:
                name = symmetrical_target(value.name)
                if name:
                    import bpy
                    if name in bpy.data.objects:
                        value = bpy.data.objects[name]
            set_attribute(driver, mirror, "object", value)


@event_handler(InputTargetRotationModeUpdateEvent)
def on_input_target_rotation_mode_update(event: InputTargetRotationModeUpdateEvent) -> None:
    if event.target.has_symmetry_target:
        try:
            driver, mirror = resolve_input_target_mirror(event.target)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            set_attribute(driver, mirror, "rotation_mode", event.value)


@event_handler(InputTargetTransformSpaceUpdateEvent)
def on_input_target_transform_space_update(event: InputTargetTransformSpaceUpdateEvent) -> None:
    if event.target.has_symmetry_target:
        try:
            driver, mirror = resolve_input_target_mirror(event.target)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            set_attribute(driver, mirror, "transform_space", event.value)


@event_handler(InputTargetTransformTypeUpdateEvent)
def on_input_target_transform_type_update(event: InputTargetTransformTypeUpdateEvent) -> None:
    if event.target.has_symmetry_target:
        try:
            driver, mirror = resolve_input_target_mirror(event.target)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            set_attribute(driver, mirror, "transform_type", event.value)

#endregion Input Target Event Handlers

#region Input Variable Event Handlers
###################################################################################################

@event_handler(InputVariableDataUpdateEvent)
def on_input_variable_data_update(event: InputVariableDataUpdateEvent) -> None:
    variable: RBFDriverInputVariable = owner_resolve(event.data, ".")
    if variable.has_symmetry_target:
        try:
            driver, mirror = resolve_input_variable_mirror(variable)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            call_method(driver, mirror, "update")


@event_handler(InputVariableIsEnabledUpdateEvent)
def on_input_variable_is_enabled_update(event: InputVariableIsEnabledUpdateEvent) -> None:
    if event.variable.has_symmetry_target:
        try:
            driver, mirror = resolve_input_variable_mirror(event.variable)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            set_attribute(driver, mirror, "is_enabled", event.value)


@event_handler(InputVariableIsInvertedUpdateEvent)
def on_input_variable_is_inverted_update(event: InputVariableIsInvertedUpdateEvent) -> None:
    # TODO
    raise NotImplementedError("symmetry_manager.on_input_variable_is_inverted_update")


@event_handler(InputVariableNameUpdateEvent)
def on_input_variable_name_update(event: InputVariableNameUpdateEvent) -> None:
    if event.variable.has_symmetry_target:
        try:
            driver, mirror = resolve_input_variable_mirror(event.variable)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            value = symmetrical_target(event.value) or event.value
            set_attribute(driver, mirror, "name", value)


@event_handler(InputVariableDefaultValueUpdateEvent)
def on_input_variable_default_value_update(event: InputVariableDefaultValueUpdateEvent) -> None:
    if event.variable.has_symmetry_target:
        try:
            driver, mirror = resolve_input_variable_mirror(event.variable)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            # TODO invert value if event.variable.is_inverted
            value = event.value
            set_attribute(driver, mirror, "default_value", value)


@event_handler(InputVariableTypeUpdateEvent)
def on_input_variable_type_update(event: InputVariableTypeUpdateEvent) -> None:
    if event.variable.has_symmetry_target:
        try:
            driver, mirror = resolve_input_variable_mirror(event.variable)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            set_attribute(driver, mirror, "type", event.value)

#endregion Input Variable Event Handlers

#region Input Variable Lifecycle Event Handlers
###################################################################################################

@event_handler(InputVariableNewEvent)
def on_input_variable_new(event: InputVariableNewEvent) -> None:
    input: RBFDriverInput = owner_resolve(event.variable, ".variables")
    if input.has_symmetry_target:
        try:
            driver, mirror = resolve_input_mirror(input)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            variable = call_method(driver, mirror.variables, "new")
            set_symmetry_target(event.variable, variable)


@event_handler(InputVariableDisposableEvent)
def on_input_variable_disposable(event: InputVariableDisposableEvent) -> None:
    if event.variable.has_symmetry_target:
        try:
            driver, mirror = resolve_input_variable_mirror(event.variable)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            call_method(driver, driver.variables, "remove", mirror)

#endregion Input Variable Lifecycle Event Handlers

#region Input Lifecycle Event Handlers
###################################################################################################

@event_handler(InputNewEvent)
def on_input_new(event: InputNewEvent) -> None:
    driver: 'RBFDriver' = owner_resolve(event.input, ".inputs")
    if driver.has_symmetry_target:
        try:
            mirror = resolve_driver_mirror(driver)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            input: 'RBFDriverInput' = call_method(mirror, mirror.inputs, "new", event.input.type)
            set_symmetry_target(event.input, input)


@event_handler(InputMoveEvent)
def on_input_move(event: InputMoveEvent) -> None:
    if event.input.has_symmetry_target:
        try:
            driver, mirror = resolve_input_mirror(event.input)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            inputs: 'RBFDriverInputs' = driver.inputs
            call_method(driver, inputs, "move", inputs.index(mirror), event.to_index)


@event_handler(InputDisposableEvent)
def on_input_disposable(event: InputDisposableEvent) -> None:
    if event.input.has_symmetry_target:
        try:
            driver, mirror = resolve_input_mirror(event.input)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            call_method(driver, driver.inputs, "remove", mirror)

#endregion Input Lifecycle Event Handlers

#region Pose Lifecycle Event Handlers
###################################################################################################

@event_handler(PoseNewEvent)
def on_pose_new(event: PoseNewEvent) -> None:
    driver: 'RBFDriver' = owner_resolve(event.pose, ".poses")
    if driver.has_symmetry_target:
        try:
            mirror = resolve_driver_mirror(driver)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            pose = call_method(mirror, mirror.poses, "new", event.pose.name)
            set_symmetry_target(event.pose, pose)


@event_handler(PoseDisposableEvent)
def on_pose_disposable(event: PoseDisposableEvent) -> None:
    if event.pose.has_symmetry_target:
        try:
            driver, mirror = resolve_pose_mirror(event.pose)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            call_method(driver, driver.poses, "remove", mirror)

#endregion Pose Lifecycle Event Handlers

#region Output Channel Event Handlers
###################################################################################################

@event_handler(OutputChannelMuteUpdateEvent)
def on_output_channel_mute_update(event: OutputChannelMuteUpdateEvent) -> None:
    if event.channel.has_symmetry_target:
        try:
            driver, mirror = resolve_output_channel_mirror(event.channel)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            set_attribute(driver, mirror, "mute", event.value)

#endregion Output Channel Event Handlers

#region Output Event Handlers
###################################################################################################

@event_handler(OutputBoneTargetChangeEvent)
def on_output_bone_target_change(event: OutputBoneTargetChangeEvent) -> None:
    if event.output.has_symmetry_target:
        try:
            driver, mirror = resolve_output_mirror(event.output)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            value = symmetrical_target(event.value) or event.value
            set_attribute(driver, mirror, "bone_target", value)


@event_handler(OutputDataPathChangeEvent)
def on_output_data_path_update(event: OutputDataPathChangeEvent) -> None:
    if event.output.has_symmetry_target:
        try:
            driver, mirror = resolve_output_mirror(event.output)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            value = symmetrical_datapath(event.value)
            set_attribute(driver, mirror, "data_path", value)


@event_handler(OutputIDTypeUpdateEvent)
def on_output_id_type_update(event: OutputIDTypeUpdateEvent) -> None:
    if event.output.has_symmetry_target:
        try:
            driver, mirror = resolve_output_mirror(event.output)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            set_attribute(driver, mirror, "id_type", event.value)


def invert_output_values(src_output: 'RBFDriverOutput',
                         tgt_driver: 'RBFDriver',
                         tgt_output: 'RBFDriverOutput',
                         pose_index: int) -> None:
    type = src_output.type
    mode = src_output.rotation_mode

    if type != tgt_output.type or (type == 'ROTATION' and mode != tgt_output.rotation_mode):
        # TODO error message
        raise RuntimeError()

    data = [channel.data[pose_index].value for channel in src_output.channels]

    if type == 'ROTATION':
        if mode == 'EULER':
            data = data[1:]
        else:
            data = getattr(rotation_utils, f'{mode.lower()}_to_euler')(data)

    imap = (src_output.invert_x, src_output.invert_y, src_output.invert_z)
    data = tuple(value * -1 if invert else value for value, invert in zip(data, imap))
    
    if type == 'ROTATION':
        if   mode == 'QUATERNION': data = rotation_utils.euler_to_quaternion(data)
        elif mode == 'AXIS_ANGLE': data = rotation_utils.euler_to_axis_angle(data, True)

    for channel, value in zip(tgt_output.channels, data):
        set_attribute(tgt_driver, channel.data[pose_index], "value", value)


@event_handler(OutputNameUpdateEvent)
def on_output_name_update(event: OutputNameUpdateEvent) -> None:
    if event.output.has_symmetry_target:
        try:
            driver, mirror = resolve_output_mirror(event.output)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            set_attribute(driver, mirror, "name", event.value)


@event_handler(OutputObjectChangeEvent)
def on_output_object_update(event: OutputObjectChangeEvent) -> None:
    if event.output.has_symmetry_target:
        try:
            driver, mirror = resolve_output_mirror(event.output)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            value = event.value
            if value is not None:
                name = symmetrical_target(value.name)
                if name:
                    import bpy
                    if name in bpy.data.objects:
                        value = bpy.data.objects[name]
            set_attribute(driver, mirror, "object", value)


@event_handler(OutputRotationModeChangeEvent)
def on_output_rotation_mode_change(event: OutputRotationModeChangeEvent) -> None:
    if event.output.has_symmetry_target:
        try:
            driver, mirror = resolve_output_mirror(event.output)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            set_attribute(driver, mirror, "rotation_mode", event.value)


@event_handler(OutputUseAxisUpdateEvent)
def on_output_use_axis_update(event: OutputUseAxisUpdateEvent) -> None:
    if event.output.has_symmetry_target:
        try:
            driver, mirror = resolve_output_mirror(event.output)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            set_attribute(driver, mirror, f'use_{event.axis.lower()}', event.value)


@event_handler(OutputUseLogarithmicMapUpdateEvent)
def on_output_use_logarithmic_map_update(event: OutputUseLogarithmicMapUpdateEvent) -> None:
    if event.output.has_symmetry_target:
        try:
            driver, mirror = resolve_output_mirror(event.output)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            set_attribute(driver, mirror, "use_logarithmic_map", event.value)

#endregion Output Event Handlers

@event_handler(DriverDisposableEvent)
def on_driver_disposable(event: DriverDisposableEvent) -> None:
    if event.driver.has_symmetry_target:
        try:
            mirror = resolve_driver_mirror(event.driver)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            call_method(mirror, mirror.id_data.rbf_drivers, "remove", mirror)
