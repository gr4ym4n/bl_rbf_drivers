
from typing import TYPE_CHECKING
from bpy.types import NodeSocket, NodeSocketInterface
from bpy.props import EnumProperty, FloatProperty
from ..core import RBFDriverNodeSocket, RBFDriverNodeSocketInterface, cache
if TYPE_CHECKING:
    from bpy.types import UILayout


def factor_get(socket: 'RBFDriverNodeSocketFloat') -> float:
    return max(0.0, min(value_get(socket), 1.0))


def factor_set(socket: 'RBFDriverNodeSocketFloat', value: float) -> None:
    value_set(socket, max(0.0, min(value, 1.0)))


def value_get(socket: 'RBFDriverNodeSocketFloat') -> float:
    return socket.get("value", socket.default_value)


def value_set(socket: 'RBFDriverNodeSocketFloat', value: float) -> None:
    socket["value"] = value
    socket.value_update()


class RBFDriverNodeSocketFloat(RBFDriverNodeSocket, NodeSocket):
    bl_idname = 'RBFDriverNodeSocketFloat'
    bl_label = "Float"

    default_value: FloatProperty(
        name="Default",
        default=0.0,
        options={'HIDDEN'}
        )

    @cache
    def data(self) -> float:
        return self.value

    angle: FloatProperty(
        name="Value",
        get=value_get,
        set=value_set,
        subtype='ANGLE',
        options=set()
        )

    factor: FloatProperty(
        name="Value",
        min=0.0,
        max=1.0,
        get=factor_get,
        set=factor_set,
        subtype='FACTOR',
        options=set()
        )

    subtype: EnumProperty(
        name="Type",
        items=[
            ('VALUE', "Float", "", 'DRIVER_TRANSFORM', 0),
            ('ANGLE', "Angle", "", 'DRIVER_ROTATIONAL_DIFFERENCE', 1),
            ('FACTOR', "Factor", "", 'ZOOM_SELECTED', 2),
            ],
        default='VALUE',
        options=set()
        )

    value: FloatProperty(
        name="Value",
        get=value_get,
        set=value_set,
        options=set()
        )

    def draw_value(self, _, layout: 'UILayout', *__) -> None:
        layout.prop(self, self.subtype.lower(), text=self.name)


class RBFDriverNodeSocketFloatInterface(RBFDriverNodeSocketInterface, NodeSocketInterface):
    bl_idname = 'RBFDriverNodeSocketFloatInterface'
    bl_socket_idname = RBFDriverNodeSocketFloat.bl_idname
    bl_label = RBFDriverNodeSocketFloat.bl_label
