
from typing import TYPE_CHECKING
from .events import event_handler
from .utils import owner_resolve
from ..api.input_variable_data_sample import InputVariableDataSampleUpdateEvent
from ..api.input import InputNameUpdateEvent
from ..api.inputs import InputMoveEvent, InputNewEvent, InputRemovedEvent
from ..api.pose_data import POSE_DATA_GROUP_TYPE_INDEX, POSE_DATUM_TYPE_INDEX
from ..api.pose import PoseUpdateEvent
from ..api.poses import PoseActiveIndexUpdateEvent
if TYPE_CHECKING:
    from ..api.pose_data import RBFDriverPoseDataGroup, RBFDriverPoseData
    from ..api.input_variable import RBFDriverInputVariable
    from ..api.input import RBFDriverInput
    from ..api.inputs import RBFDriverInputs
    from ..api.driver import RBFDriver


def pose_data_group_init__generic(group: 'RBFDriverPoseDataGroup', input: 'RBFDriverInput', pose_index: int) -> None:
    for index, variable in enumerate(input.variables):
        datum = group.data__internal__.add()
        datum["name"] = variable.name
        datum["index"] = index
        datum["value"] = variable.data[pose_index].value
        datum["is_enabled"] = variable.is_enabled


def pose_data_group_init__rotation(group: 'RBFDriverPoseDataGroup', input: 'RBFDriverInput', pose_index: int) -> None:
    mode = input.rotation_mode
    variable: 'RBFDriverInputVariable'

    if len(mode) < 5:
        group["type"] = POSE_DATA_GROUP_TYPE_INDEX['EULER']
        for index, variable in zip(range(1, 4), input.variables[1:]):
            datum = group.data__internal__.add()
            datum["name"] = variable.name
            datum["type"] = POSE_DATUM_TYPE_INDEX['ANGLE']
            datum["index"] = index
            datum["value"] = variable.data[pose_index].value
            datum["is_enabled"] = variable.is_enabled

    # TODO consider mapping swing/twist to XYZ representation
    else:
        group["type"] = POSE_DATA_GROUP_TYPE_INDEX['QUATERNION']
        for index, variable in enumerate(input.variables):
            datum = group.data__internal__.add()
            datum["name"] = variable.name
            datum["index"] = index
            datum["value"] = variable.data[pose_index].value
            datum["is_enabled"] = variable.is_enabled


def pose_data_group_init__bbone(group: 'RBFDriverPoseDataGroup', input: 'RBFDriverInput', pose_index: int) -> None:
    for index, variable in enumerate(input.variables):
        datum = group.data__internal__.add()
        datum["name"] = variable.name
        datum["index"] = index
        datum["value"] = variable.data[pose_index]
        datum["is_enabled"] = variable.is_enabled
        if   "roll" in variable.name: datum["type"] = 'ROLL'
        elif "ease" in variable.name: datum["type"] = 'EASING'


def pose_data_init(data: 'RBFDriverPoseData', inputs: 'RBFDriverInputs', pose_index: int) -> None:
    for input in inputs:
        group = data.data__internal__.add()
        group["name"] = input.name

        if input.type == 'BBONE':
            pose_data_group_init__bbone(group, input, pose_index)
        elif input.type == 'ROTATION':
            pose_data_group_init__rotation(group, input, pose_index)
        else:
            pose_data_group_init__generic(group, input, pose_index)


@event_handler(InputVariableDataSampleUpdateEvent)
def on_input_variable_data_sample_update(event: InputVariableDataSampleUpdateEvent) -> None:
    '''
    Updates the input pose data when any of the active pose's input variable data samples is updated
    '''
    driver: 'RBFDriver' = owner_resolve(event.sample, ".inputs")

    if driver.poses.active_index == event.sample.index:
        data: 'RBFDriverPoseData' = driver.inputs.active_pose_data
        data.data__internal__.clear()
        pose_data_init(data, driver.inputs, driver.poses.active_index)


@event_handler(InputMoveEvent)
def on_input_move(event: InputMoveEvent) -> None:
    '''
    '''
    driver: 'RBFDriver' = owner_resolve(event.input, ".inputs")

    if event.from_index <= driver.inputs.active_pose_index <= event.to_index:
        active: 'RBFDriverPoseData' = driver.inputs.active_pose_data
        active.data__internal__.clear()

        if driver.poses.active:
            pose_data_init(active, driver.inputs, driver.poses.active_index)


@event_handler(InputNewEvent)
def on_input_new(event: InputNewEvent) -> None:
    '''
    Updates the input pose data when a new input is created
    '''
    driver: 'RBFDriver' = owner_resolve(event.input, ".inputs")
    active: 'RBFDriverPoseData' = driver.inputs.active_pose_data
    active.data__internal__.clear()

    if driver.poses.active:
        pose_data_init(active, driver.inputs, driver.poses.active_index)


@event_handler(InputRemovedEvent)
def on_input_removed(event: InputRemovedEvent) -> None:
    '''
    Updates the input pose data when an input has been removed
    '''
    driver: 'RBFDriver' = owner_resolve(event.inputs, ".")
    active: 'RBFDriverPoseData' = driver.inputs.active_pose_data
    active.data__internal__.clear()

    if driver.poses.active:
        pose_data_init(active, driver.inputs, driver.poses.active_index)


@event_handler(InputNameUpdateEvent)
def on_input_name_update(event: InputNameUpdateEvent) -> None:
    '''
    Updates the name of the corresponding pose data group
    '''
    driver: 'RBFDriver' = owner_resolve(event.input, ".inputs")
    inputs: 'RBFDriverInputs' = driver.inputs

    index = inputs.index(event.input)
    if index < len(inputs.active_pose_data):
        inputs.active_pose_data[index]["name"] = event.input.name


@event_handler(PoseActiveIndexUpdateEvent)
def on_pose_active_index_update(event: PoseActiveIndexUpdateEvent) -> None:
    '''
    Updates the input pose data when the active pose index changes
    '''
    poses = event.poses
    index = event.value

    driver: 'RBFDriver' = owner_resolve(poses, ".")
    active: 'RBFDriverPoseData' = driver.inputs.active_pose_data
    active.data__internal__.clear()

    if index < len(poses):
        pose_data_init(active, driver.inputs, index)


@event_handler(PoseUpdateEvent)
def on_pose_update(event: PoseUpdateEvent) -> None:
    '''
    Updates the input pose data when the active pose is updated
    '''
    driver: 'RBFDriver' = owner_resolve(event.pose, ".poses")

    if driver.poses.active == event.pose:
        data: 'RBFDriverPoseData' = driver.inputs.active_pose_data
        data.data__internal__.clear()
        pose_data_init(data, driver.inputs, driver.poses.active_index)
