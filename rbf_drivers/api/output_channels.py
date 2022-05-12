
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty
from .mixins import Collection, Searchable
from .output_channel import RBFDriverOutputChannel


class RBFDriverOutputChannels(Searchable[RBFDriverOutputChannel],
                              Collection[RBFDriverOutputChannel],
                              PropertyGroup):

    collection__internal__: CollectionProperty(
        type=RBFDriverOutputChannel,
        options={'HIDDEN'}
        )

    def __repr__(self) -> str:
        return self.__class__.__name__

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".collection__internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'