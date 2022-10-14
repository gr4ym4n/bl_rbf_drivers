
from typing import TYPE_CHECKING, Dict, Optional, Tuple, Union
import numpy as np
from .events import dataclass, dispatch_event, event_handler, Event
from .idprop import idprop_append, idprop_assign, idprop_delete, idprop_exists, idprop_isarray
from .input_manager import InputInitializedEvent, InputSamplesUpdatedEvent
from ..api.interfaces import ICollection
from ..api.pose_data_ import pose_data_container_update, pose_data_group_remove
from ..api.input_variables import input_variable_is_enabled
from ..api.input import input_is_normalized
from ..api.inputs import InputDisposableEvent
from ..api.poses import PoseNewEvent
from ..api.drivers import DriverDisposableEvent
if TYPE_CHECKING:
    from ..api.pose_data_ import PoseDataGroup, PoseDataContainer
    from ..api.input import Input

_input_data_matrices: Dict[str, ] = {}

def input_data_matrix(input_: 'Input') -> Optional[np.ndarray]:
    return 



@dataclass
class InputPoseDataUpdate:
    data: List[Tuple[InputVariable, IDPropertyArrayElementReference ]]


# dispatch List[Tuple[Variable, Parameter]]












INPUT_DATA = "pose_data"
INPUT_NORM = "pose_data_norms"



def input_propname_data(input_: 'Input') -> str:
    return  f'input_{input_.identifier}_data'


def input_propname_norm(input_: 'Input') -> str:
    return f'input_{input_.identifier}_norm'


@dataclass(frozen=True)
class InputDataInitializedEvent(Event):
    input: 'Input'
    data: np.ndarray


@dataclass(frozen=True)
class InputDataUpdatedEvent(Event):
    input: 'Input'
    data: np.ndarray


def input_data_samples(input_: 'Input') -> np.ndarray:
    variables = tuple(filter(input_variable_is_enabled, input_.variables))
    return np.array([tuple(v.data.values()) for v in variables], dtype=float).T


def input_data_samples_normalize(input_: 'Input', data: np.ndarray) -> np.ndarray:
    norms = np.array([v.data.norm for v in input_.variables], dtype=float)
    np.divide(data, norms[:,np.newaxis], where=norms[:,np.newaxis]>input_.tolerance, out=data)
    return norms


def input_dataframe_create(input_: 'Input') -> np.ndarray:
    params: ICollection['PoseDataContainer'] = input_.parameters.internal__
    container = params.add()
    container["name"] = INPUT_DATA
    container["id_property_name"] = f'input_{input_.identifier}_{INPUT_DATA}'
    data = input_data_samples(input_)
    if input_is_normalized(input_):
        norms = params.add()
        norms["name"] = INPUT_NORM
        norms["id_property_name"] = f'input_{input_.identifier}_{INPUT_NORM}'
        pose_data_container_update(norms, input_data_samples_normalize(input_, data))
    pose_data_container_update(container, data)
    return data


def input_dataframe_update(input_: 'Input') -> np.ndarray:
    data = input_data_samples(input_)
    if input_.is_normalized:
        norms = input_data_samples_normalize(input_, data)
        pose_data_container_update(input_.parameters[INPUT_NORM], norms)
    pose_data_container_update(input_.parameters[INPUT_DATA], data)
    return data


def input_dataframe_delete(input_: 'Input') -> None:
    group: 'PoseDataGroup' = input_.parameters
    pose_data_group_remove(group, INPUT_DATA)
    pose_data_group_remove(group, INPUT_NORM)


def _input_data_update(input_: 'Input', data: np.ndarray) -> None:
    if input_is_normalized(input_):
        norm = input_data_samples_normalize(input_, data)
        idprop_assign(input_.id, input_propname_norm(input_), norm)
    idprop_assign(input_.id, input_propname_data(input_), data)






def _update(input_: 'Input') -> Union[Tuple[np.ndarray], Tuple[np.ndarray, np.ndarray]]:
    id_ = input_.id_data.data
    vars_ = tuple(filter(input_variable_is_enabled, input_.variables))
    data = np.array([tuple(v.data.values()) for v in vars_], dtype=float).T
    
    if input_is_normalized(input_):
        norms = np.array([v.data.norm for v in input_.variables], dtype=float)
        np.divide(data, norms[:,np.newaxis], where=norms[:,np.newaxis]>input_.tolerance, out=data)
        idprop_assign(id_, input_propname_norm(input_))

    idprop_assign(id_, input_propname_data(input_), data)
    return data
    


def _input_data_delete(input_: 'Input') -> None:
    idprop_delete(input_.id, input_propname_data(input_))
    if input_is_normalized(input_):
        idprop_delete(input_.id, input_propname_norm(input_))


@event_handler(InputInitializedEvent)
def on_input_initialized(event: InputInitializedEvent) -> None:
    input_ = event.input
    data = input_data_samples(input_)
    dispatch_event(InputDataInitializedEvent(input_, data))


@event_handler(InputDisposableEvent)
def on_input_disposable(event: InputDisposableEvent) -> None:
    _input_data_delete(event.input)


@event_handler(DriverDisposableEvent)
def on_driver_disposable(event: DriverDisposableEvent) -> None:
    for input_ in event.driver.inputs:
        _input_data_delete(input_)


@event_handler(PoseNewEvent)
def on_pose_new(event: PoseNewEvent) -> None:
    id_ = event.poses.id_data
    for input_ in event.poses.driver:
        name = input_propname_data(input_)
        if idprop_exists(id_, name, idprop_isarray, lambda x: len(x) == len(event.poses)-1 * )

        if input_is_normalized(input_):
            pass
        else:
            idprop_append(id_, input_propname_data(input_), data)



@event_handler(InputSamplesUpdatedEvent)
def on_input_samples_updated(event: InputSamplesUpdatedEvent) -> None:
    input_ = event.input
    dispatch_event(InputDataUpdatedEvent(input_, input_dataframe_update(input_)), immediate=True)

