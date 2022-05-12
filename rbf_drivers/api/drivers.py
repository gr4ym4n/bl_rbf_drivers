
from typing import Optional
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, IntProperty
from .mixins import Collection, Reorderable, Searchable
from .driver import RBFDriver, DRIVER_TYPE_TABLE
from ..app.events import dataclass, dispatch_event, Event
from ..lib.symmetry import symmetrical_target


@dataclass(frozen=True)
class DriverNewEvent(Event):
    driver: RBFDriver


@dataclass(frozen=True)
class DriverDisposableEvent(Event):
    driver: RBFDriver


@dataclass(frozen=True)
class DriverRemovedEvent(Event):
    drivers: 'RBFDrivers'
    index: int


class RBFDrivers(Reorderable,
                 Searchable[RBFDriver],
                 Collection[RBFDriver],
                 PropertyGroup):

    active_index: IntProperty(
        name="RBF Driver",
        min=0,
        default=0,
        options=set()
        )

    @property
    def active(self) -> Optional[RBFDriver]:
        index = self.active_index
        return self[index] if index < len(self) else None

    collection__internal__: CollectionProperty(
        type=RBFDriver,
        options={'HIDDEN'}
        )

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}{{{self.id_data.name}}}'

    def __str__(self) -> str:
        path: str = self.path_from_id()
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'

    def new(self,
            type: Optional[str]='NONE',
            name: Optional[str]="",
            mirror: Optional[RBFDriver]=None) -> RBFDriver:

        if mirror:
            if not isinstance(mirror, RBFDriver):
                raise TypeError((f'{self.__class__.__name__}.new(name="", type="NONE", mirror=None): '
                                 f'Expected mirror to be NoneType or RBFDriver, not {type.__class__.__name__}'))

            if mirror.id_data != self.id_data:
                raise ValueError((f'{self.__class__.__name__}.new(name="", type="NONE", mirror=None): '
                                  f'mirror must be a member of the same collection of RBF drivers.'))

            type = mirror.type
            if not name:
                name = symmetrical_target(mirror.name) or mirror.name

        if not isinstance(type, str):
            raise TypeError((f'{self.__class__.__name__}.new(name="", type="NONE", mirror=None): '
                              f'Expected type to str, not {type.__class__.__name__}'))

        if type not in DRIVER_TYPE_TABLE:
            raise TypeError((f'{self.__class__.__name__}.new(name="", type="NONE", mirror=None): '
                             f'type "{type}" not found in ({",".join(DRIVER_TYPE_TABLE.keys())})'))

        if type == 'SHAPE_KEY' and self.id_data.type not in {'MESH', 'LATTICE', 'CURVE'}:
            raise ValueError((f'{self.__class__.__name__}.new(name="", type="GENERIC", mirror=None): '
                              f'type "{type}" is only valid for mesh, lattice and curve objects.'))

        driver = self.collection__internal__.add()
        driver.__init__(type=type, name=name, mirror=mirror)

        dispatch_event(DriverNewEvent(driver))

        self.active_index = len(self) - 1
        return driver

    def remove(self, driver: RBFDriver) -> None:

        if not isinstance(driver, RBFDriver):
            raise TypeError((f'{self.__class__.__name__}.remove(driver): '
                             f'Expected driver to be RBFDriver, not {driver.__class__.__name__}'))

        index = next((index for index, item in enumerate(self) if item == driver), -1)

        if index == -1:
            raise ValueError((f'{self.__class__.__name__}.remove(driver): '
                              f'driver is not a member of this collection'))

        dispatch_event(DriverDisposableEvent(driver))

        self.collection__internal__.remove(index)
        self.active_index = min(self.active_index, len(self)-1)

        dispatch_event(DriverRemovedEvent(self, index))

    def search(self, identifier: str) -> Optional[RBFDriver]:
        return next((item for item in self if item.identifier == identifier), None)
