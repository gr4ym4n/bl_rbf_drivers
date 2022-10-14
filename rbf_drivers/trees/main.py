
from bpy.types import NodeTree
from bpy.props import IntProperty
from .base import RBFDriverNodeTree


class RBFDriverNodeTreeMain(RBFDriverNodeTree, NodeTree):
    bl_idname = 'RBFDriverNodeTreeMain'
    bl_label = "RBF Driver"

    input_active_index: IntProperty(
        min=0,
        default=0,
        options=set()
        )