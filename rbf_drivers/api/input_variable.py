
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union
from bpy.types import Context, PropertyGroup
from bpy.props import (BoolProperty,
                       EnumProperty,
                       FloatProperty,
                       PointerProperty,
                       StringProperty)
from .mixins import Symmetrical
from .input_targets import RBFDriverInputTargets
from .input_variable_data import RBFDriverInputVariableData
from ..app.events import dataclass, dispatch_event, Event
from ..app.utils import owner_resolve
from ..lib.transform_utils import (transform_matrix,
                                   transform_matrix_element,
                                   transform_target,
                                   transform_target_distance,
                                   transform_target_rotational_difference)
if TYPE_CHECKING:
    from .input_target import RBFDriverInputTarget
    from .input import RBFDriverInput


INPUT_VARIABLE_TYPE_ITEMS: List[Tuple[str, str, str, str, int]] = [
    ('SINGLE_PROP'  , "Single Property"      , "Use the value from some RNA property (Default).", 'RNA'                         , 0),
    ('TRANSFORMS'   , "Transform Channel"    , "Final transformation value of object or bone."  , 'DRIVER_TRANSFORM'            , 1),
    ('ROTATION_DIFF', "Rotational Difference", "Use the angle between two bones."               , 'DRIVER_ROTATIONAL_DIFFERENCE', 2),
    ('LOC_DIFF'     , "Distance"             , "Distance between two bones or objects."         , 'DRIVER_DISTANCE'             , 3),
    ]

INPUT_VARIABLE_TYPE_INDEX: List[str] = [
    item[0] for item in INPUT_VARIABLE_TYPE_ITEMS
    ]

INPUT_VARIABLE_TYPE_TABLE: Dict[str, int] = {
    item[0]: item[4] for item in INPUT_VARIABLE_TYPE_ITEMS
    }


@dataclass(frozen=True)
class InputVariableIsEnabledUpdateEvent(Event):
    variable: 'RBFDriverInputVariable'
    value: bool


@dataclass(frozen=True)
class InputVariableNameUpdateEvent(Event):
    variable: 'RBFDriverInputVariable'
    value: str


@dataclass(frozen=True)
class InputVariableTypeUpdateEvent(Event):
    variable: 'RBFDriverInputVariable'
    value: str


def input_variable_type_update_handler(variable: 'RBFDriverInputVariable', _: 'Context') -> None:
    dispatch_event(InputVariableTypeUpdateEvent(variable, variable.type))


def input_variable_is_enabled(variable: 'RBFDriverInputVariable') -> bool:
    return variable.get("is_enabled", False)


def input_variable_is_enabled_set(variable: 'RBFDriverInputVariable', value: bool) -> None:
    input: 'RBFDriverInput' = owner_resolve(variable, ".variables")
    
    if input.type == 'ROTATION' and input.rotation_mode in {'QUATERNION', 'SWING', 'TWIST'}:
        raise RuntimeError((f'{variable}.is_enabled is not writable for'
                            f'{input} with type {input.type} and rotation_mode {input.rotation_mode}'))

    variable["is_enabled"] = value
    dispatch_event(InputVariableIsEnabledUpdateEvent(variable, value))


def input_variable_name(variable: 'RBFDriverInputVariable') -> str:
    return variable.get("name", "")


def input_variable_name_set(variable: 'RBFDriverInputVariable', value: str) -> None:
    input: 'RBFDriverInput' = owner_resolve(variable, ".variables")

    if input.type not in {'USER_DEF', 'SHAPE_KEY'}:
        raise RuntimeError((f'{variable}.name is not writable '
                            f'for {input} with type {input.type}'))

    variable["name"] = value
    if input.type == 'SHAPE_KEY':
        variable.targets[0]["data_path"] = f'key_blocks["{value}"].value'

    dispatch_event(InputVariableNameUpdateEvent(variable, value))


def input_variable_value__transforms(variable: 'RBFDriverInputVariable') -> float:
    target: 'RBFDriverInputTarget' = variable.targets[0]
    matrix = transform_matrix(transform_target(target.object, target.bone_target), target.transform_space)

    if target.transform_type == 'ROT_W' and len(target.rotation_mode) < 5:
        return 0.0

    return transform_matrix_element(matrix, target.transform_type, target.rotation_mode, driver=True)


def input_variable_value__loc_diff(variable: 'RBFDriverInputVariable') -> float:
    a = variable.targets[0]
    b = variable.targets[1]
    return transform_target_distance(transform_target(a.object, a.bone_target),
                                     transform_target(b.object, b.bone_target),
                                     a.transform_space,
                                     b.transform_space)


def input_variable_value__rotation_diff(variable: 'RBFDriverInputVariable') -> float:
    a = variable.targets[0]
    b = variable.targets[1]
    return transform_target_rotational_difference(transform_target(a.object, a.bone_target),
                                                  transform_target(b.object, b.bone_target))


def input_variable_value__single_prop(variable: 'RBFDriverInputVariable') -> float:
    target = variable.targets[0]
    id = target.id
    if id:
        try:
            value = id.path_resolve(target.data_path)
        except ValueError:
            pass
        else:
            if isinstance(value, (float, int, bool)):
                return float(value)
    return 0.0


def input_variable_is_valid__singleprop(variable: 'RBFDriverInputVariable') -> bool:
    target = variable.targets[0]
    object = target.object

    if object is None:
        return False

    idtype = target.id_type

    if idtype != 'OBJECT':
        if object.type != idtype:
            return False
        id = object.data
    else:
        id = object

    try:
        value = id.path_resolve(target.data_path)
    except ValueError:
        return False
    else:
        return isinstance(value, (bool, int, float))


def input_variable_is_valid__transforms(variable: 'RBFDriverInputVariable') -> bool:
    target = variable.targets[0]
    object = target.object

    if object is None:
        return False

    if object.type == 'ARMATURE':
        bone = target.bone_target
        if bone:
            return bone in object.data.bones

    return True


def input_variable_is_valid__diff(variable: 'RBFDriverInputVariable') -> bool:
    for target in variable.targets:
        object = target.object

        if object is None:
            return False

        if object.type == 'ARMATURE':
            bone = target.bone_target
            if bone and bone in object.data.bones:
                return False

    return True


def input_variable_is_valid(variable: 'RBFDriverInputVariable') -> bool:
    type = variable.type
    if type == 'SINGLE_PROP' : return input_variable_is_valid__singleprop(variable)
    if type == 'TRANSFORMS'  : return input_variable_is_valid__transforms(variable)
    if type.endswith('DIFF') : return input_variable_is_valid__diff(variable)
    return False


class RBFDriverInputVariable(Symmetrical, PropertyGroup):

    data: PointerProperty(
        name="Data",
        type=RBFDriverInputVariableData,
        options=set()
        )

    default_value: FloatProperty(
        name="Default",
        description="The default value for the variable",
        default=0.0,
        options=set()
        )

    is_enabled: BoolProperty(
        name="Enabled",
        description="Include or exclude the variable from the RBF driver calculations",
        get=input_variable_is_enabled,
        set=input_variable_is_enabled_set,
        options=set(),
        )

    is_valid: BoolProperty(
        name="Valid",
        description="Whether or not the input variable is valid (read-only)",
        get=input_variable_is_valid,
        options=set()
        )

    name: StringProperty(
        name="Name",
        description="Variable name",
        get=input_variable_name,
        set=input_variable_name_set,
        options=set(),
        )

    targets: PointerProperty(
        name="Targets",
        type=RBFDriverInputTargets,
        options=set()
        )

    type: EnumProperty(
        name="Type",
        description="The variable type",
        items=INPUT_VARIABLE_TYPE_ITEMS,
        default=INPUT_VARIABLE_TYPE_ITEMS[0][0],
        update=input_variable_type_update_handler,
        options=set(),
        )

    ui_expand: BoolProperty(
        name="Expand",
        description="Show/hide variable settings",
        default=False,
        options=set()
        )

    @property
    def value(self) -> float:
        """
        The current value of the variable (read-only)
        """
        type = self.type
        if type == 'TRANSFORMS'    : return input_variable_value__transforms(self)
        if type == 'LOC_DIFF'      : return input_variable_value__loc_diff(self)
        if type == 'ROTATION_DIFF' : return input_variable_value__rotation_diff(self)
        return input_variable_value__single_prop(self)

    def __init__(self,
                 type: Optional[Union[int, str]]=None,
                 default_value: Optional[float]=None,
                 is_enabled: Optional[bool]=None) -> None:
        
        assert (type is None
                or (isinstance(type, int) and 0 <= type < len(INPUT_VARIABLE_TYPE_INDEX))
                or (isinstance(type, str) and type in INPUT_VARIABLE_TYPE_TABLE))

        assert isinstance(default_value, (int, bool, float))
        assert isinstance(is_enabled, (int, bool))

        if isinstance(type, str):
            type = INPUT_VARIABLE_TYPE_TABLE[type]

        if type is not None:
            self["type"] = type

        if default_value is not None:
            self["default_value"] = bool(default_value)

        if is_enabled is not None:
            self["is_enabled"] = bool(is_enabled)

    def __repr__(self) -> str:
        return (f'{self.__class__.__name__}(type="{self.type}", '
                                          f'name={self.name}'
                                          f'default_value={self.default_value})'
                                          f'is_enabled={self.is_enabled}')

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".collection__internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'
