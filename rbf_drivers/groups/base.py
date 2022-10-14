
from bpy.types import Operator
from bpy.props import StringProperty
from ..nodes.base import RBFDriverNode


class RBFDriverNodeGroupEdit(Operator):
    bl_idname = 'rbfdriver.group_edit'
    bl_label = "Edit"
    bl_options = {'INTERNAL'}

    group_name: StringProperty()

    @classmethod
    def poll(cls, context):
        space = context.space_data
        if space is not None:
            tree = getattr(space, "node_tree", None)
            return tree is not None and tree.bl_idname == 'RBFDriverNodeTreeMain'
        return False

    def execute(self, context):
        node = context.node
        grps = context.blend_data.node_groups
        path = context.space_data.path
        path.clear()
        path.start(node.id_data)
        path.append(grps[self.group_name])
        return {'FINISHED'}


class RBFDriverNodeGroup(RBFDriverNode):

    @classmethod
    def poll(cls, tree):
        return tree.bl_idname == 'RBFDriverNodeTreeMain'

    def free(self):
        import bpy
        bpy.node_groups.remove(self.node_tree)

    def evaluate(self):
        ntree = self.node_tree
        if ntree:
            ntree.pause_evaluation()
            nodes = ntree.nodes
            group = next((n for n in nodes if n.bl_idname == 'NodeGroupInput'), None)
            if group:
                for src in self.inputs:
                    tgt = next((i for i in group.outputs if i.identifier == src.identifier))
                    if tgt:
                        a = src.data
                        b = tgt.data
                        if a != b:
                            tgt.data = a
            ntree.unpause_evaluation()
            group = next((n for n in nodes if n.bl_idname == 'NodeGroupOutput'), None)
            if group:
                for tgt in self.outputs:
                    src = next((i for i in group.inputs if i.identifier == tgt.identifier))
                    if src:
                        tgt.data = src.data
