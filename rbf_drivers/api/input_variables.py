
from typing import TYPE_CHECKING, Dict, Iterator, List, Optional, Tuple, Union
from bpy.types import Context, PropertyGroup
from bpy.props import (BoolProperty,
                       CollectionProperty,
                       EnumProperty,
                       FloatProperty,
                       IntProperty,
                       PointerProperty,
                       StringProperty)
from rbf_drivers.app.utils import name_unique
from .mixins import Collection, Searchable, Symmetrical
from .input_targets import InputTargetDataPathUpdateEvent, InputTargets, INPUT_TARGET_ID_TYPE_TABLE
from .input_data import InputData
from ..app.events import dataclass, dispatch_event, Event
from ..lib.transform_utils import (transform_matrix,
                                   transform_matrix_element,
                                   transform_target,
                                   transform_target_distance,
                                   transform_target_rotational_difference)
if TYPE_CHECKING:
    from .input_targets import InputTarget
    from .inputs import Input


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
class InputVariablePropertyUpdateEvent(Event):
    variable: 'InputVariable'


@dataclass(frozen=True)
class InputVariableIsEnabledUpdateEvent(InputVariablePropertyUpdateEvent):
    value: bool


@dataclass(frozen=True)
class InputVariableNameUpdateEvent(InputVariablePropertyUpdateEvent):
    value: str


@dataclass(frozen=True)
class InputVariableTypeUpdateEvent(InputVariablePropertyUpdateEvent):
    value: str


def input_variable_type_update_handler(variable: 'InputVariable', _: 'Context') -> None:
    type = variable.type
    if type.endswith('DIFF'):
        if len(variable.targets) < 2:
            variable.targets.internal__.add()
    else:
        if len(variable.targets) > 1:
            variable.targets.internal__.remove(1)
    dispatch_event(InputVariableTypeUpdateEvent(variable, variable.type))


def input_variable_is_enabled(variable: 'InputVariable') -> bool:
    return variable.get("is_enabled", False)


def input_variable_is_enabled_set(variable: 'InputVariable', value: bool) -> None:
    input = variable.input
    
    if input.type == 'ROTATION' and input.rotation_mode in {'QUATERNION', 'SWING', 'TWIST'}:
        raise RuntimeError((f'{variable}.is_enabled is not writable for'
                            f'{input} with type {input.type} and rotation_mode {input.rotation_mode}'))

    variable["is_enabled"] = value
    dispatch_event(InputVariableIsEnabledUpdateEvent(variable, value))


def input_variable_name(variable: 'InputVariable') -> str:
    return variable.get("name", "")


def input_variable_name_set(variable: 'InputVariable', value: str) -> None:
    input = variable.input

    if input.type not in {'USER_DEF', 'SHAPE_KEY'}:
        raise RuntimeError((f'{variable}.name is not writable '
                            f'for {input} with type {input.type}'))

    variable["name"] = value
    if input.type == 'SHAPE_KEY':
        target = variable.targets[0]
        target["data_path"] = f'key_blocks["{value}"].value'
        dispatch_event(InputTargetDataPathUpdateEvent(target, target.data_path))

    dispatch_event(InputVariableNameUpdateEvent(variable, value))


def input_variable_value__transforms(variable: 'InputVariable') -> float:
    target: 'InputTarget' = variable.targets[0]
    matrix = transform_matrix(transform_target(target.object, target.bone_target), target.transform_space)

    if target.transform_type == 'ROT_W' and len(target.rotation_mode) < 5:
        return 0.0

    return transform_matrix_element(matrix, target.transform_type, target.rotation_mode, driver=True)


def input_variable_value__loc_diff(variable: 'InputVariable') -> float:
    a = variable.targets[0]
    b = variable.targets[1]
    return transform_target_distance(transform_target(a.object, a.bone_target),
                                     transform_target(b.object, b.bone_target),
                                     a.transform_space,
                                     b.transform_space)


def input_variable_value__rotation_diff(variable: 'InputVariable') -> float:
    a = variable.targets[0]
    b = variable.targets[1]
    return transform_target_rotational_difference(transform_target(a.object, a.bone_target),
                                                  transform_target(b.object, b.bone_target))


def input_variable_value__single_prop(variable: 'InputVariable') -> float:
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


def input_variable_is_valid__singleprop(variable: 'InputVariable') -> bool:
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


def input_variable_is_valid__transforms(variable: 'InputVariable') -> bool:
    target = variable.targets[0]
    object = target.object

    if object is None:
        return False

    if object.type == 'ARMATURE':
        bone = target.bone_target
        if bone:
            return bone in object.data.bones

    return True


def input_variable_is_valid__diff(variable: 'InputVariable') -> bool:
    for target in variable.targets:
        object = target.object

        if object is None:
            return False

        if object.type == 'ARMATURE':
            bone = target.bone_target
            if bone and bone in object.data.bones:
                return False

    return True


def input_variable_is_valid(variable: 'InputVariable') -> bool:
    type = variable.type
    if type == 'SINGLE_PROP' : return input_variable_is_valid__singleprop(variable)
    if type == 'TRANSFORMS'  : return input_variable_is_valid__transforms(variable)
    if type.endswith('DIFF') : return input_variable_is_valid__diff(variable)
    return False


class InputVariable(Symmetrical, PropertyGroup):

    data: PointerProperty(
        name="Data",
        type=InputData,
        options=set()
        )

    default_value: FloatProperty(
        name="Default",
        description="The default value for the variable",
        default=0.0,
        options=set()
        )

    @property
    def index(self) -> int:
        """
        The index of the variable (read-only)
        """
        return self.input.variables.index(self)

    @property
    def input(self) -> 'Input':
        """
        Parent input (read-only)
        """
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".variables"))

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
        description="Unique variable name",
        get=input_variable_name,
        set=input_variable_name_set,
        options=set(),
        )

    targets: PointerProperty(
        name="Targets",
        type=InputTargets,
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

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'


@dataclass(frozen=True)
class InputVariablesUpdateEvent(Event):
    variables: 'InputVariables'


@dataclass(frozen=True)
class InputVariableNewEvent(InputVariablesUpdateEvent):
    variable: InputVariable


@dataclass(frozen=True)
class InputVariableDisposableEvent(InputVariablesUpdateEvent):
    variable: InputVariable


@dataclass(frozen=True)
class InputVariableRemovedEvent(InputVariablesUpdateEvent):
    index: int


class InputVariables(Searchable, Collection[InputVariable], PropertyGroup):

    internal__: CollectionProperty(
        type=InputVariable,
        options={'HIDDEN'}
        )

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

    @property
    def input(self) -> 'Input':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition("."))

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}'

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'

    def enabled(self) -> Iterator[InputVariable]:
        return filter(input_variable_is_enabled, self)

    def new(self, name: Optional[str]="var") -> InputVariable:
        input = self.input

        if input.type not in {'USER_DEF', 'SHAPE_KEY'}:
            raise RuntimeError((f'{self.__class__.__name__}.new(name="var"): '
                                f'Variables are not mutable for inputs of type {input.type}'))

        if len(self) >= 16:
            raise RuntimeError((f'{self.__class__.__name__}.new(name="var"): '
                                f'Maximum number of variables per input exceeded'))

        name = name_unique(name, tuple(self.keys()), separator="_", zfill=2)

        variable: InputVariable = self.internal__.add()
        variable["name"] = name
        variable.targets.internal__.add()

        if input.type == 'SHAPE_KEY':
            object = input.object
            compat = {'MESH', 'LATTICE', 'CURVE'}
            target: 'InputTarget' = variable.targets[0]

            target["id_type"] = INPUT_TARGET_ID_TYPE_TABLE['KEY']
            target["id"] = object.data.shape_keys if object and object.type in compat else None
            target["data_path"] = f'key_blocks["{name}"].value'

        dispatch_event(InputVariableNewEvent(variable))
        return variable

    def remove(self, variable: InputVariable) -> None:
        input = self.input

        if input.type not in {'USER_DEF', 'SHAPE_KEY'}:
            raise RuntimeError((f'{self.__class__.__name__}.remove(variable): '
                                f'Variables are not mutable for inputs of type {input.type}'))

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

        dispatch_event(InputVariableDisposableEvent(variable))
        self.internal__.remove(index)
        dispatch_event(InputVariableRemovedEvent(self, index))