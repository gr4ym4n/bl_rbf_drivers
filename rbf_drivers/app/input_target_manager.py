
from itertools import chain
from operator import attrgetter
from typing import TYPE_CHECKING, Iterator
from .input_initialization_manager import input_variable_data_init
from .events import event_handler
from .utils import owner_resolve
from ..api.input_target import INPUT_TARGET_ID_TYPE_TABLE
from ..api.input_variable import InputVariableNameUpdateEvent, InputVariableTypeUpdateEvent
from ..api.input_variables import InputVariableNewEvent
from ..api.input import (InputBoneTargetUpdateEvent,
                         InputObjectUpdateEvent,
                         InputRotationAxisUpdateEvent,
                         InputRotationModeChangeEvent,
                         InputTransformSpaceChangeEvent)
from ..lib.transform_utils import ROTATION_MODE_TABLE, TRANSFORM_SPACE_TABLE
if TYPE_CHECKING:
    from ..api.input_target import InputTarget
    from ..api.input import Input
    from ..api.driver import RBFDriver


targets = attrgetter("targets")


def targets_chain(input: 'Input') -> Iterator['InputTarget']:
    return chain(*tuple(map(targets, input.variables)))


@event_handler(InputObjectUpdateEvent)
def on_input_object_update(event: InputObjectUpdateEvent) -> None:
    for target in targets_chain(event.input):
        target["object"] = event.value


@event_handler(InputBoneTargetUpdateEvent)
def on_input_bone_target_update(event: InputBoneTargetUpdateEvent) -> None:
    for target in targets_chain(event.input):
        target["bone_target"] = event.value


@event_handler(InputRotationAxisUpdateEvent)
def on_input_rotation_axis_update(event: InputRotationAxisUpdateEvent) -> None:
    if event.input.rotation_mode == 'TWIST':
        value = ROTATION_MODE_TABLE[f'SWING_TWIST_{event.value}']
        for target in targets_chain(event.input):
            target["rotation_mode"] = value


@event_handler(InputRotationModeChangeEvent)
def on_input_rotation_mode_update(event: InputRotationModeChangeEvent) -> None:
    if event.input.type == 'ROTATION':
        mode = event.value

        if   mode == 'SWING' : mode = 'QUATERNION'
        elif mode == 'TWIST' : mode = f'SWING_TWIST_{event.input.rotation_axis}'
        elif mode == 'EULER' : mode = event.input.rotation_order

        for target in targets_chain(event.input):
            target["rotation_mode"] = ROTATION_MODE_TABLE[mode]


@event_handler(InputTransformSpaceChangeEvent)
def on_input_transform_space_change(event: InputTransformSpaceChangeEvent) -> None:
    value = TRANSFORM_SPACE_TABLE[event.value]
    for target in targets_chain(event.input):
        target["transform_space"] = value


@event_handler(InputVariableNewEvent)
def on_input_variable_new(event: InputVariableNewEvent) -> None:
    variable = event.variable

    variable.targets["length__internal__"] = 1
    variable.targets.internal__.add()
    variable.targets.internal__.add()

    input: 'Input' = owner_resolve(variable, ".variables")

    if input.type == 'SHAPE_KEY':
        object = input.object
        compat = {'MESH', 'LATTICE', 'CURVE'}
        target: 'InputTarget' = variable.targets[0]

        target["id_type"] = INPUT_TARGET_ID_TYPE_TABLE['KEY']
        target["id"] = object.data.shape_keys if object and object.type in compat else None
        target["data_path"] = f'key_blocks["{variable.name}"].value'

    driver: 'RBFDriver' = owner_resolve(input, ".inputs")
    input_variable_data_init(variable.data, 0.0, len(driver.poses), True)



@event_handler(InputVariableNameUpdateEvent)
def on_input_variable_name_update(event: InputVariableNameUpdateEvent) -> None:
    '''
    Updates a shape key input target's data path according to the input variable's name
    '''
    input: 'Input' = owner_resolve(event.variable, ".variables")
    if input.type == 'SHAPE_KEY':
        event.variable.targets[0]["data_path"] = f'key_blocks["{event.value}"].value'


@event_handler(InputVariableTypeUpdateEvent)
def on_input_variable_type_update(event: InputVariableTypeUpdateEvent) -> None:
    '''
    Ensures the input variable has the correct number of targets
    '''
    if event.variable.type.endswith('DIFF'):
        event.variable.targets['length__internal__'] = 2
    else:
        event.variable.targets["length__internal__"] = 1
