
from gc import collect
from typing import TYPE_CHECKING, Union
from .events import dataclass, dispatch_event, event_handler, Event
from .utils import owner_resolve
from ..api.pose_data import PoseDatumUpdateEvent
from ..api.inputs import RBFDriverInputs
from ..api.outputs import RBFDriverOutputs
if TYPE_CHECKING:
    from ..api.pose_data import RBFDriverPoseDatum, RBFDriverPoseDataGroup
    from ..api.input import RBFDriverInput
    from ..api.output import RBFDriverOutput


@dataclass(frozen=True)
class InputPoseDatumUpdateEvent(Event):
    input: 'RBFDriverInput'
    group: 'RBFDriverPoseDataGroup'
    datum: 'RBFDriverPoseDatum'
    value: float


@dataclass(frozen=True)
class OutputPoseDatumUpdateEvent(Event):
    input: 'RBFDriverOutput'
    group: 'RBFDriverPoseDataGroup'
    datum: 'RBFDriverPoseDatum'
    value: float


@event_handler(PoseDatumUpdateEvent)
def on_pose_datum_update(event: PoseDatumUpdateEvent) -> None:
    '''
    '''
    collection: Union[RBFDriverInputs, RBFDriverOutputs] = owner_resolve(event.datum, ".active_pose_data")

    if isinstance(collect, RBFDriverInputs):
        group = owner_resolve(event.datum, ".data__internal__")
        dispatch_event(InputPoseDatumUpdateEvent())
