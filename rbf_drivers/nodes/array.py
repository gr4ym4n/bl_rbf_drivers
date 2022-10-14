
from typing import Sequence, TYPE_CHECKING, Tuple
from bpy.types import Node
from bpy.props import EnumProperty, IntProperty
from ..core import RBFDriverNode
if TYPE_CHECKING:
    from ..sockets.float import RBFDriverNodeSocketFloat
    from ..sockets.array import RBFDriverNodeSocketArray


class RBFDriverNodeArray(RBFDriverNode, Node):
    bl_idname = 'RBFDriverNodeArray'
    bl_label = "Array"

    def _resize(self, size: int) -> Sequence['RBFDriverNodeSocketFloat']:
        inputs = self.inputs
        while len(inputs) > size: inputs.remove(inputs[0])
        while len(inputs) < size: inputs.new('RBFDriverNodeSocketFloat', str(len(inputs)))
        return inputs

    def _format_none(self) -> None:
        for n, i in enumerate(self._resize(self.length)):
            i.name = str(n)
        self.outputs[0].name = "Array"

    def _format_location(self) -> None:
        for i, k in zip(self._resize(3), 'XYZ'):
            i.name = k
            i.subtype = 'VALUE'
            i.default_value = 0.0
        self.outputs[0].name = "Location"

    def _format_scale(self) -> None:
        for i, k in zip(self._resize(3), 'XYZ'):
            i.name = k
            i.subtype = 'VALUE'
            i.default_value = 1.0
        self.outputs[0].name = "Scale"

    def _format_quaternion(self) -> None:
        for i, k in zip(self._resize(4), 'WXYZ'):
            i.name = k
            i.subtype = 'VALUE'
            i.default_value = float(k == 'W')
        self.outputs[0].name = "Quaternion"

    def _format_euler(self) -> None:
        for i, k in zip(self._resize(3), 'XYZ'):
            i.name = k
            i.subtype = 'ANGLE'
            i.default_value = 0.0
        self.outputs[0].name = "Euler"

    def _format_axis_angle(self) -> None:
        for i, k in zip(self._resize(4), 'WXYZ'):
            i.name = k
            i.subtype = 'ANGLE' if k == 'W' else 'VALUE'
            i.default_value = float(k == 'Y')
        self.outputs[0].name = "Axis/Angle"

    def _format_color(self) -> None:
        for i, k in zip(self._resize(3), 'RGB'):
            i.name = k
            i.subtype = 'FACTOR'
            i.default_value = 0.0
        self.outputs[0].name = "Color"

    def _format(self, _=None) -> None:
        getattr(self, f'_format_{self.subtype.lower()}')()

    def _update(self, _) -> None:
        self._format()

    subtype: EnumProperty(
        items=[
            ('NONE', "Array", ""),
            ('LOCATION', "Location", ""),
            ('EULER', "Euler", ""),
            ('QUATERNION', "Quaternion", ""),
            ('AXIS_ANGLE', "Axis/Angle", ""),
            ('SCALE', "Scale", ""),
            ('COLOR', "Color", ""),
            ],
        default='NONE',
        options=set(),
        update=_update
        )

    length: IntProperty(
        name="Length",
        min=0,
        default=0,
        options=set(),
        update=_update
        )

    def init(self, _) -> None:
        self.outputs.new('RBFDriverNodeSocketArray', "Array")
        self._format(_)

    def draw_buttons(self, _, layout):
        row = layout.row(align=True)
        row.prop(self, "subtype", text="")
        if self.subtype == 'NONE':
            row = row.row(align=True)
            row.ui_units_x = 4
            row.prop(self, "length", text="")

    def data(self, _: 'RBFDriverNodeSocketArray') -> Tuple[float, ...]:
        return tuple(i.data() for i in self.inputs)
