
from typing import TYPE_CHECKING, List
from bpy.types import NodeTree
from bpy.props import PointerProperty
from nodeitems_utils import NodeCategory, NodeItem
from .nodes import sockets
from . import nodes, tools
if TYPE_CHECKING:
    from bpy.types import Context


class RBFDNodeTree(NodeTree):
    bl_idname = 'RBFDNodeTree'
    bl_label = "RBF Drivers Node Tree"
    bl_icon = 'NODETREE'

    tools: PointerProperty(
        name="Tools",
        type=tools.RBFDTools,
        options=set()
        )


class RBFDNodeCategory(NodeCategory):
    @classmethod
    def poll(cls, context: 'Context') -> bool:
        return context.space_data.tree_type == RBFDNodeTree.bl_idname


RBFD_NODE_CATEGORIES: List[RBFDNodeCategory] = [
    RBFDNodeCategory('IO', "Input/Output", items=[
        NodeItem(nodes.RBFDTargetNode.bl_idname, label=nodes.RBFDTargetNode.bl_label),
        NodeItem(nodes.RBFDTargetTransformMatrixNode.bl_idname, label=nodes.RBFDTargetTransformMatrixNode.bl_label),
        NodeItem(nodes.RBFDTransformMatrixDecomposeNode.bl_idname, label="Decompose Matrix")
    ]),
    RBFDNodeCategory('SAMPLES', "Samples", items=[
        NodeItem(nodes.RBFDQuaternionSampleNode.bl_idname, label=nodes.RBFDQuaternionSampleNode.bl_label)
        ])
    ]


def register():
    from bpy.utils import register_class
    from nodeitems_utils import register_node_categories
    sockets.register()
    nodes.register()
    tools.register()
    register_class(RBFDNodeTree)
    register_node_categories(RBFDNodeTree.bl_idname, RBFD_NODE_CATEGORIES)


def unregister():
    from bpy.utils import unregister_class
    from nodeitems_utils import unregister_node_categories
    unregister_node_categories(RBFDNodeTree.bl_idname)
    unregister_class(RBFDNodeTree)
    tools.unregister()
    nodes.unregister()
    sockets.unregister()
