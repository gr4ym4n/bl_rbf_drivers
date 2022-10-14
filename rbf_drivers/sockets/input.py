
from typing import TYPE_CHECKING
from bpy.types import NodeSocket, NodeSocketInterface
from bpy.props import EnumProperty, IntProperty
from ..data import Input, InputMapping, InputType, Target, VectorDataType
from ..core import RBFDriverNodeSocket, RBFDriverNodeSocketInterface, cache
if TYPE_CHECKING:
    from bpy.types import Context, Node, UILayout


COLOR = (0.365, 0.714, 0.918, 1.)


class RBFDriverNodeSocketInput(RBFDriverNodeSocket, NodeSocket):
    bl_idname = 'RBFDriverNodeSocketInput'
    bl_label = "Input"
    VALID_COLOR = COLOR
    draw_value = RBFDriverNodeSocket.draw_label

    @cache
    def data(self) -> Input:
        return Input(type=InputType.SINGLE_PROP, name=self.name, targets=(Target(),))


class RBFDriverNodeSocketInputMapping(RBFDriverNodeSocket, NodeSocket):
    bl_idname = 'RBFDriverNodeSocketInputMapping'
    bl_label = "Inputs"
    VALID_COLOR = COLOR
    draw_value = RBFDriverNodeSocket.draw_label

    @cache
    def data(self) -> InputMapping:
        return InputMapping()


class RBFDriverNodeSocketInputInterface(RBFDriverNodeSocketInterface, NodeSocketInterface):
    bl_idname = 'RBFDriverNodeSocketInputInterface'
    bl_socket_idname = RBFDriverNodeSocketInput.bl_idname
    bl_label = RBFDriverNodeSocketInput.bl_label


class RBFDriverNodeSocketInputMappingInterface(RBFDriverNodeSocketInterface, NodeSocketInterface):
    bl_idname = 'RBFDriverNodeSocketInputMappingInterface'
    bl_socket_idname = RBFDriverNodeSocketInputMapping.bl_idname
    bl_label = RBFDriverNodeSocketInputMapping.bl_label


CLASSES = [
    RBFDriverNodeSocketInput,
    RBFDriverNodeSocketInputMapping,
    RBFDriverNodeSocketInputInterface,
    RBFDriverNodeSocketInputMappingInterface,
]