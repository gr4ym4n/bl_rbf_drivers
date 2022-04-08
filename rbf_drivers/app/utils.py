
from typing import Any, Dict, Optional, TYPE_CHECKING
from bpy.types import ID, PropertyGroup
from rbf_drivers.lib.driver_utils import driver_remove
from rna_prop_ui import rna_idprop_ui_create
from idprop.types import IDPropertyArray
if TYPE_CHECKING:
    from bpy.types import ChannelDriverVariables

def owner_resolve(data: PropertyGroup, token: str) -> PropertyGroup:
    path: str = data.path_from_id()
    return data.id_data.path_resolve(path.rpartition(token)[0])


def idprop_create(id: ID, name: str, **options: Dict[str, Any]) -> None:
    rna_idprop_ui_create(id, name, **options)


def idprop_ensure(id: ID, name: str, size: Optional[int]=1) -> str:
    value = id.get(name)
    if value is None or not isinstance(value, IDPropertyArray) or len(value) != size:
        id[name] = [0.0] * size
    return f'["{name}"]'


def idprop_array_ensure(id: ID, name: str, size: int, remove_drivers: Optional[bool]=True) -> None:
    val = id.get(name)
    if val is not None and remove_drivers:
        if not isinstance(val, IDPropertyArray):
            driver_remove(id, f'["{name}"]')
        elif len(val) > size:
            path = f'["{name}"]'
            for i in range(size, len(val)):
                driver_remove(id, path, i)
    id[name] = [0.0] * size


def driver_variables_ensure(variables: 'ChannelDriverVariables', count: int) -> 'ChannelDriverVariables':
    while len(variables) > count:
        variables.remove(variables[-1])
    while len(variables) < count:
        variables.new()
    return variables


def idprop_remove(id: ID, name: str, remove_drivers: Optional[bool]=True) -> None:
    try:
        del id[name]
    except KeyError:
        pass
    else:
        if remove_drivers:
            animdata = id.animation_data
            if animdata:
                datapath = f'["{name}"]'
                for fcurve in reversed(animdata.drivers):
                    if fcurve.data_path == datapath:
                        animdata.drivers.remove(fcurve)


def idprop_splice(id: ID, name: str, index: int, remove_driver: Optional[bool]=True) -> None:
    value = id.get(name)
    if isinstance(value, IDPropertyArray) and len(value) > index:
        id[name] = [0.0] * (len(value) - 1)
        if remove_driver:
            animdata = id.animation_data
            if animdata:
                datapath = f'["{name}"]'
                for fcurve in animdata.drivers:
                    if fcurve.data_path == datapath and fcurve.array_index == index:
                        animdata.drivers.remove(fcurve)
                        break
