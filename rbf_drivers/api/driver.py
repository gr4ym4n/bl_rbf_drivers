
from typing import TYPE_CHECKING, Optional
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
        name="Interpolation Settings",
        description="Default pose interpolation settings",
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
        description="Prevents symmetry property changes from infinite regression (internal-use)",
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

    def __init__(self, type: str, name: Optional[str]="", mirror: Optional['RBFDriver']=None) -> None:
        assert isinstance(type, str) and type in DRIVER_TYPE_TABLE
        assert isinstance(name, str)
        assert mirror is None or (isinstance(mirror, RBFDriver)
                                  and mirror.id_data == self.id_data
                                  and mirror != self)

        self["type"] = DRIVER_TYPE_TABLE[type]
        if name:
            self.name = name

        if mirror:
            self["symmetry_identifier"] = mirror.identifier
            mirror["symmetry_identifier"] = self.identifier

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(type="{self.type}", name="{self.name}")'

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".collection__internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'
