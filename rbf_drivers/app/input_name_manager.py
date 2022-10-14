
from typing import TYPE_CHECKING
from .events import event_handler
from .utils import name_unique
from ..api.input_targets import InputTargetBoneTargetUpdateEvent, InputTargetObjectUpdateEvent
from ..api.input import InputBoneTargetUpdateEvent, InputNameUpdateEvent
if TYPE_CHECKING:
    from ..api.input_targets import InputTargetPropertyUpdateEvent, InputTarget
    from ..api.input import Input


def input_target_token(target: 'InputTarget') -> str:
    object = target.object
    if object is None:
        return "?"
    if object.type == 'ARMATURE' and target.bone_target:
        return target.bone_target
    return object.name


def input_name_define(input_: 'Input') -> None:
    driver = input_.driver
    input_["name_is_user_defined"] = True
    input_["name"] = name_unique(input_.name, [i.name for i in driver.inputs if i != input_])


def input_name_create(input_: 'Input') -> str:
    type = input_.type
    if type in {'LOCATION', 'ROTATION', 'SCALE'}:
        result = type.title()
        object = input_.object
        target = input_.bone_target
        if object:
            suffix = target if target and object and object.type == "ARMATURE" else object.name
            result = f'{result} ({suffix})'
    elif type.endswith('DIFF'):
        result = "Distance" if type == 'LOC_DIFF' else "Rotational Difference"
        origin = input_target_token(input_.variables[0].targets[0])
        target = input_target_token(input_.variables[0].targets[1])
        result = f'{result} ({origin} - {target})'
    elif type == 'SHAPE_KEY':
        result = "Shape Keys"
        object = input_.object
        if object:
            result = f'{result} ({object.name})'
    else:
        driver = input_.driver
        result = name_unique("Input", [i.name for i in driver.inputs if i != input_])
    input_["name_is_user_defined"] = False
    input_["name"] = result


@event_handler(InputTargetObjectUpdateEvent, InputTargetBoneTargetUpdateEvent)
def on_input_target_object_update(event: 'InputTargetPropertyUpdateEvent') -> None:
    input = event.target.input
    if input.type.endswith('DIFF') and not input.name_is_user_defined:
        input_name_create(input)


@event_handler(InputBoneTargetUpdateEvent)
def on_input_bone_target_update(event: InputBoneTargetUpdateEvent) -> None:
    input_ = event.input
    if input_.type not in {'USER_DEF', 'SHAPE_KEY'} and input_.name_is_user_defined:
        input_name_create(input_)


@event_handler(InputNameUpdateEvent)
def on_input_name_update_handler(event: InputNameUpdateEvent) -> None:
    input_ = event.input
    if event.value:
        input_name_define(input_)
    else:
        input_name_create(input_)
