
from typing import Iterable, Iterator, List, Optional, Tuple, Union
from logging import getLogger
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, IntProperty
from .driver import RBFDriver, DRIVER_TYPE_INDEX
from ..app.events import dataclass, dispatch_event, Event
from ..lib.symmetry import symmetrical_target

log = getLogger("rbf_drivers")


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


class RBFDrivers(PropertyGroup):

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

    def __len__(self) -> int:
        return len(self.collection__internal__)

    def __iter__(self) -> Iterator[RBFDriver]:
        return iter(self.collection__internal__)

    def __getitem__(self, key: Union[str, int, slice]) -> Union[RBFDriver, List[RBFDriver]]:
        return self.collection__internal__[key]

    def find(self, name: str) -> int:
        return self.collection__internal__.find(name)

    def get(self, name: str, default: Optional[object]=None) -> Optional[RBFDriver]:
        return self.collection__internal__.get(name, default)

    def keys(self) -> Iterable[str]:
        return self.collection__internal__.keys()

    def index(self, driver: RBFDriver) -> int:
        if not isinstance(driver, RBFDriver):
            raise TypeError((f'{self.__class__.__name__}.remove(driver): '
                             f'Expected driver to be RBFDriver, not {driver.__class__.__name__}'))

        return next(index for index, item in enumerate(self) if item == driver)

    def items(self) -> Iterable[Tuple[str, RBFDriver]]:
        return self.collection__internal__.items()

    def new(self,
            name: Optional[str]="",
            type: Optional[str]='NONE',
            mirror: Optional[RBFDriver]=None) -> RBFDriver:

        log.info(f'Creating new RBF driver at {self.id_data}')

        if mirror:
            if not isinstance(mirror, RBFDriver):
                raise TypeError((f'{self.__class__.__name__}.new(name="", type="NONE", mirror=None): '
                                 f'Expected mirror to be NoneType or RBFDriver, not {type.__class__.__name__}'))

            if mirror.id_data != self.id_data:
                raise ValueError((f'{self.__class__.__name__}.new(name="", type="NONE", mirror=None): '
                                  f'mirror must be a member of the same collection.'))

            type = mirror.type
            if not name:
                name = symmetrical_target(mirror.name) or mirror.name

        if not isinstance(type, str):
            raise TypeError((f'{self.__class__.__name__}.new(name="", type="NONE", mirror=None): '
                              f'Expected type to str, not {type.__class__.__name__}'))

        if type and type not in DRIVER_TYPE_INDEX:
            raise TypeError((f'{self.__class__.__name__}.new(name="", type="NONE", mirror=None): '
                             f'type "{type}" not found in {DRIVER_TYPE_INDEX.keys()}'))

        driver = self.collection__internal__.add()
        driver["type"] = DRIVER_TYPE_INDEX[type]
        driver.name = name or "RBFDriver"

        if mirror:
            driver["symmetry_identifier"] = mirror.identifier
            mirror["symmetry_identifier"] = driver.identifier

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

    def values(self) -> Iterable[RBFDriver]:
        return self.collection__internal__.values()