
from ctypes import Union
from math import acos, asin, fabs, pi, sqrt
from typing import TYPE_CHECKING, Callable, Iterator, Optional, Sequence
import numpy as np
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, IntProperty, PointerProperty, StringProperty
from .mixins import Observable
from .inputs import Inputs
from .poses import Poses
from ..utils_ import resolve
if TYPE_CHECKING:
    from .inputs import Input
    from .poses import Pose

DRIVER_TYPE_ITEMS = [
    ('NONE'      , "Generic"   , "", 'DRIVER'       , 0),
    ('SHAPE_KEY' , "Shape Keys", "", 'SHAPEKEY_DATA', 1),
    ]

DRIVER_TYPE_INDEX = [
    item[0] for item in DRIVER_TYPE_ITEMS
    ]

#region Driver
#--------------------------------------------------------------------------------------------------

def _driver_name_get(driver: 'RBFDriver') -> str:
    return driver.get("name", "")


def _driver_name_set(driver: 'RBFDriver', name: str) -> None:
    names = list(resolve(driver, ".drivers").keys())
    index = 0
    value = name
    while value in names:
        index += 1
        value = f'{name}.{str(index).zfill(3)}'
    cache = driver.name
    driver["name"] = value
    driver.notify_observers("name", value, cache)


class RBFDriver(Observable, PropertyGroup):

    inputs: PointerProperty(
        name="Inputs",
        description="",
        type=Inputs,
        options=set()
        )

    name: StringProperty(
        name="Name",
        description="Unique driver name",
        get=_driver_name_get,
        set=_driver_name_set,
        maxlen=56
        options=set()
        )

    poses: PointerProperty(
        name="Poses",
        description="",
        type=Poses,
        options=set()
        )

#endregion

#region Drivers
#--------------------------------------------------------------------------------------------------

class RBFDrivers(Observable, PropertyGroup):

    active_index: IntProperty(
        name="RBF Driver",
        min=0,
        default=0,
        options=set()
        )

    @property
    def active(self) -> Optional[RBFDriver]:
        index = self.active_index
        return self[index] if index < len(self) else None

    internal__: CollectionProperty(
        type=RBFDriver,
        options={'HIDDEN'}
        )

    def new(self, type: str) -> RBFDriver:
        
        if not isinstance(type, str):
            raise TypeError((f'{self.__class__.__name__}.new(name="", type="NONE", mirror=None): '
                              f'Expected type to str, not {type.__class__.__name__}'))

        if type not in DRIVER_TYPE_INDEX:
            raise TypeError((f'{self.__class__.__name__}.new(name="", type="NONE", mirror=None): '
                             f'type "{type}" not found in {", ".join(DRIVER_TYPE_INDEX)}'))

        driver = self.internal__.add()
        driver["type"] = DRIVER_TYPE_INDEX.index(type)

        driver.inputs.add_observer("new", on_input_new)
        driver.poses.add_observer("new", on_pose_new)
            

#endregion


def input_data_create(data: 'InputData', default_value: float, poses: Poses) -> None:
    for pose in poses:
        sample = data.internal__.add()
        sample.__init__(name=pose.name, value=default_value)
        sample.add_observer("value", on_input_sample_value_update)


def input_data_update(data: 'InputData') -> None:
    if data.is_normalized:
        norm = data["norm"] = np.linalg.norm(tuple(data.values()))
        if norm != 0.0:
            for sample in data:
                sample["value_normalized"] = sample.value / norm
        else:
            for sample in data:
                sample["value_normalized"] = sample.value


def on_input_new(inputs: Inputs, input_: 'Input') -> None:
    driver = resolve(inputs, ".inputs")
    variables = input_.variables
    for variable in variables:
        data = variable.data
        input_data_create(data, variable.default_value, driver.poses)
        input_data_update(data)
    variables.add_observer("new", on_input_variable_new)



def on_input_variable_new(variables: 'InputVariables', variable: 'InputVariable') -> None:
    pass


def on_pose_name_update(pose: 'Pose', value: str, previous_value: str) -> None:
    driver = resolve(pose, ".poses")
    for input_ in driver.inputs:
        for variable in input_.variables:
            sample = variable.data.get(previous_value)
            if sample:
                sample["name"] = value


def on_pose_new(poses: Poses, pose: 'Pose') -> None:
    pose.add_observer("name", on_pose_name_update)
    driver = resolve(pose, ".poses")
    for input_ in driver.inputs:
        for variable in input_.variables:
            data = variable.data
            sample = data.internal__.add()
            sample.__init__(name=pose.name, value=variable.value)
            input_data_update(data)


def on_driver_name_update(driver: RBFDriver, value: str, previous_value: str) -> None:
    try:
        del driver.id_data.data[f'{previous_value}_radii']
    except KeyError: pass
    pose_radii_idprop_update(driver)
    network.inputs.build()