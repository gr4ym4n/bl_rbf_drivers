
from bpy.types import UILayout, UIList
from ..api.driver import RBFDriver

class RBFDRIVER_UL_drivers(UIList):
    def draw_item(self, _0, layout: UILayout, _1, rbf_driver: RBFDriver, _2, _3, _4) -> None:
        layout.prop(rbf_driver, "name",
                    icon_value=UILayout.enum_item_icon(rbf_driver, "type", rbf_driver.type),
                    text="",
                    emboss=False,
                    translate=False)

        if rbf_driver.has_symmetry_target:
            mirror = rbf_driver.id_data.rbf_drivers.search(rbf_driver.symmetry_identifier)
            if mirror is not None:
                row = layout.row()
                row.alignment = 'RIGHT'
                row.label(icon='MOD_MIRROR', text=mirror.name)

