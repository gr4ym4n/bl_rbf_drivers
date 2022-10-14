
from typing import TYPE_CHECKING
from bpy.types import Menu, Panel, UIList
from .drivers import RBFDRIVERS_PT_drivers
from .utils import GUILayerUtils
from ..api.input import INPUT_TYPE_ICONS
from ..ops.input import (RBFDRIVERS_OT_input_add, RBFDRIVERS_OT_input_decompose,
                         RBFDRIVERS_OT_input_remove,
                         RBFDRIVERS_OT_input_move_up,
                         RBFDRIVERS_OT_input_move_down,
                         RBFDRIVERS_OT_input_variable_add,
                         RBFDRIVERS_OT_input_variable_remove)
if TYPE_CHECKING:
    from bpy.types import Context, UILayout
    from ..api.input_variables import InputVariable
    from ..api.input import Input


class RBFDRIVERS_UL_inputs(UIList):
    bl_idname = 'RBFDRIVERS_UL_inputs'

    def draw_item(self, _0,
                  layout: 'UILayout', _1,
                  input: 'Input', _2, _3, _4) -> None:

        layout.prop(input, "name",
                    text="",
                    icon=INPUT_TYPE_ICONS[input.type],
                    emboss=False,
                    translate=False)


class RBFDRIVERS_MT_input_context_menu(Menu):
    bl_label = "Input Specials Menu"
    bl_idname = 'RBFDRIVERS_MT_input_context_menu'

    def draw(self, _: 'Context') -> None:
        layout = self.layout
        layout.operator(RBFDRIVERS_OT_input_decompose.bl_idname,
                        icon='RNA',
                        text="Decompose input variables")


class RBFDRIVERS_PT_inputs(GUILayerUtils, Panel):

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_inputs'
    bl_parent_id = RBFDRIVERS_PT_drivers.bl_idname
    bl_description = "RBF driver inputs"
    bl_label = "Inputs"

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None)

    def draw_header(self, context: 'Context') -> None:
        layout = self.layout
        inputs = context.object.rbf_drivers.active.inputs
        if len(inputs) == 0 or not any(input.is_valid for input in inputs):
            layout.label(icon='ERROR')
        elif not any(input.is_enabled for input in inputs):
            layout.label(icon='RADIOBUT_OFF')
        else:
            layout.label(icon='RADIOBUT_ON')

    def draw(self, context: 'Context') -> None:
        layout = self.subpanel(self.layout)
        inputs = context.object.rbf_drivers.active.inputs

        layout.separator(factor=0.5)

        row = layout.row()
        column = row.column()
        column.template_list(RBFDRIVERS_UL_inputs.bl_idname, "",
                             inputs, "internal__",
                             inputs, "active_index")

        column = row.column(align=True)
        column.operator_menu_enum(RBFDRIVERS_OT_input_add.bl_idname, "type", text="", icon='ADD')
        column.operator(RBFDRIVERS_OT_input_remove.bl_idname, text="", icon='REMOVE')
        column.separator()
        column.menu(RBFDRIVERS_MT_input_context_menu.bl_idname, text="", icon='DOWNARROW_HLT')
        column.separator()
        column.operator(RBFDRIVERS_OT_input_move_up.bl_idname, text="", icon='TRIA_UP')
        column.operator(RBFDRIVERS_OT_input_move_down.bl_idname, text="", icon='TRIA_DOWN')

        input = inputs.active

        if input is not None:
            layout.separator()
            getattr(self, f'draw_{input.type.lower()}')(layout, context, input)

            if input.type == 'USER_DEF':
                layout.separator()
                self.draw_variables(layout, context)

    def draw_location(self, layout: 'UILayout', context: 'Context', input: 'Input') -> None:
        self.draw_transform_target(layout, context, input)

        layout.separator(factor=0.5)

        column, decorations = self.split_layout(layout, "Channels", decorate_fill=False)
        column.prop(input, "transform_space", text="")

        if input.has_symmetry_target:
            decorations.prop(input, "use_mirror_x", text="", icon='MOD_MIRROR', toggle=True)
        else:
            decorations.label(icon='BLANK1')

        row = column.row(align=True)
        for variable in input.variables:
            row.prop(variable, "is_enabled", text=variable.name, toggle=True)

    def draw_rotation(self, layout: 'UILayout', context: 'Context', input: 'Input') -> None:
        self.draw_transform_target(layout, context, input)
        layout.separator(factor=0.5)
        column, decorations = self.split_layout(layout, "Channels", decorate_fill=False)

        row = column.row()
        row.prop(input, "rotation_mode", text="")

        if input.has_symmetry_target:
            decorations.prop(input, "use_mirror_x", text="", icon='MOD_MIRROR', toggle=True)
        else:
            decorations.label(icon='BLANK1')

        mode = input.rotation_mode
        if mode == 'EULER':
            subrow = row.row()
            subrow.alignment = 'RIGHT'
            subrow.prop(input, "rotation_order", text="")
        elif mode in {'SWING', 'TWIST'}:
            subrow = row.row()
            subrow.alignment = 'RIGHT'
            subrow.prop(input, "rotation_axis", text="")

        column.prop(input, "transform_space", text="")

        if mode == 'EULER':
            subrow = column.row(align=True)
            for variable in input.variables[1:]:
                subrow.prop(variable, "is_enabled", text=variable.name, toggle=True)

    def draw_scale(self, layout: 'UILayout', context: 'Context', input: 'Input') -> None:
        self.draw_transform_target(layout, context, input)

        layout.separator(factor=0.5)

        column = self.split_layout(layout, "Channels")
        column.prop(input, "transform_space", text="")

        row = column.row(align=True)
        for variable in input.variables:
            row.prop(variable, "is_enabled", text=variable.name, toggle=True)

    def draw_rotation_diff(self, layout: 'UILayout', context: 'Context', input: 'Input') -> None:
        for suffix, target in zip("AB", input.variables[0].targets):
            self.draw_transform_target(layout, context, target, f'Target {suffix}')
            if suffix == 'A':
                layout.separator(factor=0.5)

    def draw_loc_diff(self, layout: 'UILayout', context: 'Context', input: 'Input') -> None:
        for suffix, target in zip("AB", input.variables[0].targets):
            self.draw_transform_target(layout, context, target, f'Target {suffix}')
            self.split_layout(layout, " ").prop(target, "transform_space", text="")
            if suffix == 'A':
                layout.separator(factor=0.5)

    def draw_shape_key(self, layout: 'UILayout', context: 'Context', input: 'Input') -> None:
        labels, values, decorations = self.split_layout(layout, decorate_fill=False)

        labels.label(text="Object")
        values.prop_search(input, "object", context.blend_data, "objects", text="", icon='OBJECT_DATA')
        decorations.label(icon='BLANK1')

        labels.separator()
        values.separator()
        decorations.separator()

        labels.label(text="Shapes")
        values.operator_context = 'INVOKE_DEFAULT'
        values.operator(RBFDRIVERS_OT_input_variable_add.bl_idname, text="Add Shape Keys", icon='ADD')
        decorations.label(icon='BLANK1')

        try:
            key = input.object.data.shape_keys
        except:
            key = None

        for index, variable in enumerate(input.variables):
            row = values.row(align=True)
            subrow = row.row(align=True)
            if key is None:
                subrow.alert = True
                subrow.prop(variable, "name", text="", icon='SHAPEKEY_DATA')
            else:
                subrow.alert = variable.name not in key.key_blocks
                subrow.prop_search(variable, "name", key, "key_blocks", text="", icon='SHAPEKEY_DATA')
            row.operator(RBFDRIVERS_OT_input_variable_remove.bl_idname, text="", icon='X').index = index
            decorations.prop(variable, "is_enabled", text="")

    def draw_user_def(self, layout: 'UILayout', context: 'Context', input: 'Input') -> None:
        labels, values, decorations = self.split_layout(layout, decorate_fill=False)

        labels.label(text="Type")
        values.prop(input, "data_type", text="")

        if input.data_type == 'QUATERNION' and len(input.variables) == 4:
            row = values.row()
            row.alignment = 'RIGHT'
            row.label(text="Extract Swing Rotation:")

            subrow = row.row()
            subrow.alignment = 'RIGHT'
            subrow.enabled = input.use_swing
            subrow.prop(input, "rotation_axis", text="")

            decorations.label(icon='BLANK1')
            decorations.prop(input, "use_swing", text="")
        else:
            decorations.label(icon='BLANK1')

    def draw_variables(self, layout: 'UILayout', context: 'Context') -> None:
        column = self.split_layout(layout, "Variables")
        column.operator(RBFDRIVERS_OT_input_variable_add.bl_idname, text="Add Input Variable", icon='ADD')

        for index, variable in enumerate(context.object.rbf_drivers.active.inputs.active.variables):
            column, decorations = self.split_layout(layout, " ", align=True, decorate_fill=False)

            row = column.box().row()
            row.prop(variable, "ui_expand",
                 text="",
                 icon=f'DISCLOSURE_TRI_{"DOWN" if variable.ui_expand else "RIGHT"}',
                 emboss=False)

            subrow = row.row(align=True)
            subrow.prop(variable, "type", text="", icon_only=True)
            subrow.prop(variable, "name", text="", translate=False)

            subrow = row.row()
            subrow.operator(RBFDRIVERS_OT_input_variable_remove.bl_idname,
                            text="",
                            icon='X',
                            emboss=False).index=index

            decorations.separator(factor=0.85)
            decorations.prop(variable, "is_enabled", text="")

            if variable.ui_expand:
                row = column.box().row()
                row.label(icon='BLANK1')

                self.draw_variable_detail(row.column(), context, variable)

                row = column.box().row()
                row.label(icon='BLANK1')

                val = self.split_layout(row, "Value:", alignment='LEFT')
                val.label(text=f'{variable.value:.3f}')

    def draw_variable_detail(self,
                             layout: 'UILayout',
                             context: 'Context',
                             variable: 'InputVariable') -> None:

        if variable.type == 'TRANSFORMS':
            target = variable.targets[0]
            self.draw_transform_target(layout, context, target, "Target:", alignment='LEFT')

            layout.separator()

            values = self.split_layout(layout, "Channel:", align=True, alignment='LEFT')

            values.prop(target, "transform_type", text="")

            if target.transform_type.startswith('ROT'):
                values.prop(target, "rotation_mode", text="")

            values.prop(target, "transform_space", text="")

        elif variable.type == 'SINGLE_PROP':
            target = variable.targets[0]
            row = self.split_layout(layout, "Data:", alignment='LEFT').row(align=True)
            row.prop(target, "id_type", text="", icon_only=True)

            column = row.column(align=True)
            column.prop_search(target, "object", context.blend_data, "objects", text="", icon='NONE')
            column.prop(target, "data_path", text="", icon='RNA')

        else:
            for suffix, target in zip("AB", variable.targets):
                self.draw_transform_target(layout, context, target, f'Target {suffix}:', alignment='LEFT')
                if variable.type == 'LOC_DIFF':
                    column = self.split_layout(layout, " ", alignment='LEFT')
                    column.prop(target, "transform_space", text="")
                if suffix == "A":
                    layout.separator()
