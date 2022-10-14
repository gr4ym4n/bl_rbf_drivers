
from typing import TYPE_CHECKING
from uuid import uuid4
from bpy.types import Object, Node, PoseBone
from bpy.props import EnumProperty
from .sockets.target import RBFDTargetSocket
from .sockets.transform_matrix import RBFDTransformMatrixSocket
from .mixins import RBFDNode
if TYPE_CHECKING:
    from bpy.types import Context, UILayout


def transform_space_update_callback(node: 'RBFDTargetTransformMatrixNode', _: 'Context') -> None:
    node.calculate_output()


class RBFDTargetTransformMatrixNode(RBFDNode, Node):
    bl_idname = 'RBFDTargetTransformMatrix'
    bl_label = "Target Transform Matrix"

    transform_space: EnumProperty(
        name="Space",
        items=[
            ('WORLD_SPACE'    , "World Space"    , "Transforms include effects of parenting/restpose and constraints"    ),
            ('TRANSFORM_SPACE', "Transform Space", "Transforms don't include parenting/restpose or constraints"          ),
            ('LOCAL_SPACE'    , "Local Space"    , "Transforms include effects of constraints but not parenting/restpose"),
            ],
        default='WORLD_SPACE',
        options=set(),
        update=transform_space_update_callback
        )

    def init(self, context: 'Context') -> None:
        self.inputs.new(RBFDTargetSocket.bl_idname, "Target", identifier=uuid4().hex).label="Target"
        self.outputs.new(RBFDTransformMatrixSocket.bl_idname, "Matrix", identifier=uuid4().hex)

    def calculate_output(self) -> None:
        socket: RBFDTargetSocket = self.inputs[0]
        target = socket.resolve()
        matrix = None
        if isinstance(target, PoseBone):
            space = self.transform_space
            if space == 'TRANSFORM_SPACE':
                matrix = target.matrix_channel
            else:
                matrix = target.id_data.convert_space(
                    pose_bone=target,
                    matrix=target.matrix,
                    from_space='POSE',
                    to_space=space[:5]
                    )
        elif isinstance(target, Object):
            space = self.transform_space
            if   space == 'LOCAL_SPACE': matrix = target.matrix_local
            elif space == 'WORLD_SPACE': matrix = target.matrix_world
            else                       : matrix = target.matrix_basis
        if matrix:
            output: RBFDTransformMatrixSocket = self.outputs[0]
            output.value = sum((matrix.col[i].to_tuple() for i in range(4)), tuple())

    def draw_buttons(self, context: 'Context', layout: 'UILayout') -> None:
        layout.prop(self, "transform_space", text="")

    def on_input_value_update(self, socket: RBFDTargetSocket) -> None:
        self.calculate_output()
