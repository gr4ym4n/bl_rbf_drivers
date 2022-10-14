
from typing import Iterator, List, Optional, TYPE_CHECKING, Tuple, Union
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, StringProperty
if TYPE_CHECKING:
    from ..nodes.mixins import RBFDNode


def noderef_name_get(ref: 'RBFDNodeReference') -> str:
    return ref.get("name", "")


def noderef_name_set(ref: 'RBFDNodeReference', _) -> None:
    raise AttributeError("RBFDNodeReference.name is read-only")


class RBFDNodeReference(PropertyGroup):

    identifier: StringProperty(
        name="Identifier",
        get=lambda self: self.get("identifier", ""),
        options={'HIDDEN'}
        )

    name: StringProperty(
        name="Name",
        get=noderef_name_get,
        set=noderef_name_set,
        options=set()
        )

    def resolve(self) -> Optional['RBFDNode']:
        return self.id_data.nodes.get(self.identifier)


class RBFDNodeReferences(PropertyGroup):

    internal__: CollectionProperty(
        type=RBFDNodeReference,
        options={'HIDDEN'}
        )

    def __contains__(self, name: str) -> bool:
        return name in self.internal__

    def __getitem__(self, key: Union[str, int, slice]) -> Union[RBFDNodeReference,
                                                                List[RBFDNodeReference]]:
        return self.internal__[key]

    def __iter__(self) -> Iterator[RBFDNodeReference]:
        return iter(self.internal__)

    def __len__(self) -> int:
        return len(self.internal__)

    def get(self, name: str) -> Optional[RBFDNodeReference]:
        return self.internal__.get(name)

    def keys(self) -> Iterator[RBFDNodeReference]:
        return self.internal__.keys()

    def items(self) -> Iterator[Tuple[str, RBFDNodeReference]]:
        return self.internal__.items()
