
#region Imports
###################################################################################################

import re
import numpy as np
from typing import TYPE_CHECKING, Any, Dict, Match, Optional, Tuple, Union
from logging import getLogger
from .utils import owner_resolve
from .events import event_handler
from ..lib import rotation_utils
from ..lib.symmetry import symmetrical_target
from ..api.mixins import Symmetrical
from ..api.input_targets import (InputTargetBoneTargetUpdateEvent,
                                InputTargetDataPathUpdateEvent,
                                InputTargetObjectUpdateEvent,
                                InputTargetRotationModeUpdateEvent,
                                InputTargetTransformSpaceUpdateEvent,
                                InputTargetTransformTypeUpdateEvent)
from ..api.input_sample import InputSampleUpdateEvent
from ..api.input_data import InputDataUpdateEvent, InputData
from ..api.input_variables import (InputVariableIsEnabledUpdateEvent,
                                  InputVariableNameUpdateEvent,
                                  InputVariableTypeUpdateEvent)
from ..api.input_variables import InputVariableDisposableEvent, InputVariableNewEvent
from ..api.inputs import (InputBoneTargetUpdateEvent,
                         InputNameUpdateEvent,
                         InputDataTypeUpdateEvent,
                         InputObjectUpdateEvent,
                         InputRotationAxisUpdateEvent,
                         InputRotationModeChangeEvent,
                         InputTransformSpaceChangeEvent,
                         InputUseMirrorXUpdateEvent,
                         InputUseSwingUpdateEvent)
from ..api.inputs import InputDisposableEvent, InputNewEvent, InputMoveEvent
from ..api.pose_interpolation import PoseInterpolationUpdateEvent
from ..api.poses import PoseNewEvent, PoseDisposableEvent
from ..api.output_data import OutputSampleUpdateEvent
from ..api.output_channels import OutputChannelMuteUpdateEvent
from ..api.output import (OutputBoneTargetChangeEvent,
                          OutputDataPathChangeEvent,
                          OutputIDTypeUpdateEvent,
                          OutputNameUpdateEvent,
                          OutputObjectChangeEvent,
                          OutputRotationModeChangeEvent,
                          OutputUseAxisUpdateEvent,
                          OutputUseMirrorXUpdateEvent,
                          OutputUseLogarithmicMapUpdateEvent)
from ..api.driver_interpolation import DriverInterpolationUpdateEvent
from ..api.drivers import DriverNewEvent, DriverDisposableEvent
from ..app.output_channel_driver_manager import output_activate, output_assign_channel_data_targets
from ..app.pose_weight_driver_manager import pose_weight_drivers_update
from ..app.property_manager import output_idprops_create, pose_idprops_create
if TYPE_CHECKING:
    from ..api.input_targets import InputTarget
    from ..api.input_sample import InputSample
    from ..api.input_variables import InputVariable
    from ..api.inputs import Input
    from ..api.inputs import Inputs
    from ..api.pose_interpolation import RBFDriverPoseInterpolation
    from ..api.poses import Pose
    from ..api.output_data import OutputSample
    from ..api.output_channel_data import OutputData
    from ..api.output_channels import OutputChannel
    from ..api.output import Output
    from ..api.driver_interpolation import RBFDriverInterpolation
    from ..api.driver import RBFDriver

#endregion Imports

#region Core
###################################################################################################

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

#endregion Core

#region Interpolation Symmetry Utilties
###################################################################################################

def get_interpolation_curve_options(manager: Union['RBFDriverInterpolation',
                                                   'RBFDriverPoseInterpolation']) -> Dict[str, Any]:
    options = {
        "curve_type": manager.curve_type,
        "easing": manager.easing,
        "ramp": manager.ramp,
        }
    if manager.interpolation == 'CURVE':
        options["curve"] = manager.curve
    else:
        options["interpolation"] = manager.interpolation
    return options

#endregion Interpolation Symmetry Utilties

#region Input Symmetry Utilties
###################################################################################################

def resolve_input_target_mirror(target: 'InputTarget') -> Tuple['RBFDriver', 'InputTarget']:

    variable: 'InputVariable' = owner_resolve(target, ".targets")
    if not variable.has_symmetry_target:
        raise SymmetryError(f'Symmetry target defined for {target} but not for {variable}')

    m_driver, m_variable = resolve_input_variable_mirror(variable)

    m_target = m_variable.targets.search(target.symmetry_identifier)
    if m_target is None:
        raise SymmetryError(f'Search failed for {target} symmetry identifier')

    return m_driver, m_target


def resolve_input_variable_mirror(variable: 'InputVariable') -> Tuple['RBFDriver', 'InputVariable']:

    input: 'Input' = owner_resolve(variable, ".variables")
    if not input.has_symmetry_target:
        raise SymmetryError(f'Symmetry target defined for {variable} but not for {input}')

    m_driver, m_input = resolve_input_mirror(input)

    m_variable = m_input.variables.search(variable.symmetry_identifier)
    if m_variable is None:
        raise SymmetryError(f'Search failed for {variable} symmetry identifier')

    return m_driver, m_variable


def resolve_input_mirror(input: 'Input') -> Tuple['RBFDriver', 'Input']:

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

def resolve_output_channel_mirror(channel: 'OutputChannel') -> Tuple['RBFDriver', 'OutputChannel']:

    output: 'Input' = owner_resolve(channel, ".channels")
    if not output.has_symmetry_target:
        raise SymmetryError(f'Symmetry target defined for {channel} but not for {output}')

    m_driver, m_output = resolve_input_mirror(output)

    m_channel = m_output.channels.search(channel.symmetry_identifier)
    if m_channel is None:
        raise SymmetryError(f'Search failed for {channel} symmetry identifier')

    return m_driver, m_channel


def resolve_output_mirror(output: 'Output') -> Tuple['RBFDriver', 'Output']:
    
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

def resolve_pose_mirror(pose: 'Pose') -> Tuple['RBFDriver', 'Pose']:

    driver: 'RBFDriver' = owner_resolve(pose, ".poses")
    if not driver.has_symmetry_target:
        raise SymmetryError(f'Symmetry target defined for {pose} but not for {driver}')

    m_driver = resolve_driver_mirror(driver)

    m_pose = m_driver.poses.search(pose.symmetry_identifier)
    if m_pose is None:
        raise SymmetryError(f'Search failed for {pose} symmetry identifier')

    return m_driver, m_pose


def resolve_driver_mirror(driver: 'RBFDriver') -> 'RBFDriver':

    if driver.symmetry_lock:
        raise SymmetryLock()

    m_driver = driver.id_data.rbf_drivers.search(driver.symmetry_identifier)
    if m_driver is None:
        raise SymmetryError(f'Search failed for {driver} symmetry target')

    return m_driver

#endregion Pose Symmetry Utilities

#region Cloning Utilities
###################################################################################################

def driver_interpolation_clone(symsrc: 'RBFDriverInterpolation', symtgt: 'RBFDriverInterpolation') -> None:
    symtgt.__init__(**get_interpolation_curve_options(symsrc))


def pose_interpolation_clone(symsrc: 'RBFDriverPoseInterpolation', symtgt: 'RBFDriverPoseInterpolation') -> None:
    symsrc["use_curve"] = symtgt.use_curve
    symtgt.__init__(**get_interpolation_curve_options(symsrc))


def input_target_clone(symsrc: 'InputTarget', symtgt: 'InputTarget') -> None:
    set_symmetry_target(symsrc, symtgt)

    for propname in ("id_type", "rotation_mode", "transform_space", "transform_type"):
        if symsrc.is_property_set(propname):
            symtgt[propname] = symsrc[propname]

    if symsrc.is_property_set("object"):
        value = symsrc.object
        if value is not None:
            name = symmetrical_target(value.name)
            if name:
                import bpy
                if name in bpy.data.objects:
                    value = bpy.data.objects[name]
        symtgt["object"] = value

    if symsrc.is_property_set("bone_target"):
        value = symsrc.bone_target
        symtgt["bone_target"] = symmetrical_target(value) or value

    if symsrc.is_property_set("data_path"):
        value = symsrc.data_path
        symtgt["bone_target"] = symmetrical_datapath(value)


def input_targets_clone(symsrc: 'Inputs', symtgt: 'Inputs') -> None:
    symtgt["length__internal__"] = symsrc["length__internal__"]
    for target in symsrc.internal__:
        input_target_clone(target, symtgt.internal__.add())


def input_variable_data_sample_clone(symsrc: 'InputSample', symtgt: 'InputSample') -> None:
    symtgt["index"] = symsrc.index
    symtgt["value"] = symsrc.value
    if symsrc.is_property_set("value_normalized"):
        symtgt["value_normalized"] = symsrc.value_normalized


def input_variable_data_clone(symsrc: 'InputData', symtgt: 'InputData') -> None:
    for propname in ("is_normalized", "norm"):
        if symsrc.is_property_set(propname):
            symtgt[propname] = symsrc[propname]

    for sample in symsrc.samples:
        input_variable_data_sample_clone(sample, symtgt.internal__.add())


def input_variable_clone(symsrc: 'InputVariable',
                         symtgt: 'InputVariable',
                         is_key: Optional[bool]=False) -> None:
    set_symmetry_target(symtgt, symsrc)

    for propname in ("type", "name", "default_value", "is_enabled"):
        if symsrc.is_property_set(propname):
            symtgt[propname] = symsrc[propname]

    if is_key:
        value = symsrc.name
        symtgt["name"] = symmetrical_target(value) or value
    else:
        symtgt["name"] = symsrc.name

    input_targets_clone(symsrc.targets, symtgt.targets)
    input_variable_data_clone(symsrc.data, symtgt.data)


def input_clone(symsrc: 'Input', symtgt: 'Input') -> None:
    set_symmetry_target(symtgt, symsrc)

    for propname in ("type",
                     "data_type",
                     "name",
                     "name_is_user_defined",
                     "rotation_axis",
                     "rotation_mode",
                     "rotation_order",
                     "transform_space",
                     "use_mirror_x",
                     "use_swing"):
        if symsrc.is_property_set(propname):
            symtgt[propname] = symsrc[propname]

    if symsrc.is_property_set("object"):
        value = symsrc.object
        if value is not None:
            name = symmetrical_target(value.name)
            if name:
                import bpy
                if name in bpy.data.objects:
                    value = bpy.data.objects[name]
        symtgt["object"] = value

    if symsrc.is_property_set("bone_target"):
        value = symsrc.bone_target
        symtgt["bone_target"] = symmetrical_target(value) or value

    is_key = symsrc.type == 'SHAPE_KEY'

    for variable in symsrc.variables:
        input_variable_clone(variable, symtgt.variables.internal__.add(), is_key)

    if symtgt.type == 'LOCATION' and symtgt.use_mirror_x:
        for sample in symtgt.variables[0].data:
            sample["value"] = sample.value * -1

    elif symtgt.type == 'ROTATION' and symtgt.use_mirror_x:
        mode = symtgt.rotation_mode
        data = np.array([var.data.values() for var in symtgt.variables], dtype=float)

        if mode == 'EULER':
            for column in data.T:
                column[:] = rotation_utils.euler_to_quaternion(column[1:])
        elif mode == 'TWIST':
            axis = symtgt.rotation_axis
            for column in data.T:
                column[:] = rotation_utils.swing_twist_to_quaternion(column, axis)

        data[2] *= -1
        data[3] *= -1
        
        if mode == 'EULER':
            order = symtgt.rotation_order
            for column in data.T:
                column[1:] = rotation_utils.quaternion_to_euler(column, order)
                column[0] = 0.0
        elif mode == 'TWIST':
            axis = symtgt.rotation_axis
            for column in data.T:
                column[:] = rotation_utils.quaternion_to_swing_twist(column, axis, True)

        for variable, values in zip(symtgt.variables, data):
            variable.data.__init__(values)


def output_channel_data_sample_clone(symsrc: 'OutputSample', symtgt: 'OutputSample') -> None:
    symtgt["index"] = symsrc.index
    symtgt["value"] = symsrc.value


def output_channel_data_clone(symsrc: 'OutputData', symtgt: 'OutputData') -> None:
    for sample in symsrc.samples:
        output_channel_data_sample_clone(sample, symtgt.internal__.add())


def output_channel_clone(symsrc: 'OutputChannel', symtgt: 'OutputChannel', name: Optional[str]="") -> None:
    set_symmetry_target(symtgt, symsrc)

    symtgt["name"] = name or symsrc.name
    for propname in ("default_value", "is_enabled", "mute"):
        if symsrc.is_property_set(propname):
            symtgt[propname] = symsrc[propname]

    output_channel_data_clone(symsrc.data, symtgt.data)


def output_clone(symsrc: 'Output', symtgt: 'Output') -> None:
    output_idprops_create(symtgt)
    set_symmetry_target(symsrc, symtgt)

    for propname in ("type",
                     "name_is_user_defined",
                     "rotation_mode",
                     "rotation_mode_is_user_defined",
                     "use_x",
                     "use_y",
                     "use_z",
                     "use_mirror_x",
                     "use_logarithmic_map"):
        if symsrc.is_property_set(propname):
            symtgt[propname] = symsrc[propname]

    if symsrc.is_property_set("object__internal__"):
        value = symsrc.object__internal__
        if value is not None:
            name = symmetrical_target(value.name)
            if name:
                import bpy
                if name in bpy.data.objects:
                    value = bpy.data.objects[name]
        symtgt["object"] = value
        symtgt["object__internal__"] = value
        id = symsrc.id
        if id:
            for channel in symtgt.channels:
                channel.id__internal__ = id

    if symsrc.is_property_set("bone_target"):
        value = symsrc.bone_target
        symtgt["bone_target"] = symmetrical_target(value) or value

    if symsrc.type == 'SHAPE_KEY':
        name = symsrc.name
        name = symmetrical_target(name) or name
        symtgt["name"] = name
        output_channel_clone(symsrc.channels[0], symtgt.channels.internal__.add(), name=name)
    else:
        for channel in symsrc.channels:
            output_channel_clone(channel, symtgt.channels.internal__.add())

    if symtgt.type == 'LOCATION' and symtgt.use_mirror_x:
        for sample in symtgt.channels[0].data:
            sample["value"] = sample.value * -1

    elif symtgt.type == 'ROTATION' and symtgt.use_mirror_x:
        mode = symtgt.rotation_mode
        data = np.array([ch.data.values() for ch in symtgt.channels], dtype=float)

        if mode == 'EULER':
            for column in data.T:
                column[:] = rotation_utils.euler_to_quaternion(column[1:])
        elif mode == 'AXIS_ANGLE':
            for column in data.T:
                column[:] = rotation_utils.axis_angle_to_quaternion(column)

        data[2] *= -1
        data[3] *= -1
        
        if mode == 'EULER':
            for column in data.T:
                column[1:] = rotation_utils.quaternion_to_euler(column)
                column[0] = 0.0
        elif mode == 'AXIS_ANGLE':
            for column in data.T:
                column[:] = rotation_utils.quaternion_to_axis_angle(column, True)

        for channel, values in zip(symtgt.channels, data):
            channel.data.__init__(values)
    
    output_assign_channel_data_targets(symtgt)


def pose_clone(symsrc: 'Pose', symtgt: 'Pose') -> None:
    pose_idprops_create(symtgt)
    set_symmetry_target(symsrc, symtgt)
    pose_interpolation_clone(symsrc.interpolation, symtgt.interpolation)
    symtgt["name"] = symsrc.name


def driver_clone(symsrc: 'RBFDriver', symtgt: 'RBFDriver') -> None:

    driver_interpolation_clone(symsrc.interpolation, symtgt.interpolation)

    for input in symsrc.inputs:
        input_clone(input, symtgt.inputs.internal__.add())

    symtgt.inputs.active_index = symsrc.inputs.active_index

    for output in symsrc.outputs:
        output_clone(output, symtgt.outputs.internal__.add())

    symtgt.outputs.active_index = symsrc.outputs.active_index

    for pose in symsrc.poses:
        pose_clone(pose, symtgt.poses.internal__.add())

    symtgt.poses.active_index = symsrc.poses.active_index

    pose_weight_drivers_update(symtgt)

    for output in symtgt.outputs:
        if output.is_valid:
            output_activate(output)

#endregion Cloning Utilities

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

@event_handler(InputSampleUpdateEvent)
def on_input_variable_data_sample_update(event: InputSampleUpdateEvent) -> None:
    variable: InputVariable = owner_resolve(event.sample, ".data.")
    if variable.has_symmetry_target:

        index = event.sample.index
        input: 'Input' = owner_resolve(variable, ".variables")
        
        if input.type == 'ROTATION' and input.use_mirror_x:
            try:
                driver, mirror = resolve_input_mirror(input)
            except SymmetryLock:
                return
            except SymmetryError as error:
                log.error(error.message)
            else:
                mode = input.rotation_mode
                data = [var.data[index].value for var in input.variables]

                if   mode == 'EULER': data = rotation_utils.euler_to_quaternion(data[1:])
                elif mode == 'TWIST': data = rotation_utils.swing_twist_to_quaternion(data, input.rotation_axis)

                data = [data[0], data[1], -data[2], -data[3]]
                
                if   mode == 'EULER': data = [0.0] + list(rotation_utils.quaternion_to_euler(data, input.rotation_order))
                elif mode == 'TWIST': data = rotation_utils.quaternion_to_swing_twist(data, input.rotation_axis, True)

                for variable, value in zip(mirror.variables, data):
                    data: 'InputData' = variable.data
                    data[index]["value"] = value
                    data.update(propagate=False)
                
                pose_weight_drivers_update(driver)
            return

        try:
            driver, mirror = resolve_input_variable_mirror(variable)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            value = event.value
            if (input.type == 'LOCATION'
                and input.use_mirror_x
                and input.variables.index(variable) == 0):
                value *= -1
            set_attribute(driver, mirror.data[index], "value", value)


@event_handler(InputDataUpdateEvent)
def on_input_variable_data_update(event: InputDataUpdateEvent) -> None:
    variable: InputVariable = owner_resolve(event.data, ".")
    if variable.has_symmetry_target:
        try:
            driver, mirror = resolve_input_variable_mirror(variable)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            call_method(driver, mirror.data, "update")


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
    input: Input = owner_resolve(event.variable, ".variables")
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
            input: 'Input' = call_method(mirror, mirror.inputs, "new", event.input.type)
            set_symmetry_target(event.input, input)
            for symsrc, symtgt in zip(event.input.variables, input.variables):
                set_symmetry_target(symsrc, symtgt)
                for symsrc, symtgt in zip(symsrc.targets.internal__, symtgt.targets.internal__):
                    set_symmetry_target(symsrc, symtgt)


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
            inputs: 'Inputs' = driver.inputs
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

#region Input Event Handlers
###################################################################################################

@event_handler(InputBoneTargetUpdateEvent)
def on_input_bone_target(event: InputBoneTargetUpdateEvent) -> None:
    if event.input.has_symmetry_target:
        try:
            driver, mirror = resolve_input_mirror(event.input)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            value = symmetrical_target(event.value) or event.value
            set_attribute(driver, mirror, "bone_target", value)


@event_handler(InputNameUpdateEvent)
def on_input_name_update(event: InputNameUpdateEvent) -> None:
    if event.input.has_symmetry_target:
        try:
            driver, mirror = resolve_input_mirror(event.input)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            value = event.value
            if event.input.type == 'SHAPE_KEY':
                value = symmetrical_target(value) or value
            set_attribute(driver, mirror, "name", value)


@event_handler(InputDataTypeUpdateEvent)
def on_input_data_type_update(event: InputDataTypeUpdateEvent) -> None:
    if event.input.has_symmetry_target:
        try:
            driver, mirror = resolve_input_mirror(event.input)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            set_attribute(driver, mirror, "data_type", event.value)


@event_handler(InputObjectUpdateEvent)
def on_input_object_update(event: InputObjectUpdateEvent) -> None:
    if event.input.has_symmetry_target:
        try:
            driver, mirror = resolve_input_mirror(event.input)
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


@event_handler(InputRotationAxisUpdateEvent)
def on_input_rotation_axis_update(event: InputRotationAxisUpdateEvent) -> None:
    if event.input.has_symmetry_target:
        try:
            driver, mirror = resolve_input_mirror(event.input)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            set_attribute(driver, mirror, "rotation_axis", event.value)


@event_handler(InputRotationModeChangeEvent)
def on_input_rotation_mode_change(event: InputRotationModeChangeEvent) -> None:
    if event.input.has_symmetry_target:
        try:
            driver, mirror = resolve_input_mirror(event.input)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            set_attribute(driver, mirror, "rotation_mode", event.value)


@event_handler(InputTransformSpaceChangeEvent)
def on_input_transform_space_change(event: InputTransformSpaceChangeEvent) -> None:
    if event.input.has_symmetry_target:
        try:
            driver, mirror = resolve_input_mirror(event.input)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            set_attribute(driver, mirror, "transform_space", event.value)


@event_handler(InputUseMirrorXUpdateEvent)
def on_input_use_mirror_x_update(event: InputUseMirrorXUpdateEvent) -> None:
    if event.input.has_symmetry_target:
        try:
            driver, mirror = resolve_input_mirror(event.input)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            set_attribute(driver, mirror, "use_mirror_x", event.value)


@event_handler(InputUseSwingUpdateEvent)
def on_input_use_swing_update(event: InputUseSwingUpdateEvent) -> None:
    if event.input.has_symmetry_target:
        try:
            driver, mirror = resolve_input_mirror(event.input)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            set_attribute(driver, mirror, "use_swing", event.value)

#endregion Input Event Handlers

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

#region Pose Interpolation Event Handlers
###################################################################################################

@event_handler(PoseInterpolationUpdateEvent)
def on_pose_interpolation_update(event: PoseInterpolationUpdateEvent) -> None:
    pose: 'Pose' = owner_resolve(event.interpolation, ".")
    if pose.has_symmetry_target:
        try:
            driver, mirror = resolve_pose_mirror(pose)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            options = get_interpolation_curve_options(event.interpolation)
            call_method(driver, mirror.interpolation, "__init__", **options)

#endregion Pose Interpolation Event Handlers

#region Output Channel Event Handlers
###################################################################################################

@event_handler(OutputSampleUpdateEvent)
def on_output_channel_data_sample_update(event: OutputSampleUpdateEvent) -> None:
    channel: 'OutputChannel' = owner_resolve(event.sample, ".data.")
    if channel.has_symmetry_target:
        index = event.sample.index
        output: 'Output' = owner_resolve(channel, ".channels")

        if output.type == 'ROTATION' and output.use_mirror_x:
            try:
                driver, mirror = resolve_output_mirror(output)
            except SymmetryLock:
                return
            except SymmetryError as error:
                log.error(error.message)
            else:
                mode = output.rotation_mode
                data = [ch.data[index].value for ch in output.channels]

                if   mode == 'EULER'     : data = rotation_utils.euler_to_quaternion(data[1:])
                elif mode == 'AXIS_ANGLE': data = rotation_utils.axis_angle_to_quaternion(data)

                data = [data[0], data[1], -data[2], -data[3]]

                if   mode == 'EULER'     : data = [0.0] + list(rotation_utils.quaternion_to_euler(data))
                elif mode == 'AXIS_ANGLE': data = rotation_utils.quaternion_to_axis_angle(data, vectorize=True)

                for channel, value in zip(mirror.channels, data):
                    channel.data[index]["value"] = value

                if mirror.is_valid:
                    output_activate(mirror)
            return
        
        try:
            driver, mirror = resolve_output_channel_mirror(channel)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            value = event.value
            if (output.type == 'LOCATION'
                and output.use_mirror_x
                and output.channels.index(channel) == 0):
                value *= -1
            set_attribute(driver, mirror.data[index], "value", value)

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


@event_handler(OutputUseMirrorXUpdateEvent)
def on_output_use_mirror_x_update(event: OutputUseMirrorXUpdateEvent) -> None:
    if event.output.has_symmetry_target:
        try:
            driver, mirror = resolve_output_mirror(event.output)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            set_attribute(driver, mirror, "use_mirror_x", event.value)


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

#region Driver Lifecycle Event Handlers
###################################################################################################

@event_handler(DriverNewEvent)
def on_driver_new(event: DriverNewEvent) -> None:
    symtgt = event.driver
    if symtgt.has_symmetry_target:
        symsrc = symtgt.id_data.rbf_drivers.search(symtgt.symmetry_identifier)

        # Given that checks against the mirror are handled with RBFDrivers.new() we shouldn't
        # ever get to this exception.
        if symsrc is None:
            raise RuntimeError(f'{symtgt} symmetry target not found.')

        driver_clone(symsrc, symtgt)


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

#endregion Driver Lifecycle Event Handlers

#region Driver Interpolation Event Handlers
###################################################################################################

@event_handler(DriverInterpolationUpdateEvent)
def on_driver_interpolation_update(event: DriverInterpolationUpdateEvent) -> None:
    driver: 'RBFDriver' = owner_resolve(event.interpolation, ".")
    if driver.has_symmetry_target:
        try:
            mirror = resolve_driver_mirror(driver)
        except SymmetryLock:
            return
        except SymmetryError as error:
            log.error(error.message)
        else:
            options = get_interpolation_curve_options(event.interpolation)
            call_method(driver, mirror.interpolation, "__init__", **options)

#endregion Driver Interpolation Event Handlers