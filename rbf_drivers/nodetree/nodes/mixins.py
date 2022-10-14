
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from bpy.types import Context, NodeSocket, NodeTree


class RBFDNode:

    @classmethod
    def poll(cls, nodetree: 'NodeTree') -> bool:
        return nodetree.bl_idname == 'RBFDNodeTree'

    def on_input_value_update(self, socket: 'NodeSocket') -> None:
        pass
