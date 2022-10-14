
from bpy.types import NodeTree
from .base import RBFDriverNodeSubtree


class RBFDriverNodeTreeInput(RBFDriverNodeSubtree, NodeTree):
    bl_idname = 'RBFDriverNodeTreeInput'
    bl_label = "Input"
