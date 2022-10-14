
from itertools import product
from functools import partial
from math import cos, sin
from operator import attrgetter
from string import ascii_letters
from typing import Any, Dict, Generic, Iterable, Iterator, List, Optional, Sequence, Tuple, TypeVar, Union, TYPE_CHECKING
from mathutils import Euler, Quaternion, Vector
from bpy.types import PoseBone, PropertyGroup
from idprop.types import IDPropertyArray
if TYPE_CHECKING:
    from mathutils import Matrix
    from bpy.types import (
        ChannelDriverVariables,
        Driver,
        DriverVariable,
        FCurve,
        FCurveKeyframePoints,
        ID,
        Object,
        UILayout
        )
    from ..api.mixins import IDPropertyController
    from ..api.pose_interpolation import CurvePointInterface
    from ..api.preferences import RBFDriverPreferences


def owner_resolve(data: PropertyGroup, token: str) -> PropertyGroup:
    path: str = data.path_from_id()
    return data.id_data.path_resolve(path.rpartition(token)[0])


def name_unique(value: str,
                names: Sequence[str],
                separator: Optional[str]=".",
                zfill: Optional[int]=3) -> str:
    i = 0
    k = value
    while k in names:
        i += 1
        k = f'{value}{separator}{str(i).zfill(zfill)}'
    return k


def driver_find(id: 'ID', path: str, index: Optional[int]=None) -> Optional['FCurve']:
    animdata = id.animation_data
    if animdata is not None:
        drivers = animdata.drivers
        return drivers.find(path) if index is None else drivers.find(path, index=index)


def driver_ensure(id: 'ID', path: str, index: Optional[int]=None) -> 'FCurve':
    fcurve = driver_find(id, path, index)
    if fcurve is None:
        drivers = id.animation_data_create().drivers
        fcurve = drivers.new(path) if index is None else drivers.new(path, index=index)
    return fcurve


def driver_remove(id: 'ID', path: str, index: Optional[int]=None) -> None:
    fcurve = driver_find(id, path, index)
    if fcurve is not None:
        fcurve.id_data.animation_data.drivers.remove(fcurve)


def driver_variables_clear(variables: 'ChannelDriverVariables') -> None:
    while len(variables):
        variables.remove(variables[-1])


class DriverVariableNameGenerator:
    """Generator for minimal length sequential valid driver variable names"""

    def __init__(self) -> None:
        self._index = 0
        self._chars = ascii_letters
        self._count = 1
        self._names = iter(self._chars)
    
    def __iter__(self) -> Iterator[str]:
        return self

    def __next__(self) -> str:
        try:
            name = next(self._names)
        except StopIteration:
            self._count += 1
            self._names = product(self._chars, repeat=self._count)
            name = next(self._names)
        return name


def driver_variables_ensure(variables: 'ChannelDriverVariables', count: int) -> 'ChannelDriverVariables':
    while len(variables) > count:
        variables.remove(variables[-1])
    while len(variables) < count:
        variables.new()
    return variables


#region

def update_filepath_check(filepath: str) -> Optional[Exception]:
    import os
    if not os.path.exists(filepath):
        return ValueError("Invalid update file path")

    import zipfile
    if not zipfile.is_zipfile(filepath):
        return ValueError("Invalid update file type")


def update_script_read(filepath: str) -> str:
    import os
    with open(os.path.join(os.path.dirname(__file__), "update.py")) as file:
        return file.read().replace("FILEPATH", filepath)


def update_preferences(preferences: 'RBFDriverPreferences',
                       status=str,
                       **kwargs: Dict[str, Any]) -> None:
    preferences.update_status = status
    for key, value in kwargs.items():
        preferences[key] = value

#endregion


# region Rotation Utilities
#--------------------------------------------------------------------------------------------------

def as_euler(value: Sequence[float]) -> Euler:
    return value if isinstance(value, Euler) else Euler(value)


def as_quaternion(value: Sequence[float]) -> Quaternion:
    return value if isinstance(value, Quaternion) else Quaternion(value)


def axis_angle_to_euler(value: Union[Sequence[float], Tuple[Sequence[float], float]]) -> Euler:
    return quaternion_to_euler(axis_angle_to_quaternion(value))


def axis_angle_to_quaternion(value: Union[Sequence[float], Tuple[Sequence[float], float]]) -> Quaternion:
    return Quaternion(*value) if len(value) == 2 else Quaternion(value[1:], value[0])


def euler_to_axis_angle(euler: Sequence[float], vectorize: Optional[bool]=False) -> Union[Tuple[Vector, float], Vector]:
    return quaternion_to_axis_angle(euler_to_quaternion(euler), vectorize)


def euler_to_quaternion(euler: Sequence[float]) -> Quaternion:
    return as_euler(euler).to_quaternion()


def euler_to_swing_twist(value: Sequence[float], axis: str, quaternion: Optional[bool]=False) -> Union[Tuple[Quaternion, float], Quaternion]:
    return quaternion_to_swing_twist(euler_to_quaternion(value), axis, quaternion)


def euler_to_swing_twist_x(value: Sequence[float], quaternion: Optional[bool]=False) -> Union[Tuple[Quaternion, float], Quaternion]:
    return euler_to_swing_twist(value, 'X', quaternion=quaternion)


def euler_to_swing_twist_y(value: Sequence[float], quaternion: Optional[bool]=False) -> Union[Tuple[Quaternion, float], Quaternion]:
    return euler_to_swing_twist(value, 'Y', quaternion=quaternion)


def euler_to_swing_twist_z(value: Sequence[float], quaternion: Optional[bool]=False) -> Union[Tuple[Quaternion, float], Quaternion]:
    return euler_to_swing_twist(value, 'Z', quaternion=quaternion)


def quaternion_to_axis_angle(quaternion: Sequence[float], vectorize: Optional[bool]=False) -> Union[Tuple[Vector, float], Vector]:
    axis, angle = as_quaternion(quaternion).to_axis_angle()
    return Vector((angle, axis[0], axis[1], axis[2])) if vectorize else (axis, angle)


def quaternion_to_euler(quaternion: Sequence[float], order: Optional[str]='XYZ') -> Euler:
    return as_quaternion(quaternion).to_euler(order)


def quaternion_to_swing_twist(value: Sequence[float], axis: str, quaternion: Optional[bool]=False) -> Union[Tuple[Quaternion, float], Quaternion]:
    swing, twist = as_quaternion(value).to_swing_twist(axis)
    if quaternion:
        index = 'WXYZ'.index(axis)
        swing[index] = twist
        return swing
    return swing, twist


def quaternion_to_swing_twist_x(value: Sequence[float], quaternion: Optional[bool]=False) -> Union[Tuple[Quaternion, float], Quaternion]:
    return quaternion_to_swing_twist(value, 'X', quaternion=quaternion)


def quaternion_to_swing_twist_y(value: Sequence[float], quaternion: Optional[bool]=False) -> Union[Tuple[Quaternion, float], Quaternion]:
    return quaternion_to_swing_twist(value, 'Y', quaternion=quaternion)


def quaternion_to_swing_twist_z(value: Sequence[float], quaternion: Optional[bool]=False) -> Union[Tuple[Quaternion, float], Quaternion]:
    return quaternion_to_swing_twist(value, 'Z', quaternion=quaternion)


def swing_twist_to_euler(value: Union[Tuple[Sequence[float], float], Sequence[float]], axis: str) -> Quaternion:
    return quaternion_to_euler(swing_twist_to_quaternion(value, axis))


def swing_twist_to_quaternion(value: Union[Tuple[Sequence[float], float], Sequence[float]], axis: str) -> Quaternion:
    index = 'WXYZ'.index(axis)
    if len(value) == 2:
        swing = as_quaternion(value[0])
        twist = Quaternion((cos(value[1] * 0.5), 0.0, 0.0, 0.0))
        twist[index] = -sin(value[1] * 0.5)
        return swing @ twist.inverted()
    else:
        swing = as_quaternion(value)
        twist = Quaternion((cos(value[index] * 0.5), 0.0, 0.0, 0.0))
        twist[index] = -sin(value[index] * 0.5)
        swing[index] = 0.0
    return swing @ twist.inverted()


def swing_twist_x_to_euler(value: Union[Tuple[Sequence[float], float], Sequence[float]]) -> Quaternion:
    return swing_twist_to_euler(value, 'X')


def swing_twist_y_to_euler(value: Union[Tuple[Sequence[float], float], Sequence[float]]) -> Quaternion:
    return swing_twist_to_euler(value, 'Y')


def swing_twist_z_to_euler(value: Union[Tuple[Sequence[float], float], Sequence[float]]) -> Quaternion:
    return swing_twist_to_euler(value, 'Z')


def swing_twist_x_to_euler(value: Union[Tuple[Sequence[float], float], Sequence[float]]) -> Euler:
    return quaternion_to_euler(swing_twist_x_to_quaternion(value))


def swing_twist_x_to_quaternion(value: Union[Tuple[Sequence[float], float], Sequence[float]]) -> Quaternion:
    return swing_twist_to_quaternion(value, 'X')


def swing_twist_y_to_quaternion(value: Union[Tuple[Sequence[float], float], Sequence[float]]) -> Quaternion:
    return swing_twist_to_quaternion(value, 'Y')


def swing_twist_z_to_quaternion(value: Union[Tuple[Sequence[float], float], Sequence[float]]) -> Quaternion:
    return swing_twist_to_quaternion(value, 'Z')


def swing_twist_x_to_swing_twist_y(value: Union[Tuple[Sequence[float], float], Sequence[float]]) -> Union[Tuple[Quaternion, float], Quaternion]:
    return quaternion_to_swing_twist_x(swing_twist_x_to_quaternion(value), quaternion=len(value) != 2)


def swing_twist_x_to_swing_twist_z(value: Union[Tuple[Sequence[float], float], Sequence[float]]) -> Union[Tuple[Quaternion, float], Quaternion]:
    return quaternion_to_swing_twist_z(swing_twist_x_to_quaternion(value), quaternion=len(value) != 2)


def swing_twist_y_to_swing_twist_x(value: Union[Tuple[Sequence[float], float], Sequence[float]]) -> Union[Tuple[Quaternion, float], Quaternion]:
    return quaternion_to_swing_twist_x(swing_twist_y_to_quaternion(value), quaternion=len(value) != 2)


def swing_twist_y_to_swing_twist_z(value: Union[Tuple[Sequence[float], float], Sequence[float]]) -> Union[Tuple[Quaternion, float], Quaternion]:
    return quaternion_to_swing_twist_z(swing_twist_y_to_quaternion(value), quaternion=len(value) != 2)


def swing_twist_z_to_swing_twist_x(value: Union[Tuple[Sequence[float], float], Sequence[float]]) -> Union[Tuple[Quaternion, float], Quaternion]:
    return quaternion_to_swing_twist_x(swing_twist_z_to_quaternion(value), quaternion=len(value) != 2)


def swing_twist_z_to_swing_twist_y(value: Union[Tuple[Sequence[float], float], Sequence[float]]) -> Union[Tuple[Quaternion, float], Quaternion]:
    return quaternion_to_swing_twist_y(swing_twist_z_to_quaternion(value), quaternion=len(value) != 2)

#endregion

#region

def transform_target(object_: Optional['Object'], bone_target: Optional[str]="") -> Optional[Union['Object', 'PoseBone']]:
    target = object_
    if target and target.type == 'ARMATURE' and bone_target:
        target = target.pose.bones.get(bone_target)
    return target


def transform_matrix(target: Union['Object', PoseBone], space: Optional[str]='WORLD_SPACE') -> 'Matrix':
    if isinstance(target, PoseBone):
        if space == 'TRANSFORM_SPACE': return target.matrix_channel
        to_space = space[:5]
        if to_space in ('LOCAL', 'WORLD'):
            return target.id_data.convert_space(pose_bone=target, matrix=target.matrix, from_space='POSE', to_space=to_space)
    else:
        if space == 'TRANSFORM_SPACE': return target.matrix_basis
        if space == 'LOCAL_SPACE': return target.matrix_local
        return target.matrix_world


def transform_location(target: Union['Object', 'PoseBone'], space: Optional[str]='WORLD_SPACE') -> 'Vector':
    return transform_matrix(target, space).to_translation()


def transform_rotation(target: Union['Object', 'PoseBone'],
                       mode: str,
                       space: Optional[str]='WORLD_SPACE') -> Union['Quaternion', 'Euler']:
    matrix = transform_matrix(target, space)
    result = matrix.to_quaternion()
    if mode == 'EULER': result = result.to_euler()
    elif mode == 'SWING_TWIST_X': return quaternion_to_swing_twist_x(result, True)
    elif mode == 'SWING_TWIST_Y': return quaternion_to_swing_twist_y(result, True)
    elif mode == 'SWING_TWIST_Z': return quaternion_to_swing_twist_z(result, True)
    return result


def transform_scale(target: Union['Object', 'PoseBone'], space: Optional[str]='WORLD_SPACE') -> 'Vector':
    return transform_matrix(target, space).to_scale()

#endregion

#region
#--------------------------------------------------------------------------------------------------

def calc_bezier_handles(p2: Vector,
                        ht: str,
                        h1: Vector,
                        h2: Vector,
                        prev:Optional[Vector]=None,
                        next:Optional[Vector]=None) -> None:
    pt = Vector((0.0, 0.0))

    if prev is None:
        p3 = next
        pt[0] = 2.0 * p2[0] - p3[0]
        pt[1] = 2.0 * p2[1] - p3[1]
        p1 = pt
    else:
        p1 = prev

    if next is None:
        p1 = prev
        pt[0] = 2.0 * p2[0] - p1[0]
        pt[1] = 2.0 * p2[1] - p1[1]
        p3 = pt
    else:
        p3 = next

    dvec_a = p2 - p1
    dvec_b = p3 - p2
    len_a = dvec_a.length
    len_b = dvec_b.length

    if len_a == 0.0:
        len_a = 1.0
    if len_b == 0.0:
        len_b = 1.0

    if ht in ('AUTO', 'AUTO_CLAMPED'):
        tvec = Vector((
            dvec_b[0] / len_b + dvec_a[0] / len_a,
            dvec_b[1] / len_b + dvec_a[1] / len_a))

        length = tvec.length * 2.5614
        if length != 0.0:
            ln = -(len_a / length)
            h1[0] = p2[0] + tvec[0] * ln
            h1[1] = p2[1] + tvec[1] * ln
            if ht == 'AUTO_CLAMPED' and prev is not None and next is not None:
                ydiff1 = prev[1] - p2[1]
                ydiff2 = next[1] - p2[1]
                if (ydiff1 <= 0.0 and ydiff2 <= 0.0) or (ydiff1 >= 0.0 and ydiff2 >= 0.0):
                    h1[1] = p2[1]
                else:
                    if ydiff1 <= 0.0:
                        if prev[1] > h1[1]:
                            h1[1] = prev[1]
                    else:
                        if prev[1] < h1[1]:
                            h1[1] = prev[1]

            ln = len_b / length
            h2[0] = p2[0] + tvec[0] * ln
            h2[1] = p2[1] + tvec[1] * ln
            if ht == 'AUTO_CLAMPED' and prev is not None and next is not None:
                ydiff1 = prev[1] - p2[1]
                ydiff2 = next[1] - p2[1]
                if (ydiff1 <= 0.0 and ydiff2 <= 0.0) or (ydiff1 >= 0.0 and ydiff2 >= 0.0):
                    h2[1] = p2[1]
                else:
                    if ydiff1 <= 0.0:
                        if next[1] < h2[1]:
                            h2[1] = next[1]
                    else:
                        if next[1] > h2[1]:
                            h2[1] = next[1]

    else: # ht == VECTOR
        h1[0] = p2[0] + dvec_a[0] * (-1.0/3.0)
        h1[1] = p2[1] + dvec_a[1] * (-1.0/3.0)
        h2[0] = p2[0] + dvec_b[0] * (1.0/3.0)
        h2[1] = p2[1] + dvec_b[1] * (1.0/3.0)


def to_bezier(points: Iterable[CurvePointInterface],
              x_range: Optional[Tuple[float, float]]=None,
              y_range: Optional[Tuple[float, float]]=None,
              extrapolate: Optional[bool]=True) -> Tuple[Tuple[Vector, Vector, Vector], ...]:
    data = [(
        pt.location.copy(),
        pt.handle_type,
        Vector((0.0, 0.0)),
        Vector((0.0, 0.0))
        ) for pt in points]

    if x_range:
        alpha, omega = x_range
        if alpha > omega:
            alpha, omega = omega, alpha
            for item in data:
                item[0][0] = 1.0 - item[0][0]
            data.reverse()
        delta = omega - alpha
        for item in data:
            item[0][0] = alpha + item[0][0] * delta

    if y_range:
        alpha, omega = y_range
        delta = omega - alpha
        for item in data:
            item[0][1] = alpha + item[0][1] * delta

    n = len(data) - 1
    for i, (pt, ht, h1, h2) in enumerate(data):
        calc_bezier_handles(pt, ht, h1, h2,
                             data[i-1][0] if i > 0 else None,
                             data[i+1][0] if i < n else None)

    if len(data) > 2:
        ptA, htA, h1A, h2A = data[0]
        ptN, htN, h1N, h2N = data[-1]

        if htA == 'AUTO':
            hlen = (h2A - ptA).length
            hvec = data[1][2].copy()
            if hvec[0] < ptA[0]:
                hvec[0] = ptA[0]

            hvec -= ptA
            nlen = hvec.length
            if nlen > 0.00001:
                hvec *= hlen / nlen
                h2A[0] = hvec[0] + ptA[0]
                h2A[1] = hvec[1] + ptA[1]
                h1A[0] = ptA[0] - hvec[0]
                h1A[1] = ptA[1] - hvec[1]

        if htN == 'AUTO':
            hlen = (h1N - ptN).length
            hvec = data[-2][3].copy()
            if hvec[0] > ptN[0]:
                hvec[0] = ptN[0]

            hvec -= ptN
            nlen = hvec.length
            if nlen > 0.00001:
                hvec *= hlen / nlen
                h1N[0] = hvec[0] + ptN[0]
                h1N[1] = hvec[1] + ptN[1]
                h2N[0] = ptN[0] - hvec[0]
                h2N[1] = ptN[1] - hvec[1]

    if not extrapolate:
        pt = data[0]
        co = pt[0]
        hl = pt[2]
        hl[0] = 0.0
        hl[1] = co[1]

        pt = data[-1]
        co = pt[0]
        hr = pt[3]
        hr[0] = 1.0
        hr[1] = co[1]

    return tuple((item[0], item[2], item[3]) for item in data)


def keyframe_points_assign(points: 'FCurveKeyframePoints',
                           bezier: Sequence[Tuple[Vector, Vector, Vector]]) -> None:

    length = len(points)
    target = len(bezier)

    while length > target:
        points.remove(points[-1])
        length -= 1

    for index, (co, hl, hr) in enumerate(bezier):

        if index < length:
            point = points[index]
        else:
            point = points.insert(co[0], co[1])
            length += 1

        point.interpolation = 'BEZIER'
        point.easing = 'AUTO'
        point.co = co
        point.handle_left_type = 'FREE'
        point.handle_right_type = 'FREE'
        point.handle_left = hl
        point.handle_right = hr

#endregion

#region

class MetaFrame(type):

    def __call__(cls, owner: Identifiable):
        cache = cls._cache
        if cache is None:
            cache = cls._cache = {}
        key = owner.identifier
        dataframe: Optional[DataFrame] = cache.get(key)
        if dataframe:
            dataframe._owner = owner
        else:
            dataframe: DataFrame = super(MetaFrame, cls).__call__(owner)
            cache[key] = dataframe
        return dataframe

Owner = TypeVar("Owner", bound=Identifiable)

class DataFrame(Generic[Owner], metaclass=MetaFrame):

    _cache = None

    def __new__(cls, owner: Owner):
        dataframe = super().__new__(cls)
        dataframe._owner = owner
        return dataframe

    @classmethod
    def delete(cls, owner: Identifiable) -> None:
        try:
            del cls._cache[owner.identifier]
        except KeyError: pass

    @property
    def id(self) -> 'ID':
        return self.object.data

    @property
    def object(self) -> 'Object':
        return self.owner.id_data

    @property
    def owner(self) -> Owner:
        return self._owner

#endregion

#region

def idprop_array(data: Union[Sequence[float], Sequence[Sequence[float]]],
                 name: Optional[str]="") -> np.ndarray:
    shape = np.shape(data)
    dtype = np.dtype([("index", int), ("value", float)], metadata={"propname": name})
    array = np.empty(shape, dtype=dtype)
    array["value"] = data
    return array


def idprop_name(obj: Union[np.ndarray, np.void]) -> str:
    md = obj.dtype.metadata
    return md.get("propname", "") if md else ""


def idprop_path(obj: Union[np.ndarray, np.void]) -> str:
    res = idprop_name(obj)
    if res:
        res = f'["{res}"]'
        if isinstance(obj, np.void):
            res += f'[{obj["index"]}]'
    return res


def idprop_read(id: 'ID', obj: Union[np.ndarray, np.void]) -> Optional[Union[float, List[float]]]:
    data = id.get(idprop_name(obj))
    if isinstance(data, IDPropertyArray):
        n = len(data)
        if isinstance(obj, np.void):
            i = obj["index"]
            return data[i] if i < n else obj["value"]
        return [data[i] if i < n else v for i, v in obj.flat]


def idprop_isvalid(id_: 'ID', obj: Union[np.ndarray, np.void]) -> bool:
    arr = obj.base or obj
    val = id_.get(idprop_name(obj))
    return isinstance(val, IDPropertyArray) and len(val) == arr.size


def idprop_ensure(id_: 'ID', obj: Union[np.ndarray, np.void]) -> None:
    if not idprop_isvalid(id_, obj):
        idprop_update(id_, obj.base or obj)


def idprop_update(id_: 'ID', obj: Union[np.ndarray, np.void]) -> None:
    arr = obj.base or obj
    if arr is obj or not idprop_isvalid(id_, obj):
        id_[idprop_name(arr)] = arr["value"].flatten()
    else:
        val = id_[idprop_name(obj)]
        if isinstance(obj, np.void):
            val[obj["index"]] = obj["value"]
        else:
            for x in obj.flat:
                val[x["index"]] = x["value"]


def idprop_reindex(data: np.ndarray) -> None:
    assert data.base is None
    data["index"] = np.arange(data.size).reshape(data.shape)


def idprop_move(data: np.ndarray,
                from_index: int,
                to_index: int,
                id: Optional['ID']=None,
                move_drivers: Optional[bool]=False) -> None:
    value = None
    if id:
        value = idprop_read(id, data)
    if value is None:
        value = data["value"].tolist()
    value.insert(to_index, value.pop(from_index))
    data["value"] = value
    idprop_reindex(data)
    if id:
        idprop_update(id, data)
        if move_drivers:
            idprop_drivers_move(id, data, from_index, to_index)


def idprop_driver(id: 'ID',
                  prop: np.void,
                  type: Optional[str]="",
                  clear_vars: Optional[bool]=False) -> 'FCurve':
    fx = id.animation_data_create()
    dp = f'["{idprop_name(prop)}"]'
    ai = prop["idx"]
    fc = fx.find(dp, ai) or fx.new(dp, ai)
    dr = fc.driver
    if type:
        dr.type = type
    if clear_vars:
        vs = dr.variables
        ls = list(vs)
        while ls:
            vs.remove(ls.pop())
    return fc


def idprop_drivers(id: 'ID',
                   props: Union[Iterable[np.void], np.void],
                   **kwargs: Dict[str, Union[str, bool]]) -> List['FCurve']:
    return list(map(partial(idprop_driver, id, **kwargs), props))


def idprop_drivers_move(id: 'ID', data: np.ndarray, from_index: int, to_index: int) -> None:
    animdata = id.animation_data
    if animdata:
        a, b = from_index, to_index
        if a > b: a, b = b, a
        idx = list(range(a, b))
        ref = idx.copy()
        ref.append(ref.pop(0))
        path = idprop_path(data)
        for fc in animdata.drivers:
            if fc.data_path == path:
                i = fc.array_index
                if i in idx:
                    fc.array_index = ref[idx.index(i)]


def idprop_variable(driver: 'Driver', object: 'Object', data: np.void) -> 'DriverVariable':
    vars = driver.variables

    for k in ascii_letters:
        if k not in vars:
            break

    var = vars.new()
    var.type = 'SINGLE_PROP'
    var.name = k

    tgt = var.targets[0]
    tgt.id_type = object.type
    tgt.id = object.data
    tgt.data_path = idprop_path(data)

    return var


def idprop_variables(driver: 'Driver',
                     object: 'Object',
                     data: Iterable[np.void]) -> List['DriverVariable']:
    return list(map(partial(idprop_variable, driver, object), data))


#endregion