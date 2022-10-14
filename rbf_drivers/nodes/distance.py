
from typing import TYPE_CHECKING
from math import acos, asin, dist, floor, pi
from bpy.types import Node
from bpy.props import EnumProperty
from ..core import RBFDriverNode
if TYPE_CHECKING:
    from bpy.types import Context, UILayout
    from ..sockets.float import RBFDriverNodeSocketFloat


class RBFDriverNodeDistance(RBFDriverNode, Node):
    bl_idname = 'RBFDriverNodeDistance'
    bl_label = "Distance"

    def function_update_handler(self, _: 'Context') -> None:
        self.validate()
        self.value_update()

    function: EnumProperty(
        name="Function",
        items=[
            ('EUCLIDEAN', "Euclidean", ""),
            ('QUATERNION', "Quaternion", ""),
            ('ANGLE', "Angle", ""),
            ('SWING_X', "Swing X", ""),
            ('SWING_Y', "Swing Y", ""),
            ('SWING_Z', "Swing Z", ""),
            ],
        default='EUCLIDEAN',
        options=set(),
        update=function_update_handler
        )

    def init(self, _: 'Context') -> None:
        self.inputs.new('RBFDriverNodeSocketArray', "A")
        self.inputs.new('RBFDriverNodeSocketArray', "B")
        self.outputs.new('RBFDriverNodeSocketFloat', "Distance")

    def data(self, _: 'RBFDriverNodeSocketFloat') -> float:
        p = self.inputs[0].data()
        q = self.inputs[1].data()
        if len(p) != len(q):
            return 0.0
        f = self.function
        if f == 'QUATERNION' or f.startswith('SWING'):
            if len(p) != 4:
                return 0.0
            if f == 'QUATERNION':
                return acos((2.0*pow(min(max(sum(a*b for a,b in zip(p,q)),-1.0),1.0),2.0)),-1.0)/pi
            else:
                pw, px, py, pz = p
                qw, qx, qy, qz = q
                if f == 'SWING_X':
                    p = (1.0 - 2.0 * (py*py+pz*pz),2.0*(px*py+pw*pz),2.0*(px*pz-pw*py))
                    q = (1.0 - 2.0 * (qy*qy+qz*qz),2.0*(qx*qy+qw*qz),2.0*(qx*qz-qw*qy))
                elif f == 'SWING_Z':
                    p = (2.0*(px*pz+pw*py),2.0*(py*pz-pw*px),1.0-2.0*(px*px+py*py))
                    q = (2.0*(qx*qz+qw*qy),2.0*(qy*qz-qw*qx),1.0-2.0*(qx*qx+qy*qy))
                else:
                    p = (2.0*(px*py-pw*pz),1.0-2.0*(px*px+pz*pz),2.0*(py*pz+pw*px))
                    q = (2.0*(qx*qy-qw*qz),1.0-2.0*(qx*qx+qz*qz),2.0*(qy*qz+qw*qx))
                return (asin((sum(a*b for a,b in zip(p,q)))) - -(pi / 2.0)) / pi
        elif f == 'ANGLE':
            p = tuple(-pi*2*floor((x+pi)/pi*2) for x in p)
            q = tuple(-pi*2*floor((x+pi)/pi*2) for x in q)
        return dist(p, q)

    def validate(self) -> None:
        a = self.inputs[0]
        b = self.inputs[1]
        p = a.data()
        q = b.data()
        f = self.function
        if f == 'QUATERNION' or f.startswith('SWING'):
            a.error = "" if len(p) == 4 else "Invalid length"
            b.error = "" if len(q) == 4 else "Invalid length"
        else:
            if len(p) == len(q):
                a.error = ""
                b.error = ""
            else:
                a.error = "Length mismatch"
                b.error = "Length mismatch"

    def draw_buttons(self, _: 'Context', layout: 'UILayout') -> None:
        layout.prop(self, "function", text="")
