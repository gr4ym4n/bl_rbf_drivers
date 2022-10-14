

from bpy.types import Node
from bpy.props import IntProperty


def input_count_update_callback(node: 'RBFDEuclideanDistanceDriverNode', _: 'Context') -> None:
    pass


class RBFDEuclideanDistanceDriverNode(Node):
    
    input_count: IntProperty(
        name="Inputs",
        min=0,
        max=16,
        options=set(),
        update=input_count_update_callback
        )

    def draw_buttons(self, context: 'Context', layout: 'UILayout') -> None:
        layout.prop(self, "input_count")
        