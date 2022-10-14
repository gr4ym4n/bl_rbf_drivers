
from typing import TYPE_CHECKING, Set
from bpy.types import NodeCustomGroup, Operator
from bpy.props import IntProperty
from .base import RBFDriverNodeGroup
from ..utils.layout import layout_nodes_columns
from ..utils.node import iternodes, findnode, listnodes
if TYPE_CHECKING:
    from bpy.types import Context, UILayout
    from ..sockets.base import RBFDriverNodeSocket


class RBFDriverNodeGroupPoses(RBFDriverNodeGroup, NodeCustomGroup):
    bl_idname = 'RBFDriverNodeGroupPoses'
    bl_label = "Poses"
    nt_type = 'RBFDriverNodeTreePoses'
    nt_name = "Poses"

    active_index: IntProperty(
        min=0,
        default=0,
        options=set()
        )

    def init(self, _) -> None:
        basis = findnode(self.id_data, 'RBFDriverNodeGroupPoses')
        super().init(_)
        tree = self.node_tree
        tree.inputs.new('RBFDriverNodeSocketVectorConfig', "Input")
        tree.outputs.new('RBFDriverNodeSocketMatrix', "Poses")
        input_ = tree.nodes.new('NodeGroupInput')
        matrix = tree.nodes.new('RBFDriverNodeMatrix')
        output = tree.nodes.new('NodeGroupOutput')
        tree.links.new(input_.outputs[0], matrix.inputs[0])
        tree.links.new(matrix.outputs[0], output.inputs[0])
        if basis:
            for node in iternodes(basis.node_tree, 'RBFDriverNodePose'):
                pose = tree.nodes.new('RBFDriverNodePose')
                pose["name"] = node.name
                pose.label = node.name
                pose["setup__internal__"] = True
        layout_nodes_columns([
            [input_],
            listnodes(tree, 'RBFDriverNodePose'),
            [matrix],
            [output]])

    def draw_buttons(self, _, layout: 'UILayout') -> None:
        row = layout.row()
        col = row.column()
        col.template_list('RBFDRIVER_UL_poses', "", self.node_tree, "nodes", self, "active_index")
        col = row.column(align=True)
        col.operator("rbfdriver.pose_add", text="", icon='ADD')
        col.separator()
        super().draw_buttons(_, col, text="")

    def push(self, input_: 'RBFDriverNodeSocket', data: object) -> None:
        return super().push(input_, data)


class RBFDriverPoseAdd(Operator):
    bl_idname = 'rbfdriver.pose_add'
    bl_label = "Add"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        space = context.space_data
        if space is not None:
            tree = getattr(space, "node_tree", None)
            return tree is not None and tree.bl_idname == 'RBFDriverNodeTreeMain'
        return False

    def execute(self, context: 'Context') -> Set[str]:
        groups = listnodes(context.space_data.node_tree, 'RBFDriverNodeGroupPoses')
        index = 0
        names = set()
        for group in groups:
            tree = group.node_tree
            if tree and tree.bl_idname == 'RBFDriverNodeTreePoses':
                for node in iternodes(tree, 'RBFDriverNodePose'):
                    names.add(node.name)
        name = "Pose"
        while name in names:
            index += 1
            name = f'Pose.{str(index).zfill(3)}'
        for group in groups:
            tree = group.node_tree
            if tree and tree.bl_idname == 'RBFDriverNodeTreePoses':
                node = tree.nodes.new('RBFDriverNodePose')
                node["name"] = name
                node.label = name
                node["setup__internal__"] = True
                layout_nodes_columns([
                    listnodes(tree, 'NodeGroupInput'),
                    listnodes(tree, 'RBFDriverNodePose'),
                    listnodes(tree, 'RBFDriverNodeMatrix'),
                    listnodes(tree, 'NodeGroupOutput'),
                    ])
        return {'FINISHED'}


class RBFDriverPoseRemove(Operator):
    bl_idname = 'rbfdriver.pose_remove'
    bl_label = "Remove"
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        space = context.space_data
        if space is not None:
            tree = getattr(space, "node_tree", None)
            return tree is not None and tree.bl_idname == 'RBFDriverNodeTreeMain'
        return False

    def execute(self, context: 'Context') -> Set[str]:
        return {'FINISHED'}