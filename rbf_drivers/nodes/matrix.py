
from typing import TYPE_CHECKING, Sequence
from bpy.types import Node
from bpy.props import IntProperty
from ..core import RBFDriverNode
if TYPE_CHECKING:
    from bpy.types import Context, UILayout
    from ..sockets.matrix import RBFDriverNodeSocketMatrix

class RBFDriverNodeMatrix(RBFDriverNode, Node):
    bl_idname = 'RBFDriverNodeMatrix'
    bl_label = "Matrix"

    def resize(self, length: int) -> None:
        length = max(length, 0)
        inputs = self.inputs
        while len(inputs) > length: inputs.remove(inputs[len(inputs)-1])
        while len(inputs) < length: inputs.new('RBFDriverNodeSocketArray', str(len(inputs)))

    length: IntProperty(
        name="Length",
        min=0,
        get=lambda self: len(self.inputs),
        set=resize,
        options=set(),
        )

    def init(self, _: 'Context') -> None:
        self.outputs.new('RBFDriverNodeSocketMatrix', "Matrix")

    def data(self, _: 'RBFDriverNodeSocketMatrix') -> Sequence[Sequence[float]]:
        data = tuple(i.data() for i in self.inputs)
        return data if len(set(map(len, data))) < 2 else tuple()

    def draw_buttons(self, _: 'Context', layout: 'UILayout') -> None:
        layout.prop(self, "length")

    def validate(self) -> None:
        inputs = self.inputs
        if len(set(map(len, (i.data() for i in self.inputs)))) > 1:
            error = "Length mismatch"
        else:
            error = ""
        for input in inputs:
            input.error = error
