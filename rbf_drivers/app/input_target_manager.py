
from typing import TYPE_CHECKING
from .events import event_handler
from .utils import owner_resolve
from ..lib.transform_utils import TRANSFORM_SPACE_INDEX
from ..api.input_target import (InputTargetBoneTargetUpdateEvent,
                                InputTargetObjectUpdateEvent,
                                InputTargetTransformSpaceUpdateEvent)
from ..api.input_variable import InputVariableNameUpdateEvent, InputVariableTypeUpdateEvent
from ..api.input import INPUT_ROTATION_MODE_INDEX, InputRotationModeChangeEvent
if TYPE_CHECKING:
    from ..api.input import RBFDriverInput


@event_handler(InputTargetBoneTargetUpdateEvent)
def on_input_target_bone_target_updated(event: InputTargetBoneTargetUpdateEvent) -> None:
    '''
    Synchronizes the bone target setting across input targets and updates input target
    data paths for bbone inputs
    '''
    input: 'RBFDriverInput' = owner_resolve(event.target, ".variables")
    value = event.value

    if input.type in {'LOCATION', 'ROTATION', 'SCALE', 'BBONE'}:
        for variable in input.variables:
            variable.targets[0]["bone_target"] = value

    if input.type == 'BBONE':
        for variable in input.variables:
            variable.targets[0]["data_path"] = f'pose.bones["{value}"].{variable.name}'


@event_handler(InputTargetObjectUpdateEvent)
def on_input_target_object_updated(event: InputTargetObjectUpdateEvent) -> None:
    '''
    Synchronizes the target object across input targets
    '''
    input: 'RBFDriverInput' = owner_resolve(event.target, ".variables")
    value = event.value

    if input.type in {'LOCATION', 'ROTATION', 'SCALE', 'BBONE', 'SHAPE_KEY'}:
        for variable in input.variables:
            variable.targets[0]["object"] = value


@event_handler(InputRotationModeChangeEvent)
def on_input_target_rotation_mode_updated(event: InputRotationModeChangeEvent) -> None:
    '''
    Sycnrhonizes the rotation mode across input targets for rotation inputs
    '''
    if event.input.type == 'ROTATION':
        mode = event.value
        if   mode.startswith('SWING') : mode = 'QUATERNION'
        elif mode.startswith('TWIST') : mode = f'SWING_{mode}'
        for variable in event.input.variables:
            variable.targets[0]["rotation_mode"] = INPUT_ROTATION_MODE_INDEX[mode]


@event_handler(InputTargetTransformSpaceUpdateEvent)
def on_input_target_transform_space_update(event: InputTargetTransformSpaceUpdateEvent) -> None:
    '''
    Synchronizes the transform space across input targets for transform inputs
    '''
    input: 'RBFDriverInput' = owner_resolve(event.target, ".variables")
    value = TRANSFORM_SPACE_INDEX[event.value]

    if input.type in {'LOCATION', 'ROTATION', 'SCALE'}:
        for variable in input.variables:
            variable.targets[0]["transform_space"] = value


@event_handler(InputVariableNameUpdateEvent)
def on_input_variable_name_update(event: InputVariableNameUpdateEvent) -> None:
    '''
    Updates a shape key input target's data path according to the input variable's name
    '''
    input: 'RBFDriverInput' = owner_resolve(event.variable, ".variables")
    if input.type == 'SHAPE_KEY':
        event.variable.targets[0]["data_path"] = f'key_blocks["{event.value}"].value'


@event_handler(InputVariableTypeUpdateEvent)
def on_input_variable_type_update(event: InputVariableTypeUpdateEvent) -> None:
    '''
    Ensures the input variable has the correct number of targets
    '''
    if event.variable.type.endswith('DIFF'):
        if len(event.variable.targets) < 2:
            event.variable.targets['length__internal__'] = 2
            event.variable.targets.collection__internal__.add()
    else:
        event.variable.targets["length__internal__"] = 1
