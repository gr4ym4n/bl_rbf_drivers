
from typing import TYPE_CHECKING, Optional
if TYPE_CHECKING:
    from bpy.types import ChannelDriverVariables, FCurve, ID


def driver_ensure(id_: 'ID', path: str, index: Optional[int]=-1) -> 'FCurve':
    fcurve = driver_find(id_, path, index)
    if fcurve is None:
        drivers = id_.animation_data_create().drivers
        fcurve = drivers.new(path, index=index) if index >= 0 else drivers.new(path)
    return fcurve


def driver_find(id_: 'ID', path: str, index: Optional[int]=-1) -> Optional['FCurve']:
    animdata = id_.animation_data
    if animdata:
        drivers = animdata.drivers
        return drivers.find(path, index=index) if index >= 0 else drivers.find(path)


def driver_remove(id_: 'ID', path: str, index: Optional[int]=-1) -> None:
    fcurve = driver_find(id_, path, index)
    if fcurve is not None:
        fcurve.id_data.animation_data.drivers.remove(fcurve)


def drivers_clear(id_: 'ID', path: str) -> None:
    animdata = id_.animation_data
    if animdata:
        drivers = animdata.drivers
        for fcurve in reversed(list(drivers)):
            if fcurve.data_path == path:
                drivers.remove(fcurve)


def driver_variables_clear(variables: 'ChannelDriverVariables') -> None:
    for index in range(len(variables)-1, -1, -1):
        variables.remove(variables[index])
