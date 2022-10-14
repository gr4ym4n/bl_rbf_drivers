
# input
# - {variable} [value, {value}, value]
# -  variable  [value,  value , value]
# + controller [....., {.....}, .....]


from math import acos, asin, fabs, pi
from typing import TYPE_CHECKING, Any, Dict, Iterator, List, Optional, Tuple, Union
from logging import getLogger
import numpy as np
from bpy.types import Object, PropertyGroup
from bpy.props import (BoolProperty,
                       CollectionProperty,
                       EnumProperty,
                       FloatProperty,
                       IntProperty,
                       IntVectorProperty,
                       PointerProperty,
                       StringProperty)
from .. import utils_
from ..utils_ import resolve
from .mixins import Observable, Identifiable
if TYPE_CHECKING:
    from bpy.types import ID, PoseBone
    from mathutils import Matrix

log = getLogger(__name__)


TRANSFORM_SPACE_ITEMS = [
    ('WORLD_SPACE'    , "World Space"    , "Transforms include effects of parenting/restpose and constraints"    ),
    ('TRANSFORM_SPACE', "Transform Space", "Transforms don't include parenting/restpose or constraints"          ),
    ('LOCAL_SPACE'    , "Local Space"    , "Transforms include effects of constraints but not parenting/restpose"),
    ]

TRANSFORM_SPACE_TABLE = {
    _item[0]: _index for _index, _item in enumerate(TRANSFORM_SPACE_ITEMS)
    }

def _get_transform_subject(object_: Optional[Object], bone: str) -> Optional[Union[Object, 'PoseBone']]:
    if object_ and object_.type == 'ARMATURE' and bone:
        return object_.pose.bones.get(bone)
    return object_


def _get_transform_matrix(subject: Union[Object, 'PoseBone'], space: str) -> 'Matrix':
    if isinstance(subject, Object):
        if space == 'TRANSFORM_SPACE': return subject.matrix_basis
        if space == 'WORLD_SPACE'    : return subject.matrix_world
        return subject.matrix_local
    if space == 'TRANSFORM_SPACE':
        return subject.matrix_channel
    return subject.id_data.convert_space(
        pose_bone=subject,
        mamtrix=subject.matrix,
        from_space='POSE',
        to_space=space[:5])


def _get_transform_element(matrix: 'Matrix', type_: str, mode: str) -> float:
    axis = type_[-1]
    if type_.startswith('LOC'):
        return matrix.to_translation()['XYZ'.index(axis)]
    if type_.startswith('SCALE'):
        return matrix.to_scale()['XYZ'.index(axis)]
    if mode == 'AUTO':
        return 0.0 if axis == 'W' else matrix.to_euler()['XYZ'.index(axis)]
    if len(mode) == 3:
        return matrix.to_euler(mode)['XYZ'.index(axis)]
    if mode == 'QUATERNION':
        return matrix.to_quaternion()['WXYZ'.index(axis)]
    twist_axis = mode[-1]
    swing, twist = matrix.to_quaternion().to_swing_twist(twist_axis)
    if axis == twist_axis:
        return twist
    value = swing['WXYZ'.index(axis)]
    return (acos if axis == 'W' else asin)(value) * 2.0


def _calc_distance(target_1: Union[Object, 'PoseBone'], space_1: str,
                   target_2: Union[Object, 'PoseBone'], space_2: str) -> float:
    m1 = _get_transform_matrix(target_1, space_1)
    m2 = _get_transform_matrix(target_2, space_2)
    return (m1.to_translation() - m2.to_translation()).length


# https://github.com/blender/blender/blob/594f47ecd2d5367ca936cf6fc6ec8168c2b360d0/source/blender/blenkernel/intern/fcurve_driver.c
def _calc_rotational_difference(target_1: Union[Object, 'PoseBone', None],
                                target_2: Union[Object, 'PoseBone', None]) -> float:
    q1 = _get_transform_matrix(target_1).to_quaternion()
    q2 = _get_transform_matrix(target_2).to_quaternion()
    angle = fabs(2.0 * acos((q1.inverted() * q2)[0]))
    return 2.0 * pi - angle if angle > pi else angle


#region InputTarget
#--------------------------------------------------------------------------------------------------

INPUT_TARGET_ID_TYPE_ITEMS = [
    ('OBJECT'     , "Object"  , "", 'OBJECT_DATA',                0),
    ('MESH'       , "Mesh"    , "", 'MESH_DATA',                  1),
    ('CURVE'      , "Curve"   , "", 'CURVE_DATA',                 2),
    ('SURFACE'    , "Surface" , "", 'SURFACE_DATA',               3),
    ('META'       , "Metaball", "", 'META_DATA',                  4),
    ('FONT'       , "Font"    , "", 'FONT_DATA',                  5),
    ('HAIR'       , "Hair"    , "", 'HAIR_DATA',                  6),
    ('POINTCLOUD' , "Point"   , "", 'POINTCLOUD_DATA',            7),
    ('VOLUME'     , "Volume"  , "", 'VOLUME_DATA',                8),
    ('GPENCIL'    , "GPencil" , "", 'OUTLINER_DATA_GREASEPENCIL', 9),
    ('ARMATURE'   , "Armature", "", 'ARMATURE_DATA',              10),
    ('LATTICE'    , "Lattice" , "", 'LATTICE_DATA',               11),
    ('EMPTY'      , "Empty"   , "", 'EMPTY_DATA',                 12),
    ('LIGHT'      , "Light"   , "", 'LIGHT_DATA',                 13),
    ('LIGHT_PROBE', "Light"   , "", 'OUTLINER_DATA_LIGHTPROBE',   14),
    ('CAMERA'     , "Camera"  , "", 'CAMERA_DATA',                15),
    ('SPEAKER'    , "Speaker" , "", 'OUTLINER_DATA_SPEAKER',      16),
    ('KEY'        , "Key"     , "", 'SHAPEKEY_DATA',              17),
    ]

INPUT_TARGET_ID_TYPE_TABLE = {
    _item[0]: _item[4] for _item in INPUT_TARGET_ID_TYPE_ITEMS
    }

INPUT_TARGET_ROTATION_MODE_ITEMS = [
    ('AUTO'         , "Auto Euler"       , "Euler using the rotation order of the target"                                  ),
    ('XYZ'          , "XYZ Euler"        , "Euler using the XYZ rotation order"                                            ),
    ('XZY'          , "XZY Euler"        , "Euler using the XZY rotation order"                                            ),
    ('YXZ'          , "YXZ Euler"        , "Euler using the YXZ rotation order"                                            ),
    ('YZX'          , "YZX Euler"        , "Euler using the YZX rotation order"                                            ),
    ('ZXY'          , "ZXY Euler"        , "Euler using the ZXY rotation order"                                            ),
    ('ZYX'          , "ZYX Euler"        , "Euler using the ZYX rotation order"                                            ),
    ('QUATERNION'   , "Quaternion"       , "Quaternion rotation"                                                           ),
    ('SWING_TWIST_X', "Swing and X Twist", "Decompose into a swing rotation to aim the X axis, followed by twist around it"),
    ('SWING_TWIST_Y', "Swing and Y Twist", "Decompose into a swing rotation to aim the Y axis, followed by twist around it"),
    ('SWING_TWIST_Z', "Swing and Z Twist", "Decompose into a swing rotation to aim the Z axis, followed by twist around it"),
    ]

INPUT_TARGET_ROTATION_MODE_TABLE = {
    _item[0]: _index for _index, _item in enumerate(INPUT_TARGET_ROTATION_MODE_ITEMS)
    }

INPUT_TARGET_TRANSFORM_TYPE_ITEMS = [
    ('LOC_X'  , "X Location", ""),
    ('LOC_Y'  , "Y Location", ""),
    ('LOC_Z'  , "Z Location", ""),
    ('ROT_W'  , "W Rotation", ""),
    ('ROT_X'  , "X Rotation", ""),
    ('ROT_Y'  , "Y Rotation", ""),
    ('ROT_Z'  , "Z Rotation", ""),
    ('SCALE_X', "X Scale"   , ""),
    ('SCALE_Y', "Y Scale"   , ""),
    ('SCALE_Z', "Z Scale"   , ""),
    ]

INPUT_TARGET_TRANSFORM_TYPE_TABLE = {
    _item[0]: _index for _index, _item in enumerate(INPUT_TARGET_TRANSFORM_TYPE_ITEMS)
    }


def input_target_bone_target_get(target: 'InputTarget') -> str:
    return target.get("bone_target", "")


def input_target_bone_target_set(target: 'InputTarget', value: str) -> None:
    input_ = _input_resolve(target)
    if input_.type == 'USER_DEF':
        cache = target.bone_target
        target["bone_target"] = value
        target.notify_observers("bone_target", value, cache)
    else:
        log.warning(f'{target}.bone_target is read-only for inputs of type {input_.type}')


def _input_target_data_path_get(target: 'InputTarget') -> str:
    return target.get("data_path", "")


def _input_target_data_path_set(target: 'InputTarget', value: str) -> None:
    input_ = _input_resolve(target)
    if input_.type == 'USER_DEF':
        cache = target.data_path
        target["data_path"] = value
        target.notify_observers("data_path", value, cache)
    else:
        log.warning(f'{target}.data_path is read-only for inputs of type {input_.type}')


def _input_target_id_type_get(target: 'InputTarget') -> str:
    return target.get("id_type", 0)


def _input_target_id_type_set(target: 'InputTarget', value: int) -> None:
    input_ = _input_resolve(target)
    if input_.type == 'USER_DEF':
        cache = target.id_type
        target["id_type"] = value
        object_ = target.object
        if object_ and not _input_target_object_poll(target, object_):
            target.property_unset("object__internal__")
            target.property_unset("object")
            target.notify_observers("object", None, object_)
        target.notify_observers("id_type", target.id_type, cache)
    else:
        log.warning(f'{target}.id_type is read-only for inputs of type {input_.type}')


def _input_target_object_poll(target: 'InputTarget', value: Object) -> bool:
    return target.id_type in (value.type, 'OBJECT')


def _input_target_object_update_handler(target: 'InputTarget', _) -> None:
    cache = target.object__internal__
    value = target.object
    target.object__internal__ = value
    target.notify_observers("object", value, cache)


def _input_target_rotation_mode_get(target: 'InputTarget') -> str:
    return target.get("rotation_mode", 0)


def _input_target_rotation_mode_set(target: 'InputTarget', value: int) -> None:
    input_ = _input_resolve(target)
    if input_.type == 'USER_DEF':
        cache = target.rotation_mode
        target["rotation_mode"] = value
        target.notify_observers("rotation_mode", target.rotation_mode, cache)
    else:
        log.warning(f'{target}.rotation_mode is read-only for inputs of type {input_.type}')


def _input_target_transform_space_get(target: 'InputTarget') -> str:
    return target.get("transform_space", 0)


def _input_target_transform_space_set(target: 'InputTarget', value: int) -> None:
    input_ = _input_resolve(target)
    if input_.type == 'USER_DEF':
        cache = target.transform_space
        target["transform_space"] = value
        target.notify_observers("transform_space", target.transform_space, cache)
    else:
        log.warning(f'{target}.transform_space is read-only for inputs of type {input_.type}')


def _input_target_transform_type_get(target: 'InputTarget') -> str:
    return target.get("transform_type", 0)


def _input_target_transform_type_set(target: 'InputTarget', value: int) -> None:
    input_ = _input_resolve(target)
    if input_.type == 'USER_DEF':
        cache = target.transform_type
        target["transform_type"] = value
        target.notify_observers("transform_type", target.transform_type, cache)
    else:
        log.warning(f'{target}.transform_type is read-only for inputs of type {input_.type}')


class InputTarget(Observable, PropertyGroup):

    bone_target: StringProperty(
        name="Bone",
        description="Pose bone target",
        get=input_target_bone_target_get,
        set=input_target_bone_target_set,
        options=set(),
        )

    data_path: StringProperty(
        name="Data",
        description="Path to target property",
        get=_input_target_data_path_get,
        set=_input_target_data_path_set,
        options=set(),
        )

    id_type: EnumProperty(
        name="Type",
        description="ID data-block type",
        items=INPUT_TARGET_ID_TYPE_ITEMS,
        get=_input_target_id_type_get,
        get=_input_target_id_type_set,
        options=set(),
        )

    @property
    def id(self) -> Optional['ID']:
        object = self.object
        if object is None or self.id_type == 'OBJECT': return object
        if object.type == self.id_type: return object.data

    object__internal__: PointerProperty(
        type=Object,
        options={'HIDDEN'}
        )

    object: PointerProperty(
        name="Object",
        description="The target object",
        type=Object,
        poll=_input_target_object_poll,
        update=_input_target_object_update_handler,
        options=set(),
        )

    rotation_mode: EnumProperty(
        name="Mode",
        description="The input rotation mode",
        items=INPUT_TARGET_ROTATION_MODE_ITEMS,
        get=_input_target_rotation_mode_get,
        set=_input_target_rotation_mode_set,
        options=set(),
        )

    transform_space: EnumProperty(
        name="Space",
        description="Transform channel space",
        items=TRANSFORM_SPACE_ITEMS,
        get=_input_target_transform_space_get,
        set=_input_target_transform_space_set,
        options=set(),
        )

    transform_type: EnumProperty(
        name="Type",
        description="Transform channel type",
        items=INPUT_TARGET_TRANSFORM_TYPE_ITEMS,
        get=_input_target_transform_type_get,
        set=_input_target_transform_type_set,
        options=set(),
        )

    def __str__(self) -> str:
        return f'{self.__class__.__name__}@{self.path_from_id().replace("internal__", "")}'

#endregion InputTarget

#region InputTargets
#--------------------------------------------------------------------------------------------------

class InputTargets(PropertyGroup):

    internal__: CollectionProperty(
        type=InputTarget,
        options={'HIDDEN'}
        )

    def __len__(self) -> int:
        return len(self.internal__)

    def __iter__(self) -> Iterator[InputTarget]:
        return iter(self.internal__)

    def __getitem__(self, key: Union[int, slice]) -> Union[InputTarget, List[InputTarget]]:
        return self.internal__[key]

    def __str__(self) -> str:
        return f'{self.__class__.__name__}@{self.path_from_id().replace("internal__", "")}'

#endregion InputTarget

#region InputSample
#--------------------------------------------------------------------------------------------------

def _input_sample_angle_get(sample: 'InputSample') -> float:
    return sample.value


def _input_sample_angle_set(sample: 'InputSample', value: float) -> None:
    sample.value = value


def _input_sample_name_get(sample: 'InputSample') -> str:
    return sample.get("name", "")


def _input_sample_name_set(sample: 'InputSample', _) -> None:
    raise RuntimeError('InputSample.name is read-only')


def _input_sample_value_get(sample: 'InputSample') -> float:
    if sample.is_property_set("value"):
        return sample.get("value")
    return resolve(sample, ".data").default_value


def _input_sample_value_set(sample: 'InputSample', value: float) -> None:
    cache = sample.value
    sample["value"] = value
    sample.notify_observers("value", value, cache)
    resolve(sample, ".variables").distance_matrix.update()


class InputSample(Observable, PropertyGroup):

    angle: FloatProperty(
        name="Value",
        description="Input sample value",
        subtype='ANGLE',
        get=_input_sample_angle_get,
        set=_input_sample_angle_set,
        options=set()
        )

    name: StringProperty(
        name="Name",
        description="The name of the corresponding pose",
        get=_input_sample_name_get,
        set=_input_sample_name_set,
        options=set()
        )

    value: FloatProperty(
        name="Value",
        description="Input sample value",
        get=_input_sample_value_get,
        set=_input_sample_value_set,
        options=set(),
        )

    def normalized(self) -> float:
        return self.get("value_normalized", self.value)

    def __init__(self, **properties: Dict[str, Any]) -> None:
        for key, value in properties.items():
            self[key] = value

#endregion InputSample

#region InputData
#--------------------------------------------------------------------------------------------------

def _input_data_is_normalized(data: 'InputData') -> bool:
    return data.get("is_normalized", False)


def _input_data_norm(data: 'InputData') -> float:
    return data.get("norm", np.linalg.norm(list(data.values())))


class InputData(PropertyGroup):

    internal__: CollectionProperty(
        type=InputSample,
        options=set()
        )

    is_normalized: BoolProperty(
        name="Normalized",
        get=_input_data_is_normalized,
        options=set()
        )

    norm: FloatProperty(
        name="Norm",
        get=_input_data_norm,
        options=set()
        )

    def __iter__(self) -> Iterator[InputSample]:
        return iter(self.internal__)

    def __len__(self) -> int:
        return len(self.internal__)

    def __getitem__(self, key: Union[str, int, slice]) -> Union[InputSample, List[InputSample]]:
        return self.internal__[key]

    def get(self, name: str) -> Optional[InputSample]:
        return self.internal__.get(name)

    def values(self, normalized: Optional[bool]=False) -> Iterator[float]:
        if normalized:
            for sample in self:
                yield sample.normalized()
        else:
            for sample in self:
                yield sample.value

    def update(self) -> None:
        if self.is_normalized:
            norm = self["norm"] = np.linalg.norm(tuple(self.values()))
            if norm != 0.0:
                for sample in self:
                    sample["value_normalized"] = sample.value / norm
            else:
                for sample in self:
                    sample["value_normalized"] = sample.value

#endregion InputData

#region InputVariable
#--------------------------------------------------------------------------------------------------


INPUT_VARIABLE_TYPE_ITEMS = [
    ('SINGLE_PROP'  , "Single Property"      , "Use the value from some RNA property (Default).", 'RNA'                         , 0),
    ('TRANSFORMS'   , "Transform Channel"    , "Final transformation value of object or bone."  , 'DRIVER_TRANSFORM'            , 1),
    ('ROTATION_DIFF', "Rotational Difference", "Use the angle between two bones."               , 'DRIVER_ROTATIONAL_DIFFERENCE', 2),
    ('LOC_DIFF'     , "Distance"             , "Distance between two bones or objects."         , 'DRIVER_DISTANCE'             , 3),
    ]

INPUT_VARIABLE_TYPE_TABLE = {
    _item[0]: _item[4] for _item in INPUT_VARIABLE_TYPE_ITEMS
    }


def _input_variable_enable_get(variable: 'InputVariable') -> bool:
    return variable.get("enable", False)


def _input_variable_enable_set(variable: 'InputVariable', value: bool) -> None:
    input_ = _input_resolve(variable)
    if input_.type == 'ROTATION' and input_.rotation_mode in {'QUATERNION', 'SWING', 'TWIST'}:
        raise RuntimeError((f'InputVariable.enable is not writable for'
                            f'inputs of type {input_.type} with '
                            f'rotation_mode {input_.rotation_mode}'))
    cache = _input_variable_enable_get(variable)
    if cache != value:
        variable["enable"] = value
        variable.notify_observers("enabled" if value else "disabled")


def _input_variable_name_get(variable: 'InputVariable') -> str:
    return variable.get("name", "")


def _input_variable_name_set(variable: 'InputVariable', name: str) -> None:
    owner = _input_resolve(variable)
    cache = variable.name
    names = list(owner.variables.keys())
    index = 0
    value = name
    while value in names:
        index += 1
        value = f'{value}_{str(index).zfill(2)}'
    variable["name"] = value
    variable.notify_observers("name", value, cache)


def _input_variable_type_get(variable: 'InputVariable') -> int:
    return variable.get("type", 0)


def _input_variable_type_set(variable: 'InputVariable', value: int) -> None:
    input_ = _input_resolve(variable)
    if input_.type == 'USER_DEF':
        cache = variable.type
        variable["type"] = value
        targets: InputTargets = variable.targets
        if input_.type.endswith('DIFF'):
            if len(targets) < 2:
                targets.internal__.add()
        elif len(targets) > 1:
            targets.internal__.remove(1)
        variable.notify_observers("type", variable.type, cache)
    else:
        log.warning(f'{variable}.type is read-only for inputs of type {input_.type}')


class InputVariable(Observable, PropertyGroup):

    data: PointerProperty(
        name="Data",
        type=InputData,
        options=set()
        )

    default_value: FloatProperty(
        name="Default",
        default=0.0,
        options=set()
        )

    enable: BoolProperty(
        name="Enable",
        get=_input_variable_enable_get,
        set=_input_variable_enable_set,
        options=set()
        )

    @property
    def is_valid(self) -> bool:
        type_: str = self.type
        if type_.endswith('DIFF'):
            for target in self.targets:
                object_ = target.object
                if object_ is None:
                    return False
                if object_.type == 'ARMATURE':
                    bone = target.bone_target
                    if bone and bone in object_.data.bones:
                        return False
            return True
        target = self.targets[0]
        object_ = target.object
        if object_ is None:
            return False
        if type_ == 'SINGLE_PROP':            
            idtype = target.id_type
            if idtype != 'OBJECT':
                if object_.type != idtype:
                    return False
                id = object_.data
            else:
                id = object_
            try:
                value = id.path_resolve(target.data_path)
            except ValueError:
                return False
            else:
                return isinstance(value, (bool, int, float))
        else: #type_ == 'TRANSFORMS':
            if object_.type == 'ARMATURE':
                bone = target.bone_target
                if bone:
                    return bone in object_.data.bones
            return True

    name: StringProperty(
        name="Name",
        default="var",
        get=_input_variable_name_get,
        set=_input_variable_name_set,
        options=set(),
        )

    targets: PointerProperty(
        name="Targets",
        type=InputTargets,
        options=set()
        )

    type: EnumProperty(
        name="Type",
        items=INPUT_VARIABLE_TYPE_ITEMS,
        get=_input_variable_type_get,
        set=_input_variable_type_set,
        options=set(),
        )

    show_expanded: BoolProperty(
        name="Expand",
        description="Show/hide settings",
        default=False,
        options=set()
        )

    @property
    def value(self) -> float:
        type_ = self.type
        if type_ == 'TRANSFORMS':
            target = self.targets[0]
            subject = _get_transform_subject(target.object, target.bone_target)
            if subject:
                matrix = _get_transform_matrix(subject, target.transform_space)
                return _get_transform_element(matrix, target.transform_type, target.rotation_mode)
        elif type_.endswith('DIFF'):
            target_a = self.targets[0]
            target_b = self.targets[1]
            subject_a = _get_transform_subject(target_a.object, target_a.bone_target)
            subject_b = _get_transform_subject(target_b.object, target_b.bone_target)
            if subject_a and subject_b:
                if type_ == 'LOC_DIFF':
                    return _calc_distance(subject_a, target_a.transform_space,
                                          subject_b, target_b.transform_space)
                else:
                    return _calc_rotational_difference(subject_a, subject_b)
        else:
            target = self.targets[0]
            id_ = target.id
            if id_:
                try:
                    value = id_.path_resolve(target.data_path)
                except ValueError:
                    pass
                else:
                    if isinstance(value, (float, int, bool)):
                        return float(value)
        return 0.0
        


    def __str__(self) -> str:
        return f'{self.__class__.__name__}@{self.path_from_id().replace("internal__", "")}'


#endregion InputVariable

#region InputVariables
#--------------------------------------------------------------------------------------------------


class InputVariables(Observable, PropertyGroup):

    active_index: IntProperty(
        name="Shape Key",
        min=0,
        default=0,
        options=set()
        )

    @property
    def active(self) -> Optional[InputVariable]:
        index = self.active_index
        return self[index] if index < len(self) else None

    internal__: CollectionProperty(
        type=InputVariable,
        options={'HIDDEN'}
        )

    def __iter__(self) -> Iterator[InputVariable]:
        return iter(self.internal__)

    def __len__(self) -> int:
        return len(self.internal__)

    def __getitem__(self, key: Union[str, int, slice]) -> Union[InputVariable, List[InputVariable]]:
        return self.internal__[key]

    def __str__(self) -> str:
        return f'{self.__class__.__name__}@{self.path_from_id().replace("internal__", "")}'

    def items(self) -> Iterator[Tuple[str, InputVariable]]:
        return self.internal__.items()

    def keys(self) -> Iterator[str]:
        return self.internal__.keys()

    def new(self, name: Optional[str]="") -> InputVariable:
        input_: Input = self.id_data.path_resolve(self.path_from_id().rpartition(".")[0])

        if input_.type not in {'USER_DEF', 'SHAPE_KEY'}:
            raise RuntimeError((f'{self.__class__.__name__}.new(): '
                                f'Variables are not mutable for inputs of type {input_.type}'))

        if len(self) >= 16:
            raise RuntimeError((f'{self.__class__.__name__}.new(): '
                                f'Maximum number of variables per input (16) exceeded'))

        variable: InputVariable = self.internal__.add()
        variable["name"] = name

        target = variable.targets.internal__.add()
        if input_.type == 'SHAPE_KEY':
            target.id_type = 'KEY'
            target.object = input_.object
            target.data_path = f'key_blocks["{name}"].value'

        self.notify_observers("new", variable)
        return variable

    def remove(self, variable: InputVariable) -> None:
        input_: Input = self.id_data.path_resolve(self.path_from_id().rpartition(".")[0])
        if input_.type not in {'USER_DEF', 'SHAPE_KEY'}:
            raise RuntimeError((f'{self.__class__.__name__}.new(): '
                                f'Variables are not mutable for inputs of type {input_.type}'))
        if not isinstance(variable, InputVariable):
            raise TypeError((f'{self.__class__.__name__}.remove(variable): '
                             f'Expected variable to be {InputVariable.__class__.__name__}, '
                             f'not {variable.__class__.__name__}'))
        index = next((index for index, item in enumerate(self) if item == variable), -1)
        if index == -1:
            raise ValueError((f'{self.__class__.__name__}.remove(variable): '
                              f'{variable} is not a member of this collection'))
        if len(self) == 1:
            raise RuntimeError((f'{self.__class__.__name__}.remove(variable): '
                                f'Inputs must have at least one variable to remain operational'))
        self.notify_observers("removing", variable)
        self.internal__.remove(index)

#endregion InputVariables

#region InputDistanceMatrix
#--------------------------------------------------------------------------------------------------

def input_distance_value_get(distance: 'InputDistance') -> float:
    return distance.get("value", 0.0)


class InputDistance(PropertyGroup):

    value: FloatProperty(
        name="Value",
        get=input_distance_value_get,
        options=set()
        )


class InputDistanceMatrixRow:

    def __init__(self, matrix: 'InputDistanceMatrix', offset: int) -> None:
        self._matrix = matrix
        self._offset = offset

    def __iter__(self) -> Iterator[float]:
        matrix = self._matrix
        ncols = matrix.shape[1]
        index = self._offset * ncols
        limit = index + ncols
        items = matrix.items__
        while index < limit:
            yield items[index].value
            index += 1

    def __len__(self) -> int:
        return self._matrix.shape[1]

    def __getitem__(self, key: Union[str, int, slice]) -> Union[float, List[float]]:
        if isinstance(key, str):
            index = self._matrix.index__.find(key)
            if index == -1:
                raise KeyError()
            return self[index]
        if isinstance(key, int):
            if key >= len(self):
                raise IndexError()
            index = self._offset * self._matrix.shape[1] + key
            return self._matrix.items__[index]


class InputDistanceMatrixColumn(PropertyGroup):

    def __init__(self, matrix: 'InputDistanceMatrix', offset: int) -> None:
        self._matrix = matrix
        self._offset = offset

    def __len__(self) -> int:
        return self._matrix.shape[0]


def input_distance_matrix_shape_get(matrix: 'InputDistanceMatrix') -> Tuple[int, int]:
    return matrix.get("shape", (0, 0))


class InputDistanceMatrix(PropertyGroup):

    index__: CollectionProperty(
        type=PropertyGroup,
        options={'HIDDEN'}
        )

    items__: CollectionProperty(
        type=InputDistance,
        options={'HIDDEN'}
        )

    shape: IntVectorProperty(
        name="Shape",
        size=2,
        get=input_distance_matrix_shape_get,
        options=set()
        )

    @property
    def size(self) -> int:
        nrows, ncols = self.shape
        return nrows * ncols

    def __iter__(self) -> Iterator[InputDistanceMatrixRow]:
        for offset in range(self.shape[0]):
            yield InputDistanceMatrixRow(self, offset)

    def __len__(self) -> int:
        return self.shape[0]

    def __getitem__(self, key: Union[str, int, tuple]) -> Union[InputDistanceMatrixColumn,
                                                                InputDistanceMatrixRow,
                                                                float]:
        if isinstance(key, str):
            index = self.index__.find(key)
            if index == -1:
                raise KeyError()
            return InputDistanceMatrixColumn(self, index)
        if isinstance(key, int):
            index = self.shape[0] + key if key < 0 else key
            if 0 > key >= self.shape[0]:
                raise IndexError()
            return InputDistanceMatrixRow(self, index)
        if isinstance(key, tuple):
            row = key[0]
            col = key[1]
            if row < 0:
                row = self.shape[0] + row
            if 0 > row >= self.shape[0]:
                raise IndexError()
            if col < 0:
                col = self.shape[1] + col
            if 0 > col >= self.shape[1]:
                raise IndexError()
            index = row * self.shape[1] + col
            return self.items__[index].value
        raise TypeError()

    def update(self) -> None:
        input_ = resolve(self, ".")
        values = [v.data.values(v.data.is_normalized) for v in input_.variables if v.enable]
        params = np.array(values, dtype=float).T
        result = np.empty((len(params), len(params)), dtype=float)
        metric = getattr(utils_, f'distance_{input_.distance_metric.lower()}')
        matrix = input_.distance_matrix
        for a, row in zip(params, result):
            for i, b in enumerate(params):
                row[i] = metric(a, b)
        items = matrix.items__
        items.clear()
        for value in result.flat:
            items.add()["value"] = value
        input_.notify_observers("distance_matrix", matrix)
        input_.pose_radii.update()

#endregion

#region InputPoseRadii
#--------------------------------------------------------------------------------------------------

def input_radius_name_get(radius: 'InputPoseRadius') -> str:
    return radius.get("name", "")


def input_radius_name_set(radius: 'InputPoseRadius', _) -> None:
    raise RuntimeError("InputPoseRadius.name is read-only")


def input_radius_value_get(radius: 'InputPoseRadius') -> float:
    return radius.get("value", 0.0)


class InputPoseRadius(PropertyGroup):

    name: StringProperty(
        name="Name",
        description="Unique pose name",
        get=input_radius_name_get,
        set=input_radius_name_set,
        options=set()
        )

    value: FloatProperty(
        name="Value",
        description="",
        get=input_radius_value_get,
        options=set()
        )

class InputPoseRadii(Identifiable, PropertyGroup):

    internal__: CollectionProperty(
        type=InputPoseRadius,
        options={'HIDDEN'}
        )

    def __iter__(self) -> Iterator[float]:
        for radius in self.internal__:
            yield radius.value

    def __len__(self) -> int:
        return len(self.internal__)

    def __getitem__(self, key: Union[str, int]) -> Union[float, List[float]]:
        if isinstance(key, str):
            index = self.internal__.find(key)
            if index == -1:
                raise KeyError()
            return self.internal__[index].value
        if isinstance(key, int):
            index = len(self) + key if key < 0 else key
            if 0 > index >= len(self):
                raise IndexError()
            return self.internal__[index].value
        raise TypeError()

    def items(self) -> Iterator[Tuple[str, float]]:
        for radius in self.internal__:
            yield radius.name, radius.value

    def keys(self) -> Iterator[str]:
        return self.internal__.keys()

    def values(self) -> Iterator[float]:
        return iter(self)

    def update(self) -> None:
        input_ = resolve(self, ".")
        matrix = input_.distance_matrix
        values = np.array(matrix.size, dtype=np.float)
        matrix.items__.foreach_get("value", values)
        values.shape = tuple(matrix.shape)
        radii = self.internal__
        for radius, row in zip(radii, np.ma.masked_values(values, 0.0, atol=0.001)):
            row = row.compressed()
            radius["value"] = 0.0 if len(row) == 0 else np.min(row)
        input_.notify_observers("pose_radii", input_.pose_radii)


#endregion

#region Input
#--------------------------------------------------------------------------------------------------

INPUT_DISTANCE_METRIC_ITEMS = [
    ('EUCLIDEAN', "Euclidean", "Euclidean distance"),
    ('ANGLE', "Agnel", "Anglular difference"),
    ('QUATERNION', "Quaternion", "Quaternion distance"),
    ('DIRECTION', "Direction", "Aim vector difference"),
    ]

INPUT_DISTANCE_METRIC_TABLE = {
    _item[0]: _index for _index, _item in enumerate(INPUT_DISTANCE_METRIC_ITEMS)
    }

INPUT_TYPE_ITEMS = [
    ('LOCATION', "Location", "Location transform channels", 'CON_LOCLIMIT' , 0),
    ('ROTATION', "Rotation", "Rotation transform channels", 'CON_ROTLIMIT' , 1),
    ('SCALE', "Scale", "Scale transform channels", 'CON_SIZELIMIT', 2),
    None,
    ('ROTATION_DIFF', "Rotational Difference", "Angle between two bones or objects.", 'DRIVER_ROTATIONAL_DIFFERENCE', 3),
    ('LOC_DIFF', "Distance", "Distance between two bones or objects.", 'DRIVER_DISTANCE', 4),
    None,
    ('SHAPE_KEY', "Shape Keys" , "Shape key values", 'SHAPEKEY_DATA', 5),
    ('USER_DEF', "User-defined", "Fully configurable input values", 'RNA', 6),
    ]

INPUT_TYPE_INDEX = [
    _item[0] for _item in INPUT_TYPE_ITEMS if _item is not None
    ]


def _input_bone_target_get(input_: 'Input') -> str:
    return input_.get("bone_target", "")


def _input_bone_target_set(input_: 'Input', value: str) -> None:
    cache = input_.bone_target
    input_["bone_target"] = value
    if input_.type in {'LOCATION', 'ROTATION', 'SCALE'}:
        for variable in input_.variables:
            variable.targets[0].bone_target = value
    input_.notify_observers("bone_target", value, cache)


def _input_data_type_get(input_: 'Input') -> int:
    return input_.get("data_type", 0)


def _input_data_type_set(input_: 'Input', value: int) -> None:
    cache = input_.data_type
    input_["data_type"] = value
    input_.notify_observers("data_type", input_.data_type, cache)


def input_distance_metric_get(input_: 'Input') -> int:
    type_ = input_.type
    if type_ == 'ROTATION':
        mode = input_.rotation_mode
        if mode == 'QUATERNION': return INPUT_DISTANCE_METRIC_TABLE['QUATERNION']
        if mode == 'SWING': return INPUT_DISTANCE_METRIC_TABLE['DIRECTION']
        if mode == 'TWIST': return INPUT_DISTANCE_METRIC_TABLE['ANGLE']
    return INPUT_DISTANCE_METRIC_TABLE['EUCLIDEAN']


def _input_is_enabled(input_: 'Input') -> bool:
    return any(variable.enable for variable in input_.variables)


def _input_object_poll(input_: 'Input', object_: Object) -> bool:
    return input_.type != 'SHAPE_KEY' or object_.type in {'MESH', 'LATTICE', 'CURVE'}


def _input_object_update_handler(input_: 'Input', _) -> None:
    cache = input_.object__internal__
    value = input_.object
    input_.object__internal__ = value
    if input_.type in {'LOCATION', 'ROTATION', 'SCALE', 'SHAPE_KEY'}:
        for variable in input_.variables:
            variable.targets[0].object = value
    input_.notify_observers("object", value, cache)


def _input_rotation_axis_get(input_: 'Input') -> int:
    return input_.get("rotation_axis", 1)


def _input_rotation_axis_set(input_: 'Input', value: int) -> None:
    cache = input_.rotation_axis
    input_["rotation_axis"] = value
    input_.notify_observers("rotation_axis", input_.rotation_axis, cache)


def _input_rotation_mode_get(input_: 'Input') -> int:
    return input_.get("rotation_mode", 0)


def _input_rotation_mode_set(input_: 'Input', value: int) -> None:
    cache = input_.rotation_mode
    input_["rotation_mode"] = value
    input_.notify_observers("rotation_mode", input_.rotation_mode, cache)


def _input_rotation_order_get(input_: 'Input') -> int:
    return input_.get("rotation_order", 0)


def _input_rotation_order_set(input_: 'Input', value: int) -> None:
    cache = input_.rotation_order
    input_["rotation_order"] = value
    input_.notify_observers("rotation_order", input_.rotation_order, cache)


def _input_transform_space_get(input_: 'Input') -> int:
    return input_.get("transform_space", 2)


def _input_transform_space_set(input_: 'Input', value: int) -> int:
    cache = input_.transform_space
    input_["transform_space"] = value
    input_.notify_observers("transform_space", input_.transform_space, cache)


def _input_type_get(input_: 'Input') -> int:
    return input_.get("type", 6)


class Input(Observable, PropertyGroup):

    bone_target: StringProperty(
        name="Bone",
        description="The pose bone to use as the input target",
        get=_input_bone_target_get,
        set=_input_bone_target_set,
        options=set()
        )

    data_type: EnumProperty(
        name="Type",
        description="Data type",
        items=[
            ('FLOAT'     , "Float"     , "Floating point value"),
            ('ANGLE'     , "Angle"     , "Euler Angles"        ),
            ('QUATERNION', "Quaternion", "Quaternion rotation" ),
            ],
        get=_input_data_type_get,
        set=_input_data_type_set,
        options=set(),
        )

    distance_matrix: PointerProperty(
        name="Distance Matrix",
        description="Input distance matrix",
        type=InputDistanceMatrix,
        options=set()
        )

    distance_metric: EnumProperty(
        name="Distance Metric",
        description="Input distance metric",
        items=INPUT_DISTANCE_METRIC_ITEMS,
        get=input_distance_metric_get,
        options=set()
        )

    is_enabled: BoolProperty(
        name="Enabled",
        description="Whether the input has at least one enabled variable",
        get=_input_is_enabled,
        options=set()
        )

    @property
    def is_valid(self) -> bool:
        variables = tuple(filter(_input_variable_enable_get, self.variables))
        if variables:
            for variable in variables:
                if not variable.is_valid:
                    return False
            return True
        return False

    object__internal__: PointerProperty(
        type=Object,
        options={'HIDDEN'}
        )

    object: PointerProperty(
        name="Object",
        description="The target object",
        type=Object,
        poll=_input_object_poll,
        options=set(),
        update=_input_object_update_handler
        )

    pose_radii: PointerProperty(
        name="Radii",
        type=InputPoseRadii,
        options=set()
        )

    rotation_axis: EnumProperty(
        name="Axis",
        description="The axis of rotation",
        items=[
            ('X', "X", "X axis rotation"),
            ('Y', "Y", "Y axis rotation"),
            ('Z', "Z", "Z axis rotation"),
            ],
        get=_input_rotation_axis_get,
        set=_input_rotation_axis_set,
        options=set(),
        )

    rotation_mode: EnumProperty(
        name="Mode",
        description="Rotation mode",
        items=[
            ('EULER'     , "Euler"     , "Euler angles"       ),
            ('QUATERNION', "Quaternion", "Quaternion rotation"),
            ('SWING'     , "Swing"     , "Swing rotation"     ),
            ('TWIST'     , "Twist"     , "Twist rotation"     ),
            ],
        get=_input_rotation_mode_get,
        set=_input_rotation_mode_set,
        options=set(),
        )

    rotation_order: EnumProperty(
        name="Order",
        description="Rotation order",
        items=[
            ('AUTO', "Auto", "Euler using the rotation order of the target."),
            ('XYZ' , "XYZ" , "Euler using the XYZ rotation order."          ),
            ('XZY' , "XZY" , "Euler using the XZY rotation order."          ),
            ('YXZ' , "YXZ" , "Euler using the YXZ rotation order."          ),
            ('YZX' , "YZX" , "Euler using the YZX rotation order."          ),
            ('ZXY' , "ZXY" , "Euler using the ZXY rotation order."          ),
            ('ZYX' , "ZYX" , "Euler using the ZYX rotation order."          ),
            ],
        get=_input_rotation_order_get,
        set=_input_rotation_order_set,
        options=set(),
        )

    transform_space: EnumProperty(
        name="Space",
        description="The space for transform channels",
        items=TRANSFORM_SPACE_ITEMS,
        get=_input_transform_space_get,
        set=_input_transform_space_set,
        options=set(),
        )

    type: EnumProperty(
        name="Type",
        items=[
            ('LOCATION', "Location", "Location transform channels", 'CON_LOCLIMIT' , 0),
            ('ROTATION', "Rotation", "Rotation transform channels", 'CON_ROTLIMIT' , 1),
            ('SCALE', "Scale", "Scale transform channels", 'CON_SIZELIMIT', 2),
            None,
            ('ROTATION_DIFF', "Rotational Difference", "Angle between two bones or objects.", 'DRIVER_ROTATIONAL_DIFFERENCE', 3),
            ('LOC_DIFF', "Distance", "Distance between two bones or objects.", 'DRIVER_DISTANCE', 4),
            None,
            ('SHAPE_KEY', "Shape Keys" , "Shape key values", 'SHAPEKEY_DATA', 5),
            ('USER_DEF', "User-defined", "Fully configurable input values", 'RNA', 6),
            ],
        get=_input_type_get,
        options=set()
        )

    variables: PointerProperty(
        type=InputVariables,
        options=set()
        )

#endregion Input

#region Inputs
#--------------------------------------------------------------------------------------------------

class Inputs(Observable, PropertyGroup):

    active_index: IntProperty(
        name="Input",
        description="RBF driver input",
        min=0,
        default=0,
        options=set()
        )

    @property
    def active(self) -> Optional[Input]:
        index = self.active_index
        return self[index] if index < len(self) else None

    internal__: CollectionProperty(
        type=Input,
        options={'HIDDEN'}
        )

    def __iter__(self) -> Iterator[Input]:
        return iter(self.internal__)

    def __len__(self) -> int:
        return len(self.internal__)

    def __getitem__(self, key: Union[str, int, slice]) -> Union[Input, List[Input]]:
        return self.internal__[key]

    def move(self, from_index: int, to_index: int) -> None:

        if not isinstance(from_index, int):
            raise TypeError((f'{self.__class__.__name__}.move(from_index, to_index): '
                             f'Expected from_index to be int, not {from_index.__class__.__name__}'))

        if not isinstance(to_index, int):
            raise TypeError((f'{self.__class__.__name__}.move(from_index, to_index): '
                             f'Expected to_index to be int, not {to_index.__class__.__name__}'))

        l = len(self)
        a = l + from_index if from_index < 0 else from_index
        b = l + to_index if to_index < 0 else to_index

        if 0 > a >= l:
            raise IndexError((f'{self.__class__.__name__}.move(from_index, to_index): '
                              f'from_index {from_index} out of range 0-{l-1}'))

        if 0 > b >= l:
            raise IndexError((f'{self.__class__.__name__}.move(from_index, to_index): '
                              f'to_index {to_index} out of range 0-{l-1}'))

        idx = list(range(l))
        idx.insert(b, idx.pop(a))
        self.internal__.move(a, b)
        self.notify_observers('reordered', idx)

    def new(self, type: str) -> Input:
        if not isinstance(type, str):
            raise TypeError(f'Inputs.new(type): type must be str, not {type.__class__.__name__}')

        if type not in INPUT_TYPE_INDEX:
            raise ValueError((f'Input.new(type): '
                              f'type {type} not found in {", ".join(INPUT_TYPE_INDEX)}'))

        input_ = self.internal__.add()
        input_["type"] = INPUT_TYPE_INDEX.index(type)

        if type == 'LOCATION':
            input_["transform_space"] = TRANSFORM_SPACE_TABLE['LOCAL_SPACE']

            for axis in "XYZ":
                variable = input_.variables.internal__.add()
                variable["type"] = INPUT_VARIABLE_TYPE_TABLE['TRANSFORMS']
                variable["name"] = axis
                
                target = variable.targets.internal__.add()
                target["transform_space"] = TRANSFORM_SPACE_TABLE['LOCAL_SPACE']
                target["transform_type"] = INPUT_TARGET_TRANSFORM_TYPE_TABLE[f'LOC_{axis}']

        elif type == 'ROTATION':
            input_["transform_space"] = TRANSFORM_SPACE_TABLE['LOCAL_SPACE']

            for axis, value in zip("WXYZ", (1.0, 0.0, 0.0, 0.0)):
                variable = input_.variables.internal__.add()
                variable["type"] = INPUT_VARIABLE_TYPE_TABLE['TRANSFORMS']
                variable["name"] = axis
                variable["default_value"] = value

                target = variable.targets.internal__.add()
                target["transform_space"] = TRANSFORM_SPACE_TABLE['LOCAL_SPACE']
                target["transform_type"] = INPUT_TARGET_TRANSFORM_TYPE_TABLE[f'ROT_{axis}']
                target["rotation_mode"] = INPUT_TARGET_ROTATION_MODE_TABLE['QUATERNION']

        elif type == 'SCALE':
            input_["transform_space"] = TRANSFORM_SPACE_TABLE['LOCAL_SPACE']

            for axis in "XYZ":
                variable = input_.variables.internal__.add()
                variable["type"] = INPUT_VARIABLE_TYPE_TABLE['TRANSFORMS']
                variable["name"] = axis
                variable["default_value"] = 1.0
                
                target = variable.targets.internal__.add()
                target["transform_space"] = TRANSFORM_SPACE_TABLE['LOCAL_SPACE']
                target["transform_type"] = INPUT_TARGET_TRANSFORM_TYPE_TABLE[f'SCALE_{axis}']
        
        elif type.endswith('DIFF'):
            variable = input_.variables.internal__.add()
            variable["type"] = INPUT_VARIABLE_TYPE_TABLE[type]
            variable["name"] = "var"
            
            variable.targets.internal__.add()
            variable.targets.internal__.add()

        elif type == 'SHAPE_KEY':
            variable = input_.variables.internal__.add()
            variable["type"] = INPUT_VARIABLE_TYPE_TABLE["SINGLE_PROP"]
            variable["name"] = ""

            target = variable.targets.internal__.add()
            target["id_type"] = INPUT_TARGET_ID_TYPE_TABLE['KEY']

        else: # type == USER_DEF:
            variable = input_.variables.internal__.add()
            variable["type"] = INPUT_VARIABLE_TYPE_TABLE["SINGLE_PROP"]
            variable["name"] = "var"
            variable.targets.internal__.add()
            variable.data["is_normalized"] = True

        self.notify_observers("new", input_)
        return input_


#endregion Inputs
