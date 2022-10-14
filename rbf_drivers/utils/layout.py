
from typing import Iterable, Optional, Tuple, Union, TYPE_CHECKING
if TYPE_CHECKING:
    from bpy.types import Node

X = Union[int, float]
Y = X
XY = Tuple[X, Y]
X_Y = Union[X, XY]


Center = Union[int, float, Tuple[Union[int, float]]]


def layout_nodes_column(nodes: Iterable['Node'],
                        center: Optional[X_Y]=0.,
                        spacing: Optional[Y]=80.) -> None:
    if isinstance(center, (int, float)):
        center = (center, 0.)

    def key(node):
        return node.location.y - (node.height / 2)
    nodes = sorted(list(nodes), key=key, reverse=True)

    offset = 0
    for node in nodes:
        node.location.x = center[0] - (node.width / 2)
        node.location.y = offset
        offset -= (spacing + node.height)

    offset = center[1] + (offset + spacing) / -2
    for node in nodes:
        node.location.y += offset


def layout_nodes_columns(nodes: Iterable[Iterable['Node']],
                         center: Optional[X_Y]=0.0,
                         spacing: Optional[X_Y]=80.) -> None:
    if isinstance(center, (int, float)):
        center = (center, 0.)

    if isinstance(spacing, (int, float)):
        spacing = (spacing, spacing)

    cols = [list(col) for col in nodes]
    for col in cols:
        layout_nodes_column(col, center, spacing[1])

    offset = spacing[0] + max([n.width for n in cols[0]], default=0.) / 2
    for col in cols[1:]:
        width = max([n.width for n in col], default=0.)
        for node in col:
            node.location.x += offset + width / 2
        offset += spacing[0] + width

    
