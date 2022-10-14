
from bpy.types import NodeTree
from .base import RBFDriverNodeSubtree


class RBFDriverNodeTreePoses(RBFDriverNodeSubtree, NodeTree):
    bl_idname = 'RBFDriverNodeTreePoses'
    bl_label = "Poses"
