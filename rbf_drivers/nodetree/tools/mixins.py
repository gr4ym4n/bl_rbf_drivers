
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from bpy.types import Context

class ActiveNodeTree:

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        space = context.space_data
        if space is not None:
            tree = getattr(space, "node_tree", None)
            return tree is not None and tree.bl_idname == 'RBFDNodeTree'
        return False