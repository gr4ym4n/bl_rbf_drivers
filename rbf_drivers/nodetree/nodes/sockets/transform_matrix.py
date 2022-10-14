
from typing import TYPE_CHECKING, Tuple
from bpy.types import NodeSocket
from bpy.props import FloatVectorProperty
from .mixins import Expandable, Labeled
if TYPE_CHECKING:
    from bpy.types import Context, Node, UILayout
    from ..mixins import RBFDNode


def value_update_callback(socket: 'RBFDTransformMatrixSocket', context: 'Context') -> None:
    if socket.is_output:
        pass
    else:
        node: 'RBFDNode' = socket.node
        node.on_input_value_update(socket)


class RBFDTransformMatrixSocket(Expandable, Labeled, NodeSocket):
    bl_idname = 'RBFDTransformMatrixSocket'
    bl_label = "Matrix"

    value: FloatVectorProperty(
        name="Value",
        size=16,
        precision=3,
        subtype='MATRIX',
        options=set(),
        update=value_update_callback
        )

    def draw(self, context: 'Context', layout: 'UILayout', node: 'Node', text: str) -> None:
        if self.is_output or not self.show_expanded:
            layout.label(text=self.label_resolve(text))
        else:
            idx = 0
            col = layout.column(align=True)
            for _0 in range(4):
                row = col.row(align=True)
                for _1 in range(4):
                    row.prop(self, "value", index=idx, text="")
                    idx += 1

    def draw_color(self, context: 'Context', node: 'Node') -> Tuple[float, float, float, float]:
        return (1.0, 0.0, 0.0, 0.0)
