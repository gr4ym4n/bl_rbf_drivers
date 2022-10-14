
from typing import TYPE_CHECKING
from uuid import uuid4
from bpy.types import Node
from .mixins import RBFDNode
from .sockets.transform_matrix import RBFDTransformMatrixSocket
from .sockets.quaternion import RBFDQuaternionSocket
from .sockets.vector3 import RBFDVector3Socket
if TYPE_CHECKING:
    from bpy.types import Context


class RBFDTransformMatrixDecomposeNode(RBFDNode, Node):
    bl_idname = 'RBFDTransformMatrixDecomposeNode'
    bl_label = "Decompose"

    def init(self, context: 'Context') -> None:
        matrix = self.inputs.new(RBFDTransformMatrixSocket.bl_idname, "Matrix", identifier=uuid4().hex)
        matrix.label="Matrix"
        
        location = self.outputs.new(RBFDVector3Socket.bl_idname, "Location", identifier=uuid4().hex)
        location.label="Location"

        rotation = self.outputs.new(RBFDQuaternionSocket.bl_idname, "Rotation", identifier=uuid4().hex)
        rotation.label = "Rotation"

        scale = self.outputs.new(RBFDVector3Socket.bl_idname, "Scale", identifier=uuid4().hex)
        scale.label = "Scale"
        scale.value = (1., 1., 1.)

    def on_input_value_update(self, socket: RBFDTransformMatrixSocket) -> None:
        matrix = socket.value
        self.outputs["Location"].value = matrix.to_translation()
        self.outputs["Rotation"].value = matrix.to_quaternion()
        self.outputs["Scale"].value = matrix.to_scale()
