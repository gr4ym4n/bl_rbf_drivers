
from typing import TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, EnumProperty, PointerProperty, StringProperty
from .mixins import Symmetrical
from .inputs import RBFDriverInputs
from .poses import RBFDriverPoses
from .outputs import RBFDriverOutputs
from .driver_interpolation import RBFDriverInterpolation
from ..app.events import dataclass, dispatch_event, Event
if TYPE_CHECKING:
    from bpy.types import Context


DRIVER_TYPE_ITEMS = [
    ('NONE'      , "Generic"   , "", 'DRIVER'       , 0),
    ('SHAPE_KEY' , "Shape Keys", "", 'SHAPEKEY_DATA', 1),
    ]

DRIVER_TYPE_INDEX = [
    item[0] for item in DRIVER_TYPE_ITEMS
    ]

DRIVER_TYPE_TABLE = {
    item[0]: item[4] for item in DRIVER_TYPE_ITEMS
    }

DRIVER_TYPE_ICONS = {
    item[0]: item[3] for item in DRIVER_TYPE_ITEMS
    }


@dataclass(frozen=True)
class DriverNameUpdateEvent(Event):
    driver: 'RBFDriver'
    value: str


def driver_name_update_handler(driver: 'RBFDriver', _: 'Context') -> None:
    dispatch_event(DriverNameUpdateEvent(driver, driver.name))


def driver_symmetry_lock(driver: 'RBFDriver') -> bool:
    return driver.get("symmetry_lock", False)


def driver_type(driver: 'RBFDriver') -> int:
    return driver.get("type", 0)


class RBFDriver(Symmetrical, PropertyGroup):
    '''Radial basis function driver'''

    @property
    def icon(self) -> str:
        """The RBF driver icon (read-only)"""
        return DRIVER_TYPE_ICONS[self.type]

    interpolation: PointerProperty(
        name="Falloff",
        description="RBF driver interpolation options",
        type=RBFDriverInterpolation,
        options=set()
        )

    inputs: PointerProperty(
        name="Inputs",
        description="Collection of RBF driver inputs",
        type=RBFDriverInputs,
        options=set()
        )

    outputs: PointerProperty(
        name="Outputs",
        description="Collection of RBF driver outputs",
        type=RBFDriverOutputs,
        options=set()
        )

    name: StringProperty(
        name="Name",
        description="Unique RBF driver name",
        options=set(),
        update=driver_name_update_handler,
        )

    poses: PointerProperty(
        name="Poses",
        description="Collection of RBF driver poses",
        type=RBFDriverPoses,
        options=set()
        )

    symmetry_lock: BoolProperty(
        name="Symmetry Lock",
        description="Prevent symmetry property changes from infinite regression (read-only)",
        get=driver_symmetry_lock,
        options={'HIDDEN'}
        )

    type: EnumProperty(
        name="Type",
        description="The RBF driver type (read-only)",
        items=DRIVER_TYPE_ITEMS,
        get=driver_type,
        options=set()
        )
