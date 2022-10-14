
import bpy
import uuid
from .sockets.target import ID_TYPE_TABLE, RBFDTargetSocket, ID_TYPE_FIELD, ID_TYPE_ICONS
from .mixins import RBFDNode

class RBFDTargetNode(RBFDNode, bpy.types.Node):
    bl_idname = 'RBFDTargetNode'
    bl_label = "Target"
    bl_width_default = 240

    def init(self, context: bpy.types.Context) -> None:
        self.outputs.new(RBFDTargetSocket.bl_idname, "Target", identifier=uuid.uuid4().hex)

    def draw_buttons(self, context: bpy.types.Context, layout: bpy.types.UILayout) -> None:
        output = self.outputs["Target"]
        row = layout.row(align=True)
        row.prop(output, "id_type", text="", icon_only=True)
        col = row.column(align=True)
        col.prop_search(output, "id",
                        bpy.data, ID_TYPE_FIELD[output.id_type],
                        text="", icon=ID_TYPE_ICONS[output.id_type])
        if output.id_type == 'OBJECT':
            id_ = output.id
            if id_ is not None and id_.type == 'ARMATURE':
                col.prop_search(output, "bone_target", id_.data, "bones",
                                icon='BONE_DATA', text="")

    def insert_link(self, link: bpy.types.NodeLink) -> None:
        socket = link.to_socket
        if isinstance(socket, RBFDTargetSocket):
            output = self.outputs[0]
            socket["id_type"] = ID_TYPE_TABLE[output.id_type]
            socket["id"] = output.id
            socket["bone_target"] = output.bone_target
            node: RBFDNode = link.to_node
            node.on_input_value_update(socket)