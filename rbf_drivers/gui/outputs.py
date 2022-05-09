
from typing import TYPE_CHECKING
from bpy.types import Panel, UILayout, UIList
from .drivers import RBFDRIVERS_PT_drivers
from .utils import GUILayerUtils, idprop_data_render
from ..api.output import OUTPUT_TYPE_ICONS
from ..ops.output import (RBFDRIVERS_OT_output_add,
                          RBFDRIVERS_OT_output_remove,
                          RBFDRIVERS_OT_output_move_up,
                          RBFDRIVERS_OT_output_move_down)
if TYPE_CHECKING:
    from bpy.types import Context
    from ..api.output import RBFDriverOutput


class RBFDRIVERS_UL_outputs(UIList):
    bl_idname = 'RBFDRIVERS_UL_outputs'

    def draw_item(self, _0, layout: UILayout, _1, output: 'RBFDriverOutput', _2, _3, _4) -> None:

        if output.type == 'SHAPE_KEY':
            layout.label(icon='SHAPEKEY_DATA', text=output.name)
        else:
            layout.prop(output, "name",
                        text="",
                        icon=OUTPUT_TYPE_ICONS[output.type],
                        emboss=False,
                        translate=False)

        layout.prop(output, "mute",
                    text="",
                    icon=f'CHECKBOX_{"DE" if output.mute else ""}HLT',
                    emboss=False)


class RBFDRIVERS_PT_outputs(GUILayerUtils, Panel):

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_outputs'
    bl_parent_id = RBFDRIVERS_PT_drivers.bl_idname
    bl_description = "RBF driver outputs"
    bl_label = "Outputs"

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None)

    def draw(self, context: 'Context') -> None:
        layout = self.subpanel(self.layout)
        driver = context.object.rbf_drivers.active
        outputs = driver.outputs

        if len(outputs):
            row = layout.row()
            row.scale_y = 0.6
            row.alignment = 'RIGHT'
            row.label(text="Active:")
            row.prop(outputs, "mute",
                     text="",
                     icon=f'CHECKBOX_{"DE" if outputs.mute else ""}HLT',
                     emboss=False)
            row.separator(factor=4.2)
        
        row = layout.row()
        column = row.column()
        column.template_list(RBFDRIVERS_UL_outputs.bl_idname, "",
                             outputs, "collection__internal__",
                             outputs, "active_index")

        column = row.column(align=True)

        if driver.type == 'SHAPE_KEY':
            subcolumn = column.column(align=True)
            subcolumn.operator_context = 'INVOKE_DEFAULT'
            subcolumn.operator(RBFDRIVERS_OT_output_add.bl_idname, text="", icon='ADD')
        else:
            column.operator_menu_enum(RBFDRIVERS_OT_output_add.bl_idname, "type", text="", icon='ADD')
        column.operator(RBFDRIVERS_OT_output_remove.bl_idname, text="", icon='REMOVE')
        column.separator()
        column.operator(RBFDRIVERS_OT_output_move_up.bl_idname, text="", icon='TRIA_UP')
        column.operator(RBFDRIVERS_OT_output_move_down.bl_idname, text="", icon='TRIA_DOWN')

        output: 'RBFDriverOutput' = outputs.active
        if output is not None:
            layout.separator()
            
            column = self.split_layout(layout, "Active")
            row = column.row()
            row.prop(output, "mute",
                     text="",
                     icon=f'CHECKBOX_{"DE" if output.mute else ""}HLT',
                     toggle=True,
                     emboss=False,
                     invert_checkbox=True)

            subrow = row.row()
            subrow.enabled = not output.mute
            idprop_data_render(subrow, output.influence, text="Influence", slider=True)

            column.separator()
            if driver.type == 'SHAPE_KEY':
                column = self.split_layout(layout, "Target")

                # If the output object has been changed through the python API
                # or doesn't match because the object has been duplicated then
                # expose it in the UI.
                if output.object != output.id_data:
                    column.prop(output, "object", text="", icon='OBJECT_DATA')

                key = output.id
                row = column.row()

                if key:
                    row.alert = output.name not in key.key_blocks
                    row.prop_search(output, "name", key, "key_blocks", text="", icon='SHAPEKEY_DATA')
                else:
                    row.alert = True
                    column.prop(output, "name", text="", icon='SHAPEKEY_DATA')
            else:
                getattr(self, f'draw_{output.type.lower()}')(layout, context, output)

            layout.separator()

    def draw_location(self, layout: 'UILayout', context: 'Context', output: 'RBFDriverOutput') -> None:
        self.draw_transform_target(layout, context, output)
        layout.separator(factor=0.5)

        column, decorations = self.split_layout(layout, "Channels", decorate_fill=False)

        if output.has_symmetry_target:
            decorations.prop(output, "use_mirror_x", text="", icon='MOD_MIRROR', toggle=True)
        else:
            decorations.label(icon='BLANK1')

        row = column.row(align=True)
        row.prop(output, "use_x", text="X", toggle=True)
        row.prop(output, "use_y", text="Y", toggle=True)
        row.prop(output, "use_z", text="Z", toggle=True)

    def draw_rotation(self, layout: 'UILayout', context: 'Context', output: 'RBFDriverOutput') -> None:
        self.draw_transform_target(layout, context, output)
        layout.separator(factor=0.5)
        column, decorations = self.split_layout(layout, "Channels", decorate_fill=False)
        column.prop(output, "rotation_mode", text="")

        if output.has_symmetry_target:
            decorations.prop(output, "use_mirror_x", text="", icon='MOD_MIRROR', toggle=True)
        else:
            decorations.label(icon='BLANK1')

        if output.rotation_mode == 'QUATERNION':
            row = column.row()
            row.alignment = 'RIGHT'
            row.label(text="Use Logarithmic Map:")
            row.prop(output, "use_logarithmic_map", text="")
        elif output.rotation_mode == 'EULER':
            row = column.row(align=True)
            row.prop(output, "use_x", text="X", toggle=True)
            row.prop(output, "use_y", text="Y", toggle=True)
            row.prop(output, "use_z", text="Z", toggle=True)

    def draw_scale(self, layout: 'UILayout', context: 'Context', output: 'RBFDriverOutput') -> None:
        self.draw_transform_target(layout, context, output)
        layout.separator(factor=0.5)

        column = self.split_layout(layout, "Channels")
        row = column.row(align=True)
        row.prop(output, "use_x", text="X", toggle=True)
        row.prop(output, "use_y", text="Y", toggle=True)
        row.prop(output, "use_z", text="Z", toggle=True)

    def draw_shape_key(self, layout: 'UILayout', context: 'Context', output: 'RBFDriverOutput') -> None:
        column = self.split_layout(layout, "Target")
        column.prop_search(output, "object", context.blend_data, "objects", text="", icon='OBJECT_DATA')

        key = output.id
        row = column.row()
        if key:
            channel = output.channels[0]
            row.alert = channel.name not in key.key_blocks
            row.prop_search(channel, "name", key, "key_blocks", text="", icon='SHAPEKEY_DATA')
        else:
            row.alert = True
            column.prop(output.channels[0], "name", text="", icon='SHAPEKEY_DATA')

    def draw_single_prop(self, layout: 'UILayout', context: 'Context', output: 'RBFDriverOutput') -> None:
        row = self.split_layout(layout, "Data").row(align=True)
        row.prop(output, "id_type", text="", icon_only=True)
        column = row.column(align=True)
        column.prop_search(output, "object", context.blend_data, "objects", text="", icon='NONE')
        column.prop(output, "data_path", text="", icon='RNA')
        