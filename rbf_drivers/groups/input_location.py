
from bpy.types import NodeCustomGroup
from bpy.props import BoolProperty
from .base import RBFDriverNodeGroup

class RBFDriverNodeGroupInputLocation(RBFDriverNodeGroup, NodeCustomGroup):
    bl_idname = 'RBFDriverNodeGroupInputLocation'
    bl_label = "Location Input"
    bl_width_default = 180

    def rebuild(self, _=None):
        with self.evaluation_context():
            ntree = self.node_tree
            ncols = [[], [], [], []]
            with ntree.update_context():
                nodes = ntree.nodes
                links = ntree.links
                nodes.clear()
                flags = (self.use_x, self.use_y, self.use_z)
                count = sum(flags)
                if count == 3:
                    vgroup = nodes.new('RBFDriverNodeVariableGroupVector')
                else:
                    vgroup = nodes.new('RBFDriverNodeVariableGroup')
                    vgroup.length = count
                ngi = nodes.new('NodeGroupInput')
                ngo = nodes.new('NodeGroupOutput')
                links.new(vgroup.outputs[0], ngo.inputs[0])
                index = 0
                for axis, flag in zip('XYZ', flags):
                    if flag:
                        var = nodes.new('RBFDriverNodeVariableTransforms')
                        var.transform_type = f'LOC_{axis}'
                        links.new(ngi.outputs[0], var.inputs[1])
                        links.new(ngi.outputs[1], var.inputs[2])
                        links.new(var.outputs[0], vgroup.inputs[index])
                        index += 1
                        ncols[1].append(var)
                ncols[0].append(ngi)
                ncols[2].append(vgroup)
                ncols[3].append(ngo)
            ntree.arrange_multi_column(ncols, spacing=(80, 120))

    use_x: BoolProperty(name="X", default=True, options=set(), update=rebuild)
    use_y: BoolProperty(name="Y", default=True, options=set(), update=rebuild)
    use_z: BoolProperty(name="Z", default=True, options=set(), update=rebuild)

    def build(self, *_):
        import bpy
        ntree = bpy.data.node_groups.new("RBFDriverInput", 'RBFDriverNodeTreeInput')
        ntree.parent__internal__ = self.id_data
        ntree.inputs.new('RBFDriverNodeSocketTransformTarget', "Target")
        ntree.inputs.new('RBFDriverNodeSocketTransformSpace', "Space")
        ntree.outputs.new('RBFDriverNodeSocketVariableGroup', "Variables")
        self.node_tree = ntree
        self.rebuild()

    def draw_buttons(self, _, layout):
        row = layout.row()
        sub = row.row(align=True)
        sub.prop(self, 'use_x', toggle=True)
        sub.prop(self, 'use_y', toggle=True)
        sub.prop(self, 'use_z', toggle=True)
        props = row.operator('rbfdriver.group_edit', icon='NODETREE', text="")
        props.group_name = self.node_tree.name

