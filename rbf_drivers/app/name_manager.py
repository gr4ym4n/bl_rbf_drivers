
from typing import TYPE_CHECKING, Sequence
from .events import event_handler
from .utils import owner_resolve
from ..api.input import InputNameUpdateEvent
from ..api.pose import PoseNameUpdateEvent
from ..api.output import OutputNameUpdateEvent
if TYPE_CHECKING:
    from ..api.driver import RBFDriver


def uniqname(value: str, names: Sequence[str]) -> str:
    i = 0
    k = value
    while k in names:
        i += 1
        k = f'{value}.{str(i).zfill(3)}'
    return k


@event_handler(InputNameUpdateEvent)
def on_input_name_update(event: InputNameUpdateEvent) -> None:
    '''
    Ensures the input's name is unique
    '''
    input = event.input
    driver: 'RBFDriver' = owner_resolve(input, ".inputs")
    input["name"] = uniqname(event.value, [x.name for x in driver.inputs if x != input])


@event_handler(PoseNameUpdateEvent)
def on_pose_name_update(event: PoseNameUpdateEvent) -> None:
    '''
    '''
    pose = event.pose
    driver: 'RBFDriver' = owner_resolve(pose, ".poses")
    pose["name"] = uniqname(event.value, [x.name for x in driver.poses if x != pose])


@event_handler(OutputNameUpdateEvent)
def on_output_name_update(event: OutputNameUpdateEvent) -> None:
    '''
    '''
    output = event.output
    driver: 'RBFDriver' = owner_resolve(output, ".outputs")
    output["name"] = uniqname(event.value, [x.name for x in driver.outputs if x != output])
