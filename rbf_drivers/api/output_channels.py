
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
