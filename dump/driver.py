
from typing import TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, EnumProperty, FloatProperty, PointerProperty
from .mixins import Symmetrical
from .inputs import RBFDriverInputs
from .poses import RBFDriverPoses
from .outputs import RBFDriverOutputs
from .driver_interpolation import RBFDriverFalloff
from ...dump.driver_distance_matrix import RBFDriverDistanceMatrix
from ...dump.driver_variable_matrix import RBFDriverVariableMatrix
from ..app.events import dataclass, dispatch_event, Event
if TYPE_CHECKING:
    from bpy.types import Context


DRIVER_TYPE_ITEMS = [
    ('NONE'      , "Generic"   , "", 'DRIVER'       , 0),
    ('SHAPE_KEYS', "Shape Keys", "", 'SHAPEKEY_DATA', 1),
    ]

DRIVER_TYPE_INDEX = {
    item[0]: item[4] for item in DRIVER_TYPE_ITEMS
    }


@dataclass(frozen=True)
class RadiusUpdateEvent(Event):
    driver: 'RBFDriver'
    value: float


@dataclass(frozen=True)
class RegularizationUpdateEvent(Event):
    driver: 'RBFDriver'
    value: float


@dataclass(frozen=True)
class SmoothingUpdateEvent(Event):
    driver: 'RBFDriver'
    value: str


def radius_update_handler(driver: 'RBFDriver', _: 'Context') -> None:
    dispatch_event(RadiusUpdateEvent(driver, driver.radius))


def regularization_update_handler(driver: 'RBFDriver', _: 'Context') -> None:
    dispatch_event(RegularizationUpdateEvent(driver, driver.regularization))


def smoothing_update_handler(driver: 'RBFDriver', _: 'Context') -> None:
    dispatch_event(SmoothingUpdateEvent(driver, driver.smoothing))


class RBFDriver(Symmetrical, PropertyGroup):

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

    outputs: PointerProperty(
        name="Outputs",
        type=RBFDriverOutputs,
        options=set()
        )

    poses: PointerProperty(
        name="Poses",
        type=RBFDriverPoses,
        options=set()
        )

    radius: FloatProperty(
        name="Radius",
        description="",
        min=0.0,
        max=10.0,
        soft_min=0.0,
        soft_max=1.0,
        default=1.0,
        options=set(),
        update=radius_update_handler
        )

    regularization: FloatProperty(
        name="Regularization",
        min=0.0001,
        soft_min=0.1,
        soft_max=1.0,
        default=1.0,
        options=set(),
        update=regularization_update_handler
        )

    smoothing: EnumProperty(
        name="Smoothing",
        items=[
            ('RADIAL', "Radial", "Pose-radius based smoothing"),
            ('LINEAR', "Linear", "Linear equations solver regularization"),
            ],
        default='RADIAL',
        options=set(),
        update=smoothing_update_handler
        )

    symmetry_lock__internal__: BoolProperty(
        default=False,
        options={'HIDDEN'}
        )

    type: EnumProperty(
        name="Type",
        items=DRIVER_TYPE_ITEMS,
        get=lambda self: self.get("type", 0),
        options=set()
        )

    variable_matrix: PointerProperty(
        name="Variable Matrix",
        type=RBFDriverVariableMatrix,
        options=set()
        )
