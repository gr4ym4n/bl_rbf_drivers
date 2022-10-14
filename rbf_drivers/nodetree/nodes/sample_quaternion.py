
from typing import TYPE_CHECKING
from uuid import uuid4
from bpy.types import Node
from .mixins import RBFDNode
from .sockets.float import RBFDFloatSocket
from .sockets.quaternion import RBFDQuaternionSocket
if TYPE_CHECKING:
    from bpy.types import Context

class RBFDQuaternionSampleNode(RBFDNode, Node):
    bl_idname = 'RBFDQuaternionSampleNode'
    bl_label = "Quaternion"

    def init(self, context: 'Context') -> None:
        for label, value in zip("WXYZ", (1., 0., 0., 0.)):
            input_ = self.inputs.new(RBFDFloatSocket.bl_idname, label, identifier=uuid4().hex)
            input_.label = label
            input_.value = value
        output = self.outputs.new(RBFDQuaternionSocket.bl_idname, "", identifier=uuid4().hex)
        output.label = "Quaternion"

    def on_input_value_update(self, socket: RBFDFloatSocket) -> None:
        print("Input value update")