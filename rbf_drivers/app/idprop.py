
from typing import Any, Callable, Dict, Optional, Sequence, Tuple, Union, TYPE_CHECKING
import numpy as np
from idprop.types import IDPropertyArray
if TYPE_CHECKING:
    from bpy.types import ID


def idprop_isarray(value: Any) -> bool:
    return isinstance(value, IDPropertyArray)


def idprop_append(id_: 'ID',
                  name: str,
                  data: Union[float, Sequence[float]],
                  axis: Optional[int]=0) -> None:
    prop = id_.get(name)
    if idprop_isarray(prop):
        if axis:
            rows = len(data)
            cols = len(prop) // rows
            prop = np.array(prop.to_list()).reshape(rows, cols)
            data = np.append(prop, np.asarray(data)[:,np.newaxis], axis=1)
            idprop_assign(id_, name, data.flatten())
        else:
            data = [data] if isinstance(data, float) else list(data)
            idprop_assign(id_, name, prop.to_list() + data)
    else:
        raise RuntimeError()


def idprop_delete(id_: 'ID', name: str) -> None:
    try:
        del id_[name]
    except KeyError: pass


def idprop_exists(id_: 'ID', name: str, *validations: Tuple[Callable[[Any], bool], ...]) -> bool:
    data = id_.get(name)
    return False if data is None else not validations or all(fn(data) for fn in validations)


def idprop_remove(id_: 'ID', name: str, index: int) -> None:
    prop = id_.get(name)
    if isinstance(prop, IDPropertyArray) and index < len(prop):
        data = prop.to_list()
        del data[index]
        idprop_assign(id_, name, data)


def idprop_assign(id_: 'ID',
                  name: str,
                  data: Optional[Union[float, Sequence[float], Sequence[Sequence[float]]]]=None,
                  **options: Dict[str, Any]) -> None:
    if data is not None:
        if isinstance(data, float):
            id_[name] = data
        else:
            id_[name] = np.asarray(data, dtype=float).flatten()
    if options:
        id_.id_properties_ui(name).update(**options)
