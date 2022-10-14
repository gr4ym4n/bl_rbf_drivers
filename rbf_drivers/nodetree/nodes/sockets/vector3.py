
from typing import TYPE_CHECKING, Tuple
from bpy.types import NodeSocket
from bpy.props import FloatVectorProperty
from .mixins import Expandable, Labeled, FloatArray
if TYPE_CHECKING:
    from bpy.types import Context, Node, UILayout
    from ..mixins import RBFDNode


def value_update_callback(socket: 'RBFDVector3Socket', context: 'Context') -> None:
    if socket.is_output:
        pass
    else:
        node: 'RBFDNode' = socket.node
        node.on_input_value_update(socket)


class RBFDVector3Socket(Expandable, Labeled, FloatArray, NodeSocket):
    bl_idname = 'RBFDVector3Socket'
    bl_label = "Vector"

    value: FloatVectorProperty(
        name="Value",
        size=3,
        precision=3,
        subtype='XYZ',
        default=(0., 0., 0.),
        options=set(),
        update=value_update_callback
        )

    def draw(self, context: 'Context', layout: 'UILayout', node: 'Node', text: str) -> None:
        if self.is_output or not self.show_expanded:
            layout.label(text=self.label_resolve(text))
        else:
            column = layout.column(align=True)
            for index, label in enumerate("XYZ"):
                column.prop(self, "value", index=index, text=label)

    def draw_color(self, context: 'Context', node: 'Node') -> Tuple[float, float, float, float]:
        return (1.0, 0.0, 0.0, 0.0)
