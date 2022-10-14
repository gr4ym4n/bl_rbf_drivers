
from typing import Sequence
from bpy.types import NodeSocket, NodeSocketInterface
from ..core import RBFDriverNodeSocket, RBFDriverNodeSocketInterface, cache


class RBFDriverNodeSocketArray(RBFDriverNodeSocket, NodeSocket):
    bl_idname = 'RBFDriverNodeSocketArray'
    bl_label = "Array"
    value = tuple()
    draw_value = RBFDriverNodeSocket.draw_label

    @cache
    def data(self) -> Sequence[float]:
        return tuple()


class RBFDriverNodeSocketArrayInterface(RBFDriverNodeSocketInterface, NodeSocketInterface):
    bl_idname = 'RBFDriverNodeSocketArrayInterface'
    bl_socket_idname = RBFDriverNodeSocketArray.bl_idname
    bl_label = RBFDriverNodeSocketArray.bl_label
