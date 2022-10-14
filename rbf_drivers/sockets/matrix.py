
from typing import Sequence
from bpy.types import NodeSocket, NodeSocketInterface
from ..core import RBFDriverNodeSocket, RBFDriverNodeSocketInterface, cache


class RBFDriverNodeSocketMatrix(RBFDriverNodeSocket, NodeSocket):
    bl_idname = 'RBFDriverNodeSocketMatrix'
    bl_label = "Array"
    value = tuple()
    draw_value = RBFDriverNodeSocket.draw_label

    @cache
    def data(self) -> Sequence[Sequence[float]]:
        return tuple()


class RBFDriverNodeSocketMatrixInterface(RBFDriverNodeSocketInterface, NodeSocketInterface):
    bl_idname = 'RBFDriverNodeSocketMatrixInterface'
    bl_socket_idname = RBFDriverNodeSocketMatrix.bl_idname
    bl_label = RBFDriverNodeSocketMatrix.bl_label
