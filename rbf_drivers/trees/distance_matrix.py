
from bpy.types import NodeTree
from .base import RBFDriverNodeSubtree


class RBFDriverNodeTreeDistanceMatrix(RBFDriverNodeSubtree, NodeTree):
    bl_idname = 'RBFDriverNodeTreeDistanceMatrix'
    bl_label = "Distance Matrix"
