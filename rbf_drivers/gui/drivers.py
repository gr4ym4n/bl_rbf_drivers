
from typing import TYPE_CHECKING
from bpy.types import Panel, UILayout, UIList
from .utils import layout_split
from ..lib.curve_mapping import draw_curve_manager_ui
from ..api.driver import RBFDriver
from ..ops.driver import (RBFDRIVERS_OT_new,
                          RBFDRIVERS_OT_remove,
                          RBFDRIVERS_OT_move_up,
                          RBFDRIVERS_OT_move_down)
if TYPE_CHECKING:
    from bpy.types import Context

class RBFDRIVERS_UL_drivers(UIList):
    bl_idname = 'RBFDRIVERS_UL_drivers'

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


class RBFDRIVERS_PT_drivers(Panel):

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_drivers'
    bl_description = "Radial based function drivers"
    bl_label = "RBF Drivers"

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        return context.object is not None

    def draw(self, context: 'Context') -> None:
        object = context.object
        layout = self.layout
        if not object.is_property_set("rbf_drivers") or len(object.rbf_drivers) == 0:
            layout.operator_menu_enum(RBFDRIVERS_OT_new.bl_idname, "type", text="Add", icon='ADD')
        else:
            drivers = object.rbf_drivers
            row = layout.row()
            col = row.column()
            col.template_list(RBFDRIVERS_UL_drivers.bl_idname, "",
                              drivers, "collection__internal__", drivers, "active_index")
            
            col = row.column(align=True)
            col.operator_menu_enum(RBFDRIVERS_OT_new.bl_idname, "type", text="", icon='ADD')
            col.operator(RBFDRIVERS_OT_remove.bl_idname, text="", icon='REMOVE')
            col.separator()
            col.operator(RBFDRIVERS_OT_move_up.bl_idname, text="", icon='TRIA_UP')
            col.operator(RBFDRIVERS_OT_move_down.bl_idname, text="", icon='TRIA_DOWN')


# class RBFDRIVERS_PT_interpolation(Panel):

#     bl_space_type = 'PROPERTIES'
#     bl_region_type = 'WINDOW'
#     bl_context = 'object'
#     bl_idname = 'RBFDRIVERS_PT_interpolation'
#     bl_parent_id = RBFDRIVERS_PT_drivers.bl_idname
#     bl_description = "RBF driver interpolation"
#     bl_label = "Interpolation"

#     @classmethod
#     def poll(cls, context: 'Context') -> bool:
#         object = context.object
#         return (object is not None
#                 and object.is_property_set("rbf_drivers")
#                 and object.rbf_drivers.active is not None)

#     def draw(self, context: 'Context') -> None:
#         layout = self.layout
#         driver = context.object.rbf_drivers.active
#         draw_curve_manager_ui(layout, driver.interpolation)
