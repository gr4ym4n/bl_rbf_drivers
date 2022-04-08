
from typing import TYPE_CHECKING
from ..rbf_drivers.app.events import event_handler
from ..rbf_drivers.app.utils import idprop_create, idprop_remove, owner_resolve
from ..rbf_drivers.lib.driver_utils import driver_ensure, driver_remove, driver_variables_clear, DriverVariableNameGenerator
from ..rbf_drivers.api.poses import PoseNewEvent, PoseRemovedEvent
if TYPE_CHECKING:
    from ..rbf_drivers.api import RBFDriverPoseInfluence
    from ..rbf_drivers.api.driver import RBFDriver


def pose_influence_sum_property_name(driver: 'RBFDriver') -> str:
    return f'rbfn_infls_{driver.identifier}'


def pose_influence_sum_idprop_ensure(rbfn: 'RBFDriver') -> None:
    rbfn.id_data.data[pose_influence_sum_property_name(rbfn)] = 0.0


def pose_influence_sum_idprop_remove(rbfn: 'RBFDriver') -> None:
    name = pose_influence_sum_property_name(rbfn)
    driver_remove(rbfn.id, f'["{name}"]')
    idprop_remove(rbfn.id, name, remove_drivers=False)


def pose_influence_sum_driver_update(rbfn: 'RBFDriver') -> None:
    pose_influence_sum_idprop_ensure(rbfn)

    fcurve = driver_ensure(rbfn.id_data.data, f'["{pose_influence_sum_property_name(rbfn)}"]')
    driver = fcurve.driver
    keygen = DriverVariableNameGenerator()

    variables = driver.variables
    driver_variables_clear(variables)

    for pose in rbfn.poses:
        influence = pose.influence

        variable = variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = next(keygen)

        target = variable.targets[0]
        target.id_type = influence.id_type
        target.id = influence.id
        target.data_path = influence.data_path

    driver.type = 'SUM'


@event_handler(PoseNewEvent)
def on_pose_new(event: PoseNewEvent) -> None:
    influence: 'RBFDriverPoseInfluence' = event.pose.influence
    idprop_create(influence.id, influence.name, default=1.0, min=0.0, max=1.0, soft_min=0.0, soft_max=1.0)

    pose_influence_sum_driver_update(owner_resolve(event.pose, ".poses"))


@event_handler(PoseRemovedEvent)
def on_pose_disposable(event: PoseRemovedEvent) -> None:
    influence: 'RBFDriverPoseInfluence' = event.pose.influence
    idprop_remove(influence.id, influence.name, remove_drivers=False)

    pose_influence_sum_driver_update(owner_resolve(event.pose, ".poses"))

