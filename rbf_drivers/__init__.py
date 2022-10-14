'''
Copyright (C) 2021 James Snowden
james@metaphysic.al
Created by James Snowden
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

bl_info = {
    "name": "RBF Drivers",
    "description": "Radial basis function drivers.",
    "author": "James Snowden",
    "version": (2, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D > Properties > Object",
    "doc_url": "https://jamesvsnowden.github.io/bl_rbf_drivers/",
    "tracker_url": "https://github.com/jamesvsnowden/bl_rbf_drivers/issues",
    "category": "Animation",
    "warning": ""
}

from nodeitems_utils import NodeCategory, NodeItem
from . import core, sockets, nodes



# class RBFDriverVectorSample(Operator):
#     bl_idname = 'rbfdriver.vector_sample'
#     bl_label = "Sample"
#     bl_options = {'INTERNAL', 'UNDO'}

#     node_name: StringProperty()

#     @classmethod
#     def poll(cls, context: 'Context') -> bool:
#         space = context.space_data
#         if space is not None:
#             tree = getattr(space, "node_tree", None)
#             return tree is not None and tree.bl_idname.startswith('RBFDriver')
#         return False

#     def execute(self, context: 'Context') -> Set[str]:
#         # TODO requires error checking
#         tree = context.space_data.node_tree
#         node = tree.nodes.get(self.node_name)
#         if node and node.bl_idname == 'RBFDriverNodeVector':
#             for input_, scalar in zip(node.inputs[1:], node.inputs[0].data()):
#                 input_["default_value"] = scalar.value
#         return {'FINISHED'}


# class RBFDriverInputAdd(Operator):
#     bl_idname = 'rbfdriver.input_add'
#     bl_label = "Add"
#     bl_options = {'INTERNAL', 'UNDO'}

#     type: EnumProperty(
#         name="Type",
#         items=RBFDriverNodeGroupInput.TYPES,
#         default='LOCATION',
#         options=set()
#         )

#     @classmethod
#     def poll(cls, context: 'Context') -> bool:
#         space = context.space_data
#         if space is not None:
#             tree = getattr(space, "node_tree", None)
#             return tree is not None and tree.bl_idname == 'RBFDriverNodeTreeMain'
#         return False

#     def execute(self, context: 'Context') -> Set[str]:
#         tree = context.space_data.node_tree
#         name = RBFDriverNodeGroupInput.TYPES[self.get("type", 0)[1]]
#         tree.nodes.new(name, 'RBFDriverNodeGroupInput').type = self.type
#         return {'FINISHED'}


# class RBFDriverInputList(UIList):
#     bl_idname = 'RBFDRIVER_UL_inputs'

#     def draw_item(self, _0,
#                   layout: 'UILayout', _1,
#                   group: RBFDriverNodeGroupInput, _2, _3, _4) -> None:
#         layout.prop(group, "name", text="", emboss=False, translate=False)

#     def filter_items(self, context: 'Context', tree: RBFDriverNodeTreeMain, _):
#         flag = self.bitflag_filter_item
#         mask = ~flag
#         name = RBFDriverNodeGroupInput.bl_idname
#         nodes = tree.nodes
#         flags = [flag if node.bl_idname == name else mask for node in nodes]
#         order = list(range(len(flags)))
#         return flags, order


# class RBFDriverPoseList(UIList):
#     bl_idname = 'RBFDRIVER_UL_poses'

#     def draw_item(self, _0,
#                   layout: 'UILayout', _1,
#                   node: RBFDriverNodePose, _2, _3, _4) -> None:
#         layout.prop(node, "name", text="", emboss=False, translate=False)

#     def filter_items(self, context: 'Context', tree: RBFDriverNodeTreeMain, _):
#         flag = self.bitflag_filter_item
#         mask = ~flag
#         name = 'RBFDriverNodePose'
#         nodes = tree.nodes
#         flags = [flag if node.bl_idname == name else mask for node in nodes]
#         order = list(range(len(flags)))
#         return flags, order


# class RBFDriverInputPanel(Panel):
#     bl_idname = 'RBFDRIVER_PT_input'
#     bl_space_type = 'NODE_EDITOR'
#     bl_region_type = 'UI'
#     bl_category = "Layers"
#     bl_label = "Inputs"

#     @classmethod
#     def poll(cls, context: 'Context') -> bool:
#         space = context.space_data
#         if space is not None:
#             tree = getattr(space, "node_tree", None)
#             return tree is not None and tree.bl_idname == RBFDriverNodeTreeMain.bl_idname
#         return False

#     def draw(self, context: 'Context') -> None:
#         tree = context.space_data.node_tree
#         layout = self.layout
#         row = layout.row()
#         row.template_list(RBFDriverInputList.bl_idname, "", tree, "nodes", tree, "input_active_index")
#         col = row.column(align=True)
#         col.operator_menu_enum(RBFDriverInputAdd.bl_idname, "type", text="", icon='ADD')
                


class RBFDriverNodeCategoryMain(NodeCategory):
    @classmethod
    def poll(cls, ctx):
        return ctx.space_data.tree_type == 'RBFDriverNodeTreeMain'


NODE_CATEGORIES = [
    RBFDriverNodeCategoryMain('INPUT', "Input", items=[
        NodeItem('RBFDriverNodeInputLocation', label="Location"),
        NodeItem('RBFDriverNodeInputRotation', label="Rotation"),
        NodeItem('RBFDriverNodeInputScale', label="Scale"),
        NodeItem('RBFDriverNodeInputTransformChannel', label="Transform Channel"),
        NodeItem('RBFDriverNodeInputLocDiff', label="Distance"),
        NodeItem('RBFDriverNodeInputRotationDiff', label="Rotational Difference"),
        NodeItem('RBFDriverNodeInputMapping', label="Input Mapping"),
    ]),
    RBFDriverNodeCategoryMain('STRUCT', "Data Structure", items=[
        NodeItem('RBFDriverNodeArray', label="Array"),
        NodeItem('RBFDriverNodeArray', label="Location", settings={"subtype": repr('LOCATION')}),
        NodeItem('RBFDriverNodeArray', label="Euler", settings={"subtype": repr('EULER')}),
        NodeItem('RBFDriverNodeArray', label="Quaternion", settings={"subtype": repr('QUATERNION')}),
        NodeItem('RBFDriverNodeArray', label="Axis/Angle", settings={"subtype": repr('AXIS_ANGLE')}),
        NodeItem('RBFDriverNodeArray', label="Scale", settings={"subtype": repr('SCALE')}),
        NodeItem('RBFDriverNodeArray', label="RGB Color", settings={"subtype": repr('RGB')}),
        NodeItem('RBFDriverNodeArray', label="HSV Color", settings={"subtype": repr('HSV')}),
        NodeItem('RBFDriverNodeMatrix', label="Matrix")
    ]),
    RBFDriverNodeCategoryMain('RBF', "RBF", items=[
        NodeItem('RBFDriverNodePose', label="Pose"),
        NodeItem('RBFDriverNodePoseGroup', label="Pose Group"),
    ]),
    RBFDriverNodeCategoryMain('DISTANCE', "Distance", items=[
        NodeItem('RBFDriverNodeDistance', label="Distance Euclidean", settings={"function": repr('EUCLIDEAN')}),
        NodeItem('RBFDriverNodeDistance', label="Distance Angle", settings={"function": repr('ANGLE')}),
        NodeItem('RBFDriverNodeDistance', label="Distance Quaternion", settings={"function": repr('QUATERNION')}),
        NodeItem('RBFDriverNodeDistance', label="Distance Swing X", settings={"function": repr('SWING_X')}),
        NodeItem('RBFDriverNodeDistance', label="Distance Swing Y", settings={"function": repr('SWING_Y')}),
        NodeItem('RBFDriverNodeDistance', label="Distance Swing Z", settings={"function": repr('SWING_Z')}),
    ])
]

CLASSES = core.CLASSES + sockets.CLASSES + nodes.CLASSES


def register():
    from bpy.utils import register_class
    from nodeitems_utils import register_node_categories
    for cls in CLASSES:
        register_class(cls)
    register_node_categories(core.RBFDriverNodeTreeMain.bl_idname, NODE_CATEGORIES)


def unregister():
    from bpy.utils import unregister_class
    from nodeitems_utils import unregister_node_categories
    unregister_node_categories(core.RBFDriverNodeTreeMain.bl_idname)
    for cls in reversed(CLASSES):
        unregister_class(cls)
