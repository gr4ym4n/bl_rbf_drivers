
from typing import Iterable, Optional, Union
from contextlib import suppress
from itertools import repeat
from bpy.types import ID
from ..api.mixins import Identifiable
from ..api.input import RBFDriverInput
from ..api.pose import RBFDriverPose
from ..api.driver import RBFDriver

INPUT_POSE_DISTANCE = 'rbfn_idist'
INPUT_POSE_DISTANCE_NORMALIZED = 'rbfn_dists'
POSE_WEIGHT = f'rbfn_pwgts'
POSE_WEIGHT_SUM = f'rbfn_swgts'
POSE_WEIGHT_NORMALIZED = f'rbfn_wnorm'

def idprop_name_format(owner: Identifiable, type: str) -> str:
    return f'{type}_{owner.identifier}'

def idprop_path_format(owner: Identifiable, type: str, index: Optional[int]=None) -> str:
    return f'["{idprop_name_format(owner, type)}"]{"" if index is None else "["+str(index)+"]"}'

def idprop_array_create(id: ID, name: str, data: Union[int, Iterable[float]]) -> None:
    id[name] = list(repeat(0.0, data) if isinstance(data, int) else data)

def idprop_float_create(id: ID, name: str, data: Optional[float]=0.0) -> None:
    id[name] = data

def idprop_input_pose_distance_update(input: RBFDriverInput, pose_count: Optional[int]=None) -> None:
    idprop_array_create(input.id_data.data,
                        idprop_name_format(input, INPUT_POSE_DISTANCE),
                        len(input.rbf_driver.poses) if pose_count is None else pose_count)

def idprop_input_pose_distance_remove(input: RBFDriverInput) -> None:
    with suppress(KeyError):
        del input.id_data.data[idprop_name_format(input, INPUT_POSE_DISTANCE)]

def idprop_input_pose_distance_normalized_ensure(driver: RBFDriver, pose_count: Optional[int]=None) -> None:
    idprop_array_create(driver.id_data.data,
                        idprop_name_format(input, INPUT_POSE_DISTANCE_NORMALIZED),
                        len(driver.poses) if pose_count is None else pose_count)

def idprop_input_pose_distance_normalized_remove(driver: RBFDriver) -> None:
    with suppress(KeyError):
        del driver.id_data.data[idprop_name_format(driver, INPUT_POSE_DISTANCE_NORMALIZED)]

def idprop_pose_weight_update(driver: RBFDriver, pose_count: Optional[int]=None) -> None:
    idprop_array_create(driver.id_data.data,
                        idprop_name_format(driver, POSE_WEIGHT),
                        len(driver.poses) if pose_count is None else pose_count)

def idprop_pose_weight_remove(driver: RBFDriver) -> None:
    with suppress(KeyError):
        del driver.id_data.data[idprop_name_format(driver, POSE_WEIGHT)]

def idprop_pose_weight_sum_update(driver: RBFDriver) -> None:
    idprop_float_create(driver.id_data.data, idprop_name_format(driver, POSE_WEIGHT_SUM), 0.0)

def idprop_pose_weight_sum_remove(driver: RBFDriver) -> None:
    with suppress(KeyError):
        del driver.id_data.data[idprop_name_format(driver, POSE_WEIGHT_SUM)]

def idprop_pose_weight_normalized_update(driver: RBFDriver, pose_count: Optional[int]=None) -> None:
    idprop_array_create(driver.id_data.data,
                        idprop_name_format(driver, POSE_WEIGHT_NORMALIZED),
                        len(driver.poses) if pose_count is None else pose_count)

def idprop_pose_weight_normalized_remove(driver: RBFDriver) -> None:
    with suppress(KeyError):
        del driver.id_data.data[idprop_name_format(driver, POSE_WEIGHT_NORMALIZED)]

def on_input_created(driver: RBFDriver, input: RBFDriverInput) -> None:
    idprop_input_pose_distance_update(input, len(driver.poses))
    if len(driver.inputs) > 1:
        idprop_input_pose_distance_normalized_ensure(driver)

def on_input_removed(driver: RBFDriver, _: int) -> None:
    idprop_input_pose_distance_remove(input, len(driver.poses))
    if len(driver.inputs) < 2:
        idprop_input_pose_distance_normalized_remove(driver)

def on_pose_created(driver: RBFDriver, _: RBFDriverPose) -> None:
    pose_count = len(driver.poses)

    for input in driver.inputs:
        idprop_input_pose_distance_update(input, pose_count)

    idprop_pose_weight_update(driver, pose_count)

    if driver.normalize_pose_weights:
        idprop_pose_weight_sum_update(driver)
        idprop_pose_weight_normalized_update(driver, pose_count)

def on_pose_removed(driver: RBFDriver, _: int) -> None:
    pose_count = len(driver.poses)

    for input in driver.inputs:
        idprop_input_pose_distance_update(input, pose_count)

    idprop_pose_weight_update(driver, pose_count)

    if driver.normalize_pose_weights:
        idprop_pose_weight_sum_update(driver)
        idprop_pose_weight_normalized_update(driver, pose_count)
