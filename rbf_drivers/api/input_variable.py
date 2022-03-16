
from typing import Any, Dict, Iterator, TYPE_CHECKING
from logging import getLogger
from bpy.types import Context, PropertyGroup
from bpy.props import (BoolProperty,
                       EnumProperty,
                       FloatProperty,
                       PointerProperty,
                       StringProperty)
from rbf_drivers.lib.symmetry import symmetrical_target
from .mixins import Symmetrical
from .input_target import RBFDriverInputTarget
from .input_targets import RBFDriverInputTargets
from .input_variable_data import RBFDriverInputVariableData
from ..lib.transform_utils import (transform_matrix,
                                   transform_matrix_element,
                                   transform_target,
                                   transform_target_distance,
                                   transform_target_rotational_difference)
if TYPE_CHECKING:
    from .input import RBFDriverInput
    from .pose import RBFDriverPose
    from .pose_weight import RBFDriverPoseWeight

log = getLogger("rbf_drivers")


INPUT_VARIABLE_TYPE_ITEMS = [
    ('SINGLE_PROP'  , "Single Property"      , "Use the value from some RNA property (Default).", 'NONE', 0),
    ('TRANSFORMS'   , "Transform Channel"    , "Final transformation value of object or bone."  , 'NONE', 1),
    ('ROTATION_DIFF', "Rotational Difference", "Use the angle between two bones."               , 'NONE', 2),
    ('LOC_DIFF'     , "Distance"             , "Distance between two bones or objects."         , 'NONE', 3),
    ]


def input_variable_type_get(variable: 'RBFDriverInputVariable') -> int:
    return variable.get("type", 0)


def input_variable_type_set(variable: 'RBFDriverInputVariable', value: int) -> None:
    input_ = variable.input

    if input_.type != 'NONE':
        raise RuntimeError((f'{variable.__class__.__name__}.type '
                            f'is not user-editable for {input_.type} inputs.'))

    variable["type"] = value
    if variable.type.endswith('DIFF'):
        if len(variable.targets) < 2:
            variable.targets["length__internal__"] = 2
            variable.targets.collection__internal__.add()
    else:
        variable.targets["length__internal__"] = 1

    variable.property_mirror("type")

def input_variable_default_value_update_handler(variable: 'RBFDriverInputVariable', context: Context) -> None:
    input_variable_property_mirror(variable, "default_value", variable.default_value)


def input_variable_is_enabled(variable: 'RBFDriverInputVariable') -> bool:
    return variable.get("enabled", False)


def input_variable_is_enabled_set(variable: 'RBFDriverInputVariable', value: bool) -> None:
    input = variable.input
    
    if input.type == 'ROTATION' and input.rotation_mode in {'QUATERNION', 'SWING', 'TWIST'}:
        message = (f'{variable.__class__.__name__}.enabled '
                   f'is not user-editable for {input.type} inputs.')
        log.error(message)
        raise AttributeError(message)

    variable["enabled"] = value

    pose: 'RBFDriverPose'
    for pose in input.rbf_driver.poses:
        weight: 'RBFDriverPoseWeight' = pose.weight
        weight.update()

    if variable.has_symmetry_target:
        input_variable_property_mirror(variable, "is_enabled", value)


def input_variable_is_inverted_update_handler(variable: 'RBFDriverInputVariable', _: Context) -> None:

    # TODO

    if variable.has_symmetry_target:
        input_variable_property_mirror(variable, "is_inverted", variable.is_inverted)


def input_variable_name_get(variable: 'RBFDriverInputVariable') -> str:
    return variable.get("name", "")


def input_variable_name_set(variable: 'RBFDriverInputVariable', value: str) -> None:
    input = variable.input

    if input.type not in {'NONE', 'SHAPE_KEY'}:
        message = f'{variable} name is not user-editable for input type {input.type}'
        log.error(message)
        raise AttributeError(message)

    if input.type == 'SHAPE_KEY':
        target: RBFDriverInputTarget = variable.targets[0]
        target["data_path"] = f'key_blocks["{value}"].value'

        pose: RBFDriverPose
        for pose in input.rbf_driver.poses:
            weight: RBFDriverPoseWeight = pose.weight
            weight.update()

    if variable.has_symmetry_target:
        input_variable_property_mirror(variable, "name", symmetrical_target(value) or value)


def input_variable_value__transforms(variable: 'RBFDriverInputVariable') -> float:
    target = variable.targets[0]
    matrix = transform_matrix(transform_target(target.object, target.bone_target), target.transform_space)
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


def input_variable_property_mirror(variable: 'RBFDriverInputVariable', name: str, value: Any) -> None:

    if not variable.has_symmetry_target:
        return
    
    input = variable.input
    if not input.has_symmetry_target:
        log.warning(f'Symmetry target defined for component {variable} but not for {input}')
        return

    driver = input.rbf_driver
    if not driver.has_symmetry_target:
        log.warning(f'Symmetry target defined for component {input} but not for {driver}')
        return

    if driver.symmetry_lock__internal__:
        return

    m_driver = driver.id_data.rbf_drivers.search(driver.symmetry_identifier)
    if m_driver is None:
        log.warning(f'Search failed for symmetry target of {driver}.')
        return

    m_input = driver.inputs.search(input.symmetry_identifier)
    if m_input is None:
        log.warning(f'Search failed for symmetry target of {input}.')
        return

    m_variable = m_input.variables.search(variable.symmetry_identifier)
    if m_variable is None:
        log.warning((f'Search failed for symmetry target of {variable}.'))
        return

    log.info(f'Mirroring {variable} property {name}')
    m_driver.symmetry_lock__internal__ = True
    try:
        setattr(m_variable, name, value)
    finally:
        m_driver.symmetry_lock__internal__ = False


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
        options=set(),
        update=input_variable_default_value_update_handler
        )

    is_inverted: BoolProperty(
        name="Invert",
        description="Invert the input variable's value when mirroring",
        default=False,
        options=set(),
        update=input_variable_is_inverted_update_handler
        )

    is_enabled: BoolProperty(
        name="Enabled",
        description="Include of exclude the variable from the RBF driver calculations",
        get=input_variable_is_enabled,
        set=input_variable_is_enabled_set,
        options=set(),
        )

    @property
    def input(self) -> 'RBFDriverInput':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".variables.")[0])

    name: StringProperty(
        name="Name",
        description="Variable name",
        get=input_variable_name_get,
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
        get=input_variable_type_get,
        set=input_variable_type_set,
        options=set(),
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

    def __init__(self, **props: Dict[str, Any]) -> None:
        self.targets.__init__(props.pop("targets", [{}]))

        for name, value in props.items():
            self[name] = value
        
        input = self.input
        normalize = input.type != 'ROTATION' or input.rotation_mode != 'QUATERNION'
        self.data.__init__([self.default], normalize)
