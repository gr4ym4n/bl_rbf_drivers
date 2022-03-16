
from typing import TYPE_CHECKING
from .events import event_handler
from .utils import owner_resolve
from ..api.input_target import (InputTargetBoneTargetUpdateEvent,
                                InputTargetObjectUpdateEvent,
                                InputTargetRotationModeUpdateEvent,
                                InputTargetTransformSpaceUpdateEvent,
                                TRANSFORM_SPACE_INDEX)
if TYPE_CHECKING:
    from ..api.input import RBFDriverInput


@event_handler(InputTargetBoneTargetUpdateEvent)
def on_input_target_bone_target_updated(event: InputTargetBoneTargetUpdateEvent) -> None:

    input: 'RBFDriverInput' = owner_resolve(event.target, ".variables")
    value = event.value

    if input.type in {'LOCATION', 'ROTATION', 'SCALE'}:
        for variable in input.variables:
            variable.targets[0]["bone_target"] = value

    elif input.type == 'BBONE':
        for variable in input.variables:
            variable.targets[0]["data_path"] = f'pose.bones["{value}"].{variable.name}'


@event_handler(InputTargetObjectUpdateEvent)
def on_input_target_object_updated(event: InputTargetObjectUpdateEvent) -> None:

    input: 'RBFDriverInput' = owner_resolve(event.target, ".variables")
    value = event.value

    if input.type in {'LOCATION', 'ROTATION', 'SCALE', 'BBONE', 'SHAPE_KEY'}:
        for variable in input.variables:
            variable.targets[0]["rotation_mode"] = value


@event_handler(InputTargetRotationModeUpdateEvent)
def on_input_target_rotation_mode_updated(event: InputTargetRotationModeUpdateEvent) -> None:

    input: 'RBFDriverInput' = owner_resolve(event.target, ".variables")
    value = event.value

    if input.type == 'ROTATION':
        for variable in input.variables:
            variable.targets[0]["rotation_mode"] = value


@event_handler(InputTargetTransformSpaceUpdateEvent)
def on_input_target_transform_space_updated(event: InputTargetTransformSpaceUpdateEvent) -> None:

    input: 'RBFDriverInput' = owner_resolve(event.target, ".variables")
    value = TRANSFORM_SPACE_INDEX[event.value]

    if input.type in {'LOCATION', 'ROTATION', 'SCALE'}:
        for variable in input.variables:
            variable.targets[0]["transform_space"] = value
