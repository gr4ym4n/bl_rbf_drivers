
from typing import Any, Iterator, List, Optional, Union, TYPE_CHECKING
from bpy.types import PropertyGroup, ShapeKey
from bpy.props import CollectionProperty
from .output_channel import RBFDriverOutputChannel
from ..app.events import dataclass, dispatch_event, Event
from ..app.utils import owner_resolve
if TYPE_CHECKING:
    from .output import RBFDriverOutput


@dataclass(frozen=True)
class OutputChannelNewEvent(Event):
    channel: RBFDriverOutputChannel


@dataclass(frozen=True)
class OutputChannelDisposableEvent(Event):
    channel: RBFDriverOutputChannel


@dataclass(frozen=True)
class OutputChannelRemovedEvent(Event):
    channels: 'RBFDriverOutputChannels'
    index: int


class RBFDriverOutputChannels(PropertyGroup):

    collection__internal__: CollectionProperty(
        type=RBFDriverOutputChannel,
        options={'HIDDEN'}
        )

    def __len__(self) -> int:
        return len(self.collection__internal__)

    def __iter__(self) -> Iterator[RBFDriverOutputChannel]:
        return iter(self.collection__internal__)

    def __getitem__(self, key: Union[str, int, slice]) -> Union[RBFDriverOutputChannel, List[RBFDriverOutputChannel]]:

        if isinstance(key, str):
            channel = next((var for var in self if var.name == key), None)
            if channel is None:
                raise KeyError(f'{self.__class__.__name__}[key]: "{key}" not found.')
            return channel

        if isinstance(key, int):
            if 0 > key >= len(self):
                raise IndexError((f'{self.__class__.__name__}[key]: '
                                  f'Index {key} out of range 0-{len(self)}.'))

            return self.collection__internal__[key]

        if isinstance(key, slice):
            return self.collection__internal__[key]

        raise TypeError((f'{self.__class__.__name__}[key]: '
                         f'Expected key to be str, int or slice, not {key.__class__.__name__}.'))

    def find(self, name: str) -> int:
        return next((index for index, channel in enumerate(self) if channel.name == name), -1)

    def get(self, name: str, default: Optional[object]=None) -> Any:
        return self.collection__internal__.get(name, default)

    def index(self, channel: RBFDriverOutputChannel) -> int:
        return next(index for index, item in enumerate(self) if channel == item)

    def new(self, shape_key: ShapeKey) -> RBFDriverOutputChannel:

        output: 'RBFDriverOutput' = owner_resolve(self, ".")

        if output.type != 'SHAPE_KEYS':
            raise RuntimeError((f'{self.__class__.__name__}.new(shape_key): '
                                f'channels are not mutable for outputs of type {output.type}'))

        if not isinstance(shape_key, ShapeKey):
            raise TypeError((f'{self.__class__.__name__}.new(shape_key): '
                             f'Expected shape_key to be ShapeKey, not {shape_key.__class__.__name__}'))

        if shape_key.id_data != self.id_data.data:
            raise RuntimeError()

        channel: RBFDriverOutputChannel = self.collection__internal__.add()
        channel["name"] = shape_key.name

        dispatch_event(OutputChannelNewEvent(channel))

        return channel

    def remove(self, channel: 'RBFDriverOutputChannel') -> None:

        output: 'RBFDriverOutput' = owner_resolve(self, ".")

        if output.type != 'SHAPE_KEYS':
            raise RuntimeError((f'{self.__class__.__name__}.remove(channel): '
                                f'channels are not mutable for outputs of type {output.type}'))

        if not isinstance(channel, RBFDriverOutputChannel):
            raise TypeError((f'{self.__class__.__name__}.remove(channel): '
                             f'Expected channel to be RBFDriverOutputChannel, not {channel.__class__.__name__}'))

        index = next((index for index, item in enumerate(self) if item == channel), -1)

        if index == -1:
            raise ValueError((f'{self.__class__.__name__}.remove(channel): '
                             f'channel is not a member of this collection'))

        dispatch_event(OutputChannelDisposableEvent(channel))
        self.collection__internal__.remove(index)
        dispatch_event(OutputChannelRemovedEvent(self, index))

    def search(self, identifier: str) -> Optional[RBFDriverOutputChannel]:
        return next((channel for channel in self if channel.identifier == identifier), None)
