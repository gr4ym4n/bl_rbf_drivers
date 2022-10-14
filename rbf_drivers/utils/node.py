

from typing import Iterator, TYPE_CHECKING, List, Optional
if TYPE_CHECKING:
    from bpy.types import Node, NodeTree


def iternodes(tree: 'NodeTree', idname: str) -> Iterator['Node']:
    for node in tree.nodes:
        if node.bl_idname == idname:
            yield node


def listnodes(tree: 'NodeTree', idname: str) -> List['Node']:
    return list(iternodes(tree, idname))


def findnode(tree: 'NodeTree', idname: str) -> Optional['Node']:
    return next(iternodes(tree, idname), None)
