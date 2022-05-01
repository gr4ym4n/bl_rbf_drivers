
from typing import TYPE_CHECKING
from ..rbf_drivers.app.events import event_handler
from ..rbf_drivers.api.output import OutputRotationModeChangeEvent, OutputUseAxisUpdateEvent
if TYPE_CHECKING:
    from ..rbf_drivers.api.output import RBFDriverOutput


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


def output_update_channel_data_paths__shape_key(output: 'RBFDriverOutput') -> None:
    for channel in output.channels:
        channel["data_path"] = f'key_blocks["{channel.name}"].value'


def output_update_channel_data_paths(output: 'RBFDriverOutput') -> None:
    if output.type in {'LOCATION', 'ROTATION', 'SCALE'}:
        output_update_channel_data_paths__transform(output)
    elif output.type == 'SHAPE_KEY':
        output_update_channel_data_paths__shape_key(output)


@event_handler(OutputRotationModeChangeEvent)
def on_output_rotation_mode_change(event: OutputRotationModeChangeEvent) -> None:
    '''
    '''
    output = event.output

    if output.type == 'ROTATION':

        if event.value == 'EULER':
            channel = output.channels[0]
            channel["is_enabled"] = False
            channel.property_unset("array_index")

            for index, (channel, enabled) in enumerate(zip(output.channels[1:], (output.use_x,
                                                                                 output.use_y,
                                                                                 output.use_z))):
                channel["array_index"] = index
                channel["is_enabled"] = enabled
        else:
            for index, channel in enumerate(output.channels):
                channel["is_enabled"] = True
                channel["array_index"] = index
        
        output_update_channel_data_paths(output)


@event_handler(OutputUseAxisUpdateEvent)
def on_output_use_axis_update(event: OutputUseAxisUpdateEvent) -> None:
    output = event.output
    if (output.type in {'LOCATION', 'SCALE'}
            or (output.type == 'ROTATION' and output.rotation_mode == 'EULER')):
        axes = 'WXYZ' if output.type == 'ROTATION' else 'XYZ'
        output.channels[axes.index(event.axis)]["is_enabled"] = event.value


# @event_handler(OutputChannelBoneTargetChangeEvent)
# def on_output_channel_bone_target_change(event: OutputChannelBoneTargetChangeEvent) -> None:
#     '''
#     Synchronizes the bone target setting across output channels and updates the rotation mode
#     according to the current output channel target (where required).
#     '''
#     output: 'RBFDriverOutput' = owner_resolve(event.channel, ".channels")

#     if output.type not in {'LOCATION', 'ROTATION', 'SCALE', 'BBONE'}:
#         return

#     for channel in output.channels:
#         channel["bone_target"] = event.value

#     if output.type == 'BBONE':
#         for channel in output.channels:
#             channel["data_path"] = f'pose.bones["{event.value}"].bbone_{channel.name}'
#         return

#     id = event.channel.id
#     if id is None or not event.value or getattr(id, "type", "") != 'ARMATURE':
#         target = id
#     else:
#         target = id.pose.bones.get(event.value)

#     if (output.type == 'ROTATION'
#         and not output.rotation_mode_is_user_defined
#         and target is not None
#         and hasattr(target, "rotation_mode")
#         ):
#         output["rotation_mode"] = target.rotation_mode

#     if event.value:
#         datapath = f'pose.bones["{event.value}"].'
#     else:
#         datapath = ""

#     if output.type == 'ROTATION':
#         propname = f'rotation_{output.rotation_mode.lower()}'
#     else:
#         propname = output.type.lower()

#     for channel in output.channels:
#         channel["data_path"] = f'{datapath}{propname}'


# @event_handler(OutputChannelObjectChangeEvent)
# def on_output_channel_object_change(event: OutputChannelObjectChangeEvent) -> None:
#     '''
#     '''
#     output: 'RBFDriverOutput' = owner_resolve(event.channel, ".channels")
#     if output.type != 'NONE':
#         for channel in output.channels:
#             channel["object"] = event.value
#             channel["object__internal__"] = event.value
