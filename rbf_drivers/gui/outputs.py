
from typing import TYPE_CHECKING
from bpy.types import Panel, UILayout, UIList
from .drivers import RBFDRIVERS_PT_drivers
from .utils import GUIUtils, idprop_data_render, layout_split, transform_target_draw
from ..ops.output import (RBFDRIVERS_OT_output_display_settings,
                          RBFDRIVERS_OT_output_add,
                          RBFDRIVERS_OT_output_remove,
                          RBFDRIVERS_OT_output_move_up,
                          RBFDRIVERS_OT_output_move_down)
if TYPE_CHECKING:
    from bpy.types import Context
    from ..api.output_channel import RBFDriverOutputChannel
    from ..api.output import RBFDriverOutput
    from ..api.outputs import RBFDriverOutputs


class GUIOutputUtils(GUIUtils):

    @classmethod
    def draw_path(cls, layout: 'UILayout', output: 'RBFDriverOutput') -> None:
        row = layout.row()
        sub = row.row(align=True)
        sub.alignment = 'LEFT'
        sub.alert = not output.is_valid

        channel = output.channels[0]
        object = channel.object

        if object is None:
            sub.label(icon='ERROR', text="Undefined")
            sub.label(icon='RIGHTARROW_THIN')
        else:
            sub.label(text=object.name, icon_value=cls.enum_icon(channel, "id_type"))
            sub.label(icon='RIGHTARROW_THIN')
            if object and object.type == 'ARMATURE':
                name = channel.bone_target
                if name:
                    icon = "ERROR" if name not in object.data.bones else "BONE_DATA"
                    sub.label(icon=icon, text=name)
                    sub.label(icon='RIGHTARROW_THIN')

        type = output.type
        if type == 'ROTATION':
            mode = output.rotation_mode
            text = f'{"Euler" if len(mode) < 5 else cls.enum_name(output, "rotation_mode")} Rotation'
        elif type == 'NONE':
            # TODO
            text = ""
        else:
            text = cls.enum_name(input, "type")

        sub.label(icon='RNA', text=text)
        row.row()


class RBFDRIVERS_PT_output_location_symmetry_settings(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_output_location_symmetry_settings'
    bl_label = "Symmetry Settings"
    bl_options = {'INSTANCED'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.outputs.active is not None
                and object.rbf_drivers.active.outputs.active.type == 'LOCATION')

    def draw(self, context: 'Context') -> None:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        output = context.object.rbf_drivers.active.outputs.active
        for axis, channel in zip('XYZ', output.channels):
            row = layout.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text=f'{"Invert " if axis == "X" else ""}{axis}')
            row.prop(channel, "invert", text="")

class RBFDRIVERS_PT_output_rotation_settings(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_output_rotation_settings'
    bl_label = "Settings"
    bl_options = {'INSTANCED'}
    bl_ui_units_x = 16

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.outputs.active is not None
                and object.rbf_drivers.active.outputs.active.type == 'ROTATION')

    def draw(self, context: 'Context') -> None:
        layout = self.layout
        output: 'RBFDriverOutput' = context.object.rbf_drivers.active.outputs.active

        if output.rotation_mode == 'QUATERNION':
            layout.label(text="Averaging")
            labels, values = layout_split(layout, decorate=False)

            labels.label(text="Method")
            values.prop(output, "quaternion_interpolation_method", text="")

            if output.quaternion_interpolation_method == 'LOG':
                labels.label(text="Reference")
                values.prop(output, "quaternion_interpolation_reference", text="")


class RBFDRIVERS_PT_outputs(GUIOutputUtils, Panel):

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

    @classmethod
    def draw_transform_target(cls, layout: 'UILayout', context: 'Context', channel: 'RBFDriverOutputChannel') -> None:
        column = layout_split(layout, "Target", align=True)
        column.prop_search(channel, "object", context.blend_data, "objects", text="", icon='OBJECT_DATA')

        object = channel.object
        if object is not None and object.type == 'ARMATURE':
            row = column.row(align=True)
            row.alert = bool(channel.bone_target) and channel.bone_target not in object.data.bones
            column.prop_search(channel, "bone_target", object.data, "bones", text="", icon='BONE_DATA')

        column.separator()

    def draw(self, context: 'Context') -> None:
        layout = self.subpanel()

        row = layout.row()
        row.operator_menu_enum(RBFDRIVERS_OT_output_add.bl_idname, "type",
                               text="Add Output",
                               icon='ADD')
        row.label(icon='BLANK1')

        for output in context.object.rbf_drivers.active.outputs:
            row = layout.row()
            col = row.column(align=True)
            self.draw_head(col.box(), output)

        outputs: 'RBFDriverOutputs' = context.object.rbf_drivers.active.outputs
        layout = self.layout
        offset = layout.row()
        header = offset.row()
        offset.operator(RBFDRIVERS_OT_output_display_settings.bl_idname,
                        icon='PRESET',
                        text="",
                        emboss=False)

        split = header.split(factor=0.75)
        split.label(icon='BLANK1')

        row = split.row()

        subrow = row.row()
        subrow.alignment = 'CENTER'
        subrow.label(text=f'{"Influence" if outputs.display_influence else " "}')

        subrow = row.row()
        subrow.ui_units_x = 1.2
        subrow.prop(outputs, "mute",
                    text="",
                    icon=f'CHECKBOX_{"DE" if outputs.mute else ""}HLT',
                    emboss=False)

        row = layout.row()
        col = row.column()
        col.template_list(RBFDRIVERS_UL_outputs.bl_idname, "",
                          outputs, "collection__internal__",
                          outputs, "active_index")

        col = row.column(align=True)
        col.operator_menu_enum(RBFDRIVERS_OT_output_add.bl_idname, "type", text="", icon='ADD')
        col.operator(RBFDRIVERS_OT_output_remove.bl_idname, text="", icon='REMOVE')
        col.separator()
        col.operator(RBFDRIVERS_OT_output_move_up.bl_idname, text="", icon='TRIA_UP')
        col.operator(RBFDRIVERS_OT_output_move_down.bl_idname, text="", icon='TRIA_DOWN')

        output: 'RBFDriverOutput' = outputs.active
        if output:
            layout.separator(factor=0.5)

            col = layout_split(layout, "Influence")
            idprop_data_render(col, output.influence, text="", slider=True)

            row = col.row()
            row.alignment = 'RIGHT'
            row.label(text="Active Driver")
            row.prop(output, "mute", text="", invert_checkbox=True)

            layout.separator(factor=0.5)

            type = output.type
            if   type == 'LOCATION' : self.draw_location(context, output)
            elif type == 'ROTATION' : self.draw_rotation(context, output)
            
            layout.separator()

    @classmethod
    def draw_head(cls, layout: 'UILayout', output: 'RBFDriverInput') -> None:
        row = layout.row()
        row.scale_y = 1.25
        row.prop(outpout, "ui_open",
                 text="",
                 icon=f'DISCLOSURE_TRI_{"DOWN" if output.ui_open else "RIGHT"}',
                 emboss=False)

        sub = row.row(align=True)

        if outpout.ui_label == 'PATH':
            subrow = sub.row(align=True)
            subrow.scale_y = 0.6
            cls.draw_path(subrow.box(), outpout)
        else:
            sub.prop(outpout, "name", text="")

        subrow = sub.row(align=True)
        subrow.scale_x = 1.1
        subrow.prop(outpout, "ui_label", text="", icon_only=True)

        row.operator(RBFDRIVERS_OT_output_remove.bl_idname,
                     text="",
                     icon='X',
                     emboss=False).input=outpout.name


    def draw_location(self, context: 'Context', output: 'RBFDriverOutput') -> None:
        layout = self.layout
        channels = output.channels
        self.draw_transform_target(context, channels[0])

        col, dec = layout_split(layout, "Location", decorate_fill=False)
        row = col.row(align=True)
        for axis, channel in zip("XYZ", channels):
            row.prop(channel, "is_enabled", text=axis, toggle=True)

        if output.has_symmetry_target:
            dec.popover(panel=RBFDRIVERS_PT_output_location_symmetry_settings.bl_idname,
                        icon='MOD_MIRROR',
                        text="")
        else:
            dec.label(icon='BLANK1')

        col.separator()

    def draw_rotation(self, context: 'Context', output: 'RBFDriverOutput') -> None:
        layout = self.layout
        transform_target_draw(layout, context, output.channels[0])

        column, decorations = layout_split(layout, "Rotation", decorate_fill=False)
        column.prop(output, "rotation_mode", text="")

        if output.has_symmetry_target:
            decorations.popover(RBFDRIVERS_PT_output_rotation_settings.bl_idname, icon='MOD_MIRROR')
        else:
            decorations.label(icon='BLANK1')

        if output.rotation_mode == 'QUATERNION':
            row = column.row()
            row.alignment = 'RIGHT'
            row.label(text="Use Logarithmic Map")
            row.prop(output, "use_logarithmic_map", text="")
        else:
            row = column.row(align=True)
            channels = output.channels[1:] if output.rotation_mode == 'EULER' else output.channels
            for channel in channels:
                row.prop(channel, "is_enabled", text=channel.name, toggle=True)
