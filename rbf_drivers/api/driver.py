
from dataclasses import dataclass, field
from typing import Callable, List
from bpy.types import Context, PropertyGroup
from bpy.props import BoolProperty, EnumProperty, PointerProperty
from .mixins import Symmetrical
from .inputs import RBFDriverInputs
from .driver_falloff import RBFDriverFalloff
from .driver_distance_matrix import RBFDriverDistanceMatrix
from .driver_variable_matrix import RBFDriverVariableMatrix


DRIVER_SMOOTHING_ITEMS = [
    ('NONE'     , "None"     , "Linear RBF kernel"                    , 'IPO_LINEAR' , 0),
    ('GAUSSIAN' , "Gaussian" , "Gaussian RBF kernel"                  , 'IPO_QUAD'   , 1),
    ('QUADRATIC', "Quadratic", "Multi-quadratic biharmonic RBF kernel", 'SMOOTHCURVE', 2),
    ]


def smoothing_update_proxy_handler(driver: 'RBFDriver', _: Context) -> None:
    value = driver.smoothing
    for handler in driver.handlers.smoothing_update:
        handler(driver, value)


def pose_weight_is_clamped_update_proxy_handler(driver: 'RBFDriver', _: Context) -> None:
    value = driver.pose_weight_is_clamped
    for handler in driver.handlers.pose_weight_is_clamped_update:
        handler(driver, value)


def pose_weight_is_normalized_update_proxy_handler(driver: 'RBFDriver', _: Context) -> None:
    value = driver.pose_weight_is_normalized
    for handler in driver.handlers.pose_weight_is_normalized_update:
        handler(driver, value)


def use_linear_equation_solver_update_proxy_handler(driver: 'RBFDriver', _: Context) -> None:
    value = driver.use_linear_equation_solver
    for handler in driver.handlers.use_linear_equation_solver_update:
        handler(driver, value)


@dataclass(frozen=True)
class RBFDriverHandlers:

    distance_matrix_update: List[Callable[['RBFDriver', RBFDriverDistanceMatrix], None]] = field(default_factory=list)
    falloff_update: List[Callable[['RBFDriver', RBFDriverFalloff], None]] = field(default_factory=list)
    pose_weight_is_clamped_update: List[Callable[['RBFDriver', bool], None]] = field(default_factory=list)
    pose_weight_is_normalized_update: List[Callable[['RBFDriver', bool], None]] = field(default_factory=list)
    smoothing_update: List[Callable[['RBFDriver', str], None]] = field(default_factory=list)
    use_linear_equation_solver_update: List[Callable[['RBFDriver', bool], None]] = field(default_factory=list)
    variable_matrix_update: List[Callable[['RBFDriver', RBFDriverVariableMatrix], None]] = field(default_factory=list)


class RBFDriver(Symmetrical, PropertyGroup):

    handlers = RBFDriverHandlers()

    distance_matrix: PointerProperty(
        name="Distance Matrix",
        type=RBFDriverDistanceMatrix,
        options=set()
        )

    falloff: PointerProperty(
        name="Falloff",
        type=RBFDriverFalloff,
        options=set()
        )

    inputs: PointerProperty(
        name="Inputs",
        type=RBFDriverInputs,
        options=set()
        )

    pose_weight_is_clamped: BoolProperty(
        name="Clamp Pose Weights",
        description="",
        default=True,
        options=set(),
        update=pose_weight_is_clamped_update_proxy_handler
        )

    pose_weight_is_normalized: BoolProperty(
        name="Normalize Pose Weights",
        description="",
        default=True,
        options=set(),
        update=pose_weight_is_normalized_update_proxy_handler
        )

    smoothing: EnumProperty(
        items=DRIVER_SMOOTHING_ITEMS,
        default='NONE',
        options=set(),
        update=smoothing_update_proxy_handler
        )

    symmetry_lock__internal__: BoolProperty(
        default=False,
        options={'HIDDEN'}
        )

    use_linear_equation_solver: BoolProperty(
        name="Use Solver",
        default=True,
        options=set(),
        update=use_linear_equation_solver_update_proxy_handler
        )

    variable_matrix: PointerProperty(
        name="Variable Matrix",
        type=RBFDriverVariableMatrix,
        options=set()
        )
