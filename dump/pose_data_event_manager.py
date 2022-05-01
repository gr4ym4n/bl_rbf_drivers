
from gc import collect
from typing import TYPE_CHECKING, Union
from ..rbf_drivers.app.events import dataclass, dispatch_event, event_handler, Event
from ..rbf_drivers.app.utils import owner_resolve
from .pose_data import PoseDatumUpdateEvent
from ..rbf_drivers.api.inputs import RBFDriverInputs
from ..rbf_drivers.api.outputs import RBFDriverOutputs
if TYPE_CHECKING:
    from .pose_data import RBFDriverPoseDatum, RBFDriverPoseDataGroup
    from ..rbf_drivers.api.input import RBFDriverInput
    from ..rbf_drivers.api.output import RBFDriverOutput


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
