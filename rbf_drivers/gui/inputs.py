
from typing import TYPE_CHECKING, Optional
from bpy.types import Panel, UILayout, UIList
from .drivers import RBFDRIVERS_PT_drivers
from .utils import GUIUtils, idprop_data_render, layout_split
from ..ops.input import (RBFDRIVERS_OT_input_display_settings,
                         RBFDRIVERS_OT_input_add,
                         RBFDRIVERS_OT_input_remove,
                         RBFDRIVERS_OT_input_move)
if TYPE_CHECKING:
    from bpy.types import Context, PropertyGroup
    from ..api.input_target import RBFDriverInputTarget
    from ..api.input import RBFDriverInput
    from ..api.inputs import RBFDriverInputs


class GUIInputUtils(GUIUtils):

    @classmethod
    def draw_path(cls, layout: 'UILayout', input: 'RBFDriverInput') -> None:
        row = layout.row()
        sub = row.row(align=True)
        sub.alignment = 'LEFT'
        sub.alert = not not input.is_valid

        target = input.variables[0].targets[0]
        object = target.object

        if object is None:
            sub.label(icon='ERROR', text="Undefined")
            sub.label(icon='RIGHTARROW_THIN')
        else:
            sub.label(text=object.name, icon_value=cls.enum_icon(target, "id_type"))
            sub.label(icon='RIGHTARROW_THIN')
            if object and object.type == 'ARMATURE':
                name = target.bone_target
                if name:
                    icon = "ERROR" if name not in object.data.bones else "BONE_DATA"
                    sub.label(icon=icon, text=name)
                    sub.label(icon='RIGHTARROW_THIN')

        type = input.type
        if type == 'ROTATION':
            mode = input.rotation_mode
            text = f'{"Euler" if len(mode) < 5 else cls.enum_name(input, "rotation_mode")} Rotation'
        elif type == 'NONE':
            # TODO
            text = ""
        else:
            text = cls.enum_name(input, "type")

        sub.label(icon='RNA', text=text)
        row.row()


class RBFDRIVERS_PT_input_location_symmetry_settings(Panel):
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_input_location_symmetry_settings'
    bl_label = "Symmetry Settings"
    bl_options = {'INSTANCED'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.inputs.active is not None
                and object.rbf_drivers.active.inputs.active.type == 'LOCATION')

    def draw(self, context: 'Context') -> None:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        input = context.object.rbf_drivers.active.inputs.active
        for axis, variable in zip('XYZ', input.variables):
            row = layout.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text=f'{"Invert " if axis == "X" else ""}{axis}')
            row.prop(variable, "invert", text="")



class RBFDRIVERS_PT_inputs(GUIInputUtils, Panel):

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

    @classmethod
    def draw_transform_target(cls, layout: 'UILayout', context: 'Context', target: 'RBFDriverInputTarget') -> None:
        column = layout_split(layout, "Target", align=True)
        column.prop_search(target, "object", context.blend_data, "objects", text="", icon='OBJECT_DATA')

        object = target.object
        if object is not None and object.type == 'ARMATURE':
            row = column.row(align=True)
            row.alert = bool(target.bone_target) and target.bone_target not in object.data.bones
            column.prop_search(target, "bone_target", object.data, "bones", text="", icon='BONE_DATA')

        column.separator()

    def draw(self, context: 'Context') -> None:
        layout = self.subpanel()

        row = layout.row()
        row.operator_menu_enum(RBFDRIVERS_OT_input_add.bl_idname, "type",
                               text="Add Input",
                               icon='ADD')
        row.label(icon="BLANK1")

        for input in context.object.rbf_drivers.active.inputs:
            row = layout.row()
            col = row.column(align=True)
            self.draw_head(col.box(), input)

            ops = row.column(align=True)
            ops.scale_y = 0.85

            op = RBFDRIVERS_OT_input_move.bl_idname
            for dir in ('UP', 'DOWN'):
                props = ops.operator(op, text="", icon=f'TRIA_{dir}')
                props.direction = dir
                props.input = input.name

            if input.ui_open:
                box = col.box()
                box.separator()
                getattr(self, f'draw_{input.type.lower()}')(box, context, input)
                box.separator()

    @classmethod
    def draw_head(cls, layout: 'UILayout', input: 'RBFDriverInput') -> None:
        row = layout.row()
        row.scale_y = 1.25
        row.prop(input, "ui_open",
                 text="",
                 icon=f'DISCLOSURE_TRI_{"DOWN" if input.ui_open else "RIGHT"}',
                 emboss=False)

        sub = row.row(align=True)

        if input.ui_label == 'PATH':
            subrow = sub.row(align=True)
            subrow.scale_y = 0.6
            cls.draw_path(subrow.box(), input)
        else:
            sub.prop(input, "name", text="")

        subrow = sub.row(align=True)
        subrow.scale_x = 1.1
        subrow.prop(input, "ui_label", text="", icon_only=True)

        row.operator(RBFDRIVERS_OT_input_remove.bl_idname,
                     text="",
                     icon='X',
                     emboss=False).input=input.name

    def draw_location(self, layout: 'UILayout', context: 'Context', input: 'RBFDriverInput') -> None:
        layout = self.layout
        variables = input.variables
        self.draw_transform_target(layout, context, variables[0].targets[0])

        col, dec = layout_split(layout, "Location", decorate_fill=False)
        row = col.row(align=True)
        for axis, variable in zip("XYZ", variables):
            row.prop(variable, "is_enabled", text=axis, toggle=True)

        if input.has_symmetry_target:
            dec.popover(panel=RBFDRIVERS_PT_input_location_symmetry_settings.bl_idname,
                        icon='MOD_MIRROR',
                        text="")
        else:
            dec.label(icon='BLANK1')

        col.prop(variables[0].targets[0], "transform_space", text="")
        col.separator()

    def draw_location(self, context: 'Context', input: 'RBFDriverInput') -> None:
        layout = self.layout
        variables = input.variables
        self.draw_transform_target(layout, context, variables[0].targets[0])

        col, dec = layout_split(layout, "Location", decorate_fill=False)
        row = col.row(align=True)
        for axis, variable in zip("XYZ", variables):
            row.prop(variable, "is_enabled", text=axis, toggle=True)

        if input.has_symmetry_target:
            dec.popover(panel=RBFDRIVERS_PT_input_location_symmetry_settings.bl_idname,
                        icon='MOD_MIRROR',
                        text="")
        else:
            dec.label(icon='BLANK1')

        col.prop(variables[0].targets[0], "transform_space", text="")
        col.separator()

    @classmethod
    def draw_rotation(cls, layout: 'UILayout', context: 'Context', input: 'RBFDriverInput') -> None:
        cls.draw_transform_target(layout, context, input.variables[0].targets[0])

        column, decorations = layout_split(layout, "Rotation", decorate_fill=False)
        column.prop(input, "rotation_mode", text="")

        if input.has_symmetry_target:
            # TODO rotation symmetry settings
            decorations.label(icon='BLANK1')
            # dec.popover(panel=RBFDRIVERS_PT_input_location_symmetry_settings.bl_idname,
            #             icon='MOD_MIRROR',
            #             text="")
        else:
            decorations.label(icon='BLANK1')

        column.prop(input.variables[0].targets[0], "transform_space", text="")

        if len(input.rotation_mode) < 5:
            row = column.row(align=True)
            for variable in input.variables[1:]:
                row.prop(variable, "is_enabled", text=variable.name, toggle=True)

        column.separator()
            