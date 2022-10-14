
from typing import TYPE_CHECKING, Tuple
from bpy.types import NodeSocket
from bpy.props import FloatProperty
from .mixins import Labeled
if TYPE_CHECKING:
    from bpy.types import Context, Node, UILayout
    from ..mixins import RBFDNode


def value_update_callback(socket: 'RBFDFloatSocket', context: 'Context') -> None:
    if socket.is_output:
        pass
    else:
        node: 'RBFDNode' = socket.node
        node.on_input_value_update(socket)


class RBFDFloatSocket(Labeled, NodeSocket):
    bl_idname = 'RBFDFloatSocket'
    bl_label = "Float"

    value: FloatProperty(
        name="Value",
        default=0.0,
        options=set(),
        update=value_update_callback
        )

    def draw(self, context: 'Context', layout: 'UILayout', node: 'Node', text: str) -> None:
        if self.is_output:
            layout.label(text=self.label_resolve(text))
        else:
            layout.prop(self, "value", text=self.label_resolve(text))

    def draw_color(self, context: 'Context', node: 'Node') -> Tuple[float, float, float, float]:
        return (1.0, 0.0, 0.0, 0.0)


