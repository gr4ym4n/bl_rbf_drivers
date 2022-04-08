
from typing import TYPE_CHECKING, Callable
from .events import event_handler
from .utils import owner_resolve
from ..api.output_channel import OutputChannelBoneTargetChangeEvent, OutputChannelObjectChangeEvent
from ..api.output import OutputRotationModeChangeEvent
from ..api.outputs import OutputNewEvent
if TYPE_CHECKING:
    from ..api.output import RBFDriverOutput





def output_update_channel_data_paths__transform(output: 'RBFDriverOutput') -> None:
    if output.type == 'ROTATION':
        propname = f'rotation_{output.rotation_mode.lower()}'
    else:
        propname = output.type.lower()

    for channel in output.channels:
        if channel.object is not None and channel.object.type == 'ARMATURE' and channel.bone_target:
            channel["data_path"] = f'pose.bones["{channel.bone_target}"].{propname}'
        else:
            channel["data_path"] = propname


def output_update_channel_data_paths__bbone(output: 'RBFDriverOutput') -> None:
    for channel in output.channels:
        channel["data_path"] = f'pose.bones["{channel.bone_target}"].{channel.name}'


def output_update_channel_data_paths__shape_key(output: 'RBFDriverOutput') -> None:
    for channel in output.channels:
        channel["data_path"] = f'key_blocks["{channel.name}"].value'


def output_update_channel_data_paths(output: 'RBFDriverOutput') -> None:
    if output.type in {'LOCATION', 'ROTATION', 'SCALE'}:
        output_update_channel_data_paths__transform(output)
    elif output.type == 'BBONE':
        output_update_channel_data_paths__bbone(output)
    elif output.type == 'SHAPE_KEY':
        output_update_channel_data_paths__shape_key(output)


@event_handler(OutputRotationModeChangeEvent)
def on_output_rotation_mode_channel(event: OutputRotationModeChangeEvent) -> None:
    '''
    '''
    output = event.output

    if output.type == 'ROTATION':

        if event.value == 'EULER':
            output.channels[0]["is_enabled"] = False
            for index, channel in enumerate(output.channels[1:]):
                channel["array_index"] = index
        else:
            for index, channel in enumerate(output.channels):
                channel["is_enabled"] = True
                channel["array_index"] = index
        
        output_update_channel_data_paths(output)


@event_handler(OutputChannelBoneTargetChangeEvent)
def on_output_channel_bone_target_change(event: OutputChannelBoneTargetChangeEvent) -> None:
    '''
    Synchronizes the bone target setting across output channels and updates the rotation mode
    according to the current output channel target (where required).
    '''
    output: 'RBFDriverOutput' = owner_resolve(event.channel, ".channels")

    if output.type not in {'LOCATION', 'ROTATION', 'SCALE', 'BBONE'}:
        return

    for channel in output.channels:
        channel["bone_target"] = event.value

    if output.type == 'BBONE':
        for channel in output.channels:
            channel["data_path"] = f'pose.bones["{event.value}"].bbone_{channel.name}'
        return

    id = event.channel.id
    if id is None or not event.value or getattr(id, "type", "") != 'ARMATURE':
        target = id
    else:
        target = id.pose.bones.get(event.value)

    if (output.type == 'ROTATION'
        and not output.rotation_mode_is_user_defined
        and target is not None
        and hasattr(target, "rotation_mode")
        ):
        output["rotation_mode"] = target.rotation_mode

    if event.value:
        datapath = f'pose.bones["{event.value}"].'
    else:
        datapath = ""

    if output.type == 'ROTATION':
        propname = f'rotation_{output.rotation_mode.lower()}'
    else:
        propname = output.type.lower()

    for channel in output.channels:
        channel["data_path"] = f'{datapath}{propname}'


@event_handler(OutputChannelObjectChangeEvent)
def on_output_channel_object_change(event: OutputChannelObjectChangeEvent) -> None:
    '''
    '''
    output: 'RBFDriverOutput' = owner_resolve(event.channel, ".channels")
    if output.type != 'NONE':
        for channel in output.channels:
            channel["object"] = event.value
            channel["object__internal__"] = event.value
