
from typing import TYPE_CHECKING
from bpy.types import UIList
if TYPE_CHECKING:
    from bpy.types import UILayout
    from ..api.selection_item import RBFDriverSelectionItem

class RBFDRIVERS_UL_selection_list(UIList):
    bl_idname = "RBFDRIVERS_UL_selection_list"

    def draw_item(self, _0,
                  layout: 'UILayout', _1,
                  item: 'RBFDriverSelectionItem', _2, _3, _4) -> None:

        layout.prop(item, "name",
                    text="",
                    icon=item.icon,
                    emboss=False,
                    translate=False)

        layout.prop(item, "selected",
                    text="",
                    icon=f'CHECKBOX_{"" if item.selected else "DE"}HLT',
                    emboss=False)
