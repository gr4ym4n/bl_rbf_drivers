
from ctypes import Union
from typing import TYPE_CHECKING, Any, Generic, Iterable, Iterator, List, Optional, Sequence, Tuple, TypeVar
from uuid import uuid4
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, EnumProperty, StringProperty
if TYPE_CHECKING:
    from bpy.types import ID, Object


def identifier(pgroup: 'Identifiable') -> str:
    value = PropertyGroup.get(pgroup, "identifier")
    if not value:
        value = uuid4().hex
        PropertyGroup.__setitem__(pgroup, "identifier", value)
    return value


class Identifiable:

    identifier: StringProperty(
        name="Identifier",
        description="Unique data identifier",
        get=identifier,
        options={'HIDDEN'}
        )


class Symmetrical(Identifiable):

    symmetry_identifier: StringProperty(
        name="Symmetry Identifier",
        get=lambda self: self.get("symmetry_identifier", ""),
        options=set(),
        )

    @property
    def has_symmetry_target(self) -> bool:
        return bool(self.symmetry_identifier)


class Targetable:

    @property
    def bone_target(self) -> str:
        raise NotImplementedError(f'{self.__class__.__name__}.bone_target')

    @property
    def id(self) -> Optional['ID']:
        raise NotImplementedError(f'{self.__class__.__name__}.id')

    @property
    def id_type(self) -> str:
        raise NotImplementedError(f'{self.__class__.__name__}.id_type')

    @property
    def object(self) -> Optional['Object']:
        raise NotImplementedError(f'{self.__class__.__name__}.object')

class Layer(Symmetrical):

    ui_label: EnumProperty(
        items=[
            ('PATH', "Path", "", 'RNA' , 0),
            ('NAME', "Name", "", 'CON_FOLLOWTRACK', 1),
            ],
        default='PATH',
        options=set()
        )

    ui_open: BoolProperty(
        name="Open",
        description="Show/Hide input settings in the UI",
        default=True,
        options=set()
        )

    ui_show_pose: BoolProperty(
        name="Show",
        description="Show/Hide pose values in the UI",
        default=False,
        options=set()
        )

ItemType = TypeVar('ItemType', bound='PropertyGroup')

class ItemCollection(Generic[ItemType]):

    @property
    def collection__internal__(self) -> Sequence[ItemType]:
        raise NotImplementedError(f'{self.__class__.__name__}.collection__internal__')

    def __len__(self) -> int:
        return len(self.collection__internal__)

    def __iter__(self) -> Iterator[ItemType]:
        return iter(self.collection__internal__)

    def __getitem__(self, key: Union[int, str, slice]) -> Union[ItemType, List[ItemType]]:
        if not isinstance(key, (int, str, slice)):
            raise TypeError((f'{self.__class__.__name__}[key]: '
                             f'Expected key to be int, str or slice, not {key.__class__.__name__}'))
        return self.collection__internal__[key]

    def __contains__(self, key: Union[str, Any]) -> bool:
        if isinstance(key, str):
            return self.find(key) != -1
        else:
            return any(x == key for x in self)

    def find(self, name: str) -> int:
        if not isinstance(name, str):
            raise TypeError((f'{self.__class__.__name__}.find(name) '
                             f'Expected name to be str, not {name.__class__.__name__}'))
        return next((i for i, x in enumerate(self) if x.name == name), -1)

    def get(self, name: str, default: object) -> Any:
        if not isinstance(name, str):
            raise TypeError((f'{self.__class__.__name__}.get(name, default) '
                             f'Expected name to be str, not {name.__class__.__name__}'))
        return next((x for x in self if x.name == name), default)

    def index(self, item: ItemType) -> int:
        index = next((i for i, x in enumerate(self) if x == item), -1)
        if index == -1:
            raise ValueError((f'{self.__class__.__name__}.index(item): '
                              f'item is not a member of this collection'))
        return index

    def keys(self) -> Iterable[str]:
        return self.collection__internal__.keys()

    def items(self) -> Iterable[Tuple[str, ItemType]]:
        return self.collection__internal__.items()

    def values(self) -> Iterable[ItemType]:
        return self.collection__internal__.values()

LayerType = TypeVar('LayerType', bound=Layer)

class LayerCollection(ItemCollection[LayerType]):

    def move(self, from_index: int, to_index: int) -> None:

        if not isinstance(from_index, int):
            raise TypeError((f'{self.__class__.__name__}.move(from_index, to_index): '
                             f'Expected from_index to be int, not {from_index.__class__.__name__}'))

        if not isinstance(to_index, int):
            raise TypeError((f'{self.__class__.__name__}.move(from_index, to_index): '
                             f'Expected to_index to be int, not {to_index.__class__.__name__}'))

        if 0 > from_index >= len(self):
            raise IndexError((f'{self.__class__.__name__}.move(from_index, to_index): '
                              f'from_index {from_index} out of range 0-{len(self)-1}'))

        if 0 > to_index >= len(self):
            raise IndexError((f'{self.__class__.__name__}.move(from_index, to_index): '
                              f'to_index {to_index} out of range 0-{len(self)-1}'))

        if from_index != to_index:
            self.collection__internal__.move(from_index, to_index)
            return True

    def search(self, identifier: str) -> Optional[LayerType]:
        return next((item for item in self if item.identifier == identifier), None)