
from typing import TYPE_CHECKING
from .events import event_handler
from .utils import owner_resolve
from ..api.pose_data import POSE_DATA_GROUP_TYPE_INDEX, POSE_DATUM_TYPE_INDEX
from ..api.output_channel_data_sample import OutputChannelDataSampleUpdateEvent
from ..api.output import OutputNameUpdateEvent
from ..api.outputs import OutputMoveEvent, OutputNewEvent, OutputRemovedEvent
from ..api.pose import PoseUpdateEvent
from ..api.poses import PoseActiveIndexUpdateEvent
if TYPE_CHECKING:
    from ..api.pose_data import RBFDriverPoseDataGroup, RBFDriverPoseData
    from ..api.output_channel import RBFDriverOutputChannel
    from ..api.output import RBFDriverOutput
    from ..api.outputs import RBFDriverOutputs
    from ..api.driver import RBFDriver


def pose_data_group_init__generic(group: 'RBFDriverPoseDataGroup', output: 'RBFDriverOutput', pose_index: int) -> None:
    channel: 'RBFDriverOutputChannel'
    for index, channel in enumerate(output.channels):
        datum = group.data__internal__.add()
        datum["name"] = channel.name
        datum["index"] = index
        datum["value"] = channel.data[pose_index].value
        datum["is_enabled"] = channel.is_enabled


def pose_data_group_init__rotation(group: 'RBFDriverPoseDataGroup', output: 'RBFDriverOutput', pose_index: int) -> None:
    mode = output.rotation_mode
    if mode == 'EULER':
        group["type"] = POSE_DATA_GROUP_TYPE_INDEX['EULER']
        for index, channel in zip(range(1, 4), output.channels[1:]):
            datum = group.data__internal__.add()
            datum["name"] = channel.name
            datum["type"] = POSE_DATUM_TYPE_INDEX['ANGLE']
            datum["index"] = index
            datum["value"] = channel.data[pose_index].value
            datum["is_enabled"] = channel.is_enabled
    else:
        group["type"] = POSE_DATA_GROUP_TYPE_INDEX[mode]
        for index, channel in enumerate(output.channels):
            datum = group.data__internal__.add()
            datum["name"] = channel.name
            datum["index"] = index
            datum["value"] = channel.data[pose_index].value
            datum["is_enabled"] = channel.is_enabled


def pose_data_group_init__bbone(group: 'RBFDriverPoseDataGroup', output: 'RBFDriverOutput', pose_index: int) -> None:
    for index, channel in enumerate(output.channels):
        datum = group.data__internal__.add()
        datum["name"] = channel.name
        datum["index"] = index
        datum["value"] = channel.data[pose_index]
        datum["is_enabled"] = channel.is_enabled
        if   "roll" in channel.name: datum["type"] = 'ROLL'
        elif "ease" in channel.name: datum["type"] = 'EASING'


def pose_data_init(data: 'RBFDriverPoseData', outputs: 'RBFDriverOutputs', pose_index: int) -> None:
    for output in outputs:
        group = data.data__internal__.add()
        group["name"] = output.name

        if output.type == 'BBONE':
            pose_data_group_init__bbone(group, output, pose_index)
        elif output.type == 'ROTATION':
            pose_data_group_init__rotation(group, output, pose_index)
        else:
            pose_data_group_init__generic(group, output, pose_index)


@event_handler(OutputChannelDataSampleUpdateEvent)
def on_output_channel_data_sample_update(event: OutputChannelDataSampleUpdateEvent) -> None:
    '''
    Updates the output pose data when any of the active pose's output channel data samples is updated
    '''
    driver: 'RBFDriver' = owner_resolve(event.sample, ".outputs")

    if driver.poses.active_index == event.sample.index:
        data: 'RBFDriverPoseData' = driver.outputs.active_pose_data
        data.data__internal__.clear()
        pose_data_init(data, driver.outputs, driver.poses.active_index)


@event_handler(OutputMoveEvent)
def on_output_move(event: OutputMoveEvent) -> None:
    '''
    '''
    driver: 'RBFDriver' = owner_resolve(event.output, ".outputs")

    if event.from_index <= driver.outputs.active_pose_index <= event.to_index:
        active: 'RBFDriverPoseData' = driver.outputs.active_pose_data
        active.data__internal__.clear()

        if driver.poses.active:
            pose_data_init(active, driver.outputs, driver.poses.active_index)


@event_handler(OutputNewEvent)
def on_output_new(event: OutputNewEvent) -> None:
    '''
    Updates the output pose data when a new output is created
    '''
    driver: 'RBFDriver' = owner_resolve(event.output, ".outputs")
    active: 'RBFDriverPoseData' = driver.outputs.active_pose_data
    active.data__internal__.clear()

    if driver.poses.active:
        pose_data_init(active, driver.outputs, driver.poses.active_index)


@event_handler(OutputRemovedEvent)
def on_output_removed(event: OutputRemovedEvent) -> None:
    '''
    Updates the output pose data when an output has been removed
    '''
    driver: 'RBFDriver' = owner_resolve(event.outputs, ".")
    active: 'RBFDriverPoseData' = driver.outputs.active_pose_data
    active.data__internal__.clear()

    if driver.poses.active:
        pose_data_init(active, driver.outputs, driver.poses.active_index)


@event_handler(OutputNameUpdateEvent)
def on_output_name_update(event: OutputNameUpdateEvent) -> None:
    '''
    Updates the name of the corresponding pose data group
    '''
    driver: 'RBFDriver' = owner_resolve(event.output, ".outputs")
    outputs: 'RBFDriverOutputs' = driver.outputs

    index = outputs.index(event.output)
    if index < len(outputs.active_pose_data):
        outputs.active_pose_data[index]["name"] = event.output.name


@event_handler(PoseActiveIndexUpdateEvent)
def on_pose_active_index_update(event: PoseActiveIndexUpdateEvent) -> None:
    '''
    Updates the output pose data when the active pose index changes
    '''
    poses = event.poses
    index = event.value

    driver: 'RBFDriver' = owner_resolve(poses, ".")
    active: 'RBFDriverPoseData' = driver.outputs.active_pose_data
    active.data__internal__.clear()

    if index < len(poses):
        pose_data_init(active, driver.outputs, index)


@event_handler(PoseUpdateEvent)
def on_pose_update(event: PoseUpdateEvent) -> None:
    '''
    Updates the output pose data when the active pose is updated
    '''
    driver: 'RBFDriver' = owner_resolve(event.pose, ".poses")

    if driver.poses.active == event.pose:
        data: 'RBFDriverPoseData' = driver.outputs.active_pose_data
        data.data__internal__.clear()
        pose_data_init(data, driver.outputs, driver.poses.active_index)
