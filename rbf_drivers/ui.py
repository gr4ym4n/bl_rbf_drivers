
import typing
import bpy
from rbf_drivers.driver import RBFDriver
from rbf_drivers.output import RBFDriverOutput, RBFDriverOutputChannel
from rbf_drivers.posedata import ActivePoseData
from .lib.curve_mapping import draw_curve_manager_ui
from .input import RBFDriverInput, RBFDriverInputTarget, RBFDriverInputVariable

from .ops import (RBFDRIVERS_OT_input_move_down,
                  RBFDRIVERS_OT_input_move_up,
                  RBFDRIVERS_OT_input_remove,
                  RBFDRIVERS_OT_move_down,
                  RBFDRIVERS_OT_move_up,
                  RBFDRIVERS_OT_new,
                  RBFDRIVERS_OT_input_add,
                  RBFDRIVERS_OT_output_add,
                  RBFDRIVERS_OT_output_move_down,
                  RBFDRIVERS_OT_output_move_up,
                  RBFDRIVERS_OT_output_remove,
                  RBFDRIVERS_OT_pose_add,
                  RBFDRIVERS_OT_pose_move_down,
                  RBFDRIVERS_OT_pose_move_up,
                  RBFDRIVERS_OT_pose_remove,
                  RBFDRIVERS_OT_pose_update,
                  RBFDRIVERS_OT_remove)

def layout_split(layout: bpy.types.UILayout,
                 label: typing.Optional[str]="",
                 align: typing.Optional[bool]=False,
                 factor: typing.Optional[float]=0.25,
                 decorate: typing.Optional[bool]=True,
                 decorate_fill: typing.Optional[bool]=True
                 ) -> typing.Union[bpy.types.UILayout, typing.Tuple[bpy.types.UILayout, ...]]:
    split = layout.row().split(factor=factor)
    col_a = split.column(align=align)
    col_a.alignment = 'RIGHT'
    if label:
        col_a.label(text=label)
    row = split.row()
    col_b = row.column(align=align)
    if decorate:
        col_c = row.column(align=align)
        if decorate_fill:
            col_c.label(icon='BLANK1')
        else:
            return (col_b, col_c) if label else (col_a, col_b, col_c)
    return col_b if label else (col_a, col_b)


class RBFDRIVERS_UL_drivers(bpy.types.UIList):
    bl_idname = 'RBFDRIVERS_UL_drivers'

    def draw_item(self, context, layout, data, item: RBFDriver, icon, active_data, active_prop) -> None:
        layout.prop(item, "name",
                    icon_value=bpy.types.UILayout.enum_item_icon(item, "type", item.type),
                    text="",
                    emboss=False,
                    translate=False)
        
        if item.has_symmetry_target:
            mirror = item.id_data.rbf_drivers.search(item.symmetry_identifier)
            if mirror is not None:
                row = layout.row()
                row.alignment = 'RIGHT'
                row.label(icon='MOD_MIRROR', text=mirror.name)


class RBFDRIVERS_PT_drivers(bpy.types.Panel):

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_drivers'
    bl_description = "Radial based function drivers"
    bl_label = "RBF Drivers"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return context.object is not None

    def draw(self, context: bpy.types.Context) -> None:
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


class RBFDRIVERS_PT_interpolation(bpy.types.Panel):

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_interpolation'
    bl_parent_id = RBFDRIVERS_PT_drivers.bl_idname
    bl_description = "RBF driver interpolation"
    bl_label = "Interpolation"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None)

    def draw(self, context: bpy.types.Context) -> None:
        driver = context.object.rbf_drivers.active
        col = layout_split(self.layout, "Falloff", decorate=False)
        draw_curve_manager_ui(col, driver.falloff)
        row = col.row()
        row.prop(driver.falloff, "radius", text="Radius")
        row.label(icon='BLANK1')


class RBFDRIVERS_UL_inputs(bpy.types.UIList):
    bl_idname = 'RBFDRIVERS_UL_inputs'

    def draw_item(self, context, layout, data, item, icon, active_data, active_prop) -> None:
        layout.prop(item, "name", text="", emboss=False, translate=False)
        row = layout.row(align=True)
        row.alignment = 'RIGHT'
        row.prop(item.id_data.data, item.influence_property_path, text="", slider=True)


class RBFDRIVERS_PT_input_location_symmetry_settings(bpy.types.Panel):
    
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_input_location_symmetry_settings'
    bl_label = "Symmetry Settings"
    bl_options = {'INSTANCED'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.inputs.active is not None
                and object.rbf_drivers.active.inputs.active.type == 'LOCATION')

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        input = context.object.rbf_drivers.active.inputs.active
        for axis, variable in zip('XYZ', input.variables):
            row = layout.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text=f'{"Invert " if axis == "X" else ""}{axis}')
            row.prop(variable, "invert", text="")


class RBFDRIVERS_PT_input_rotation_symmetry_settings(bpy.types.Panel):
    
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_input_rotation_symmetry_settings'
    bl_label = "Symmetry Settings"
    bl_options = {'INSTANCED'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.inputs.active is not None
                and object.rbf_drivers.active.inputs.active.type == 'ROTATION')

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        input = context.object.rbf_drivers.active.inputs.active

        mode = input.rotation_mode
        if input.rotation_mode.startswith('TWIST'):
            row = layout.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text=f'Invert {mode[-1]}')
            row.prop(input.variables['WXYZ'.index(mode[-1])], "invert", text="")
        else:
            for axis, variable in zip('XYZ', input.variables[1:]):
                row = layout.row(align=True)
                row.alignment = 'RIGHT'
                row.label(text=f'{"Invert " if axis == "X" else ""}{axis}')
                row.prop(variable, "invert", text="")


class RBFDRIVERS_PT_input_scale_symmetry_settings(bpy.types.Panel):
    
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_input_scale_symmetry_settings'
    bl_label = "Symmetry Settings"
    bl_options = {'INSTANCED'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.inputs.active is not None
                and object.rbf_drivers.active.inputs.active.type == 'SCALE')

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        input = context.object.rbf_drivers.active.inputs.active
        for axis, variable in zip('XYZ', input.variables):
            row = layout.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text=f'{"Invert " if axis == "X" else ""}{axis}')
            row.prop(variable, "invert", text="")


class RBFDRIVERS_PT_input_bbone_curvein_symmetry_settings(bpy.types.Panel):
    
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_input_bbone_curvein_symmetry_settings'
    bl_label = "Symmetry Settings"
    bl_options = {'INSTANCED'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.inputs.active is not None
                and object.rbf_drivers.active.inputs.active.type == 'BBONE')

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        input = context.object.rbf_drivers.active.inputs.active
        for axis in "XZ":
            row = layout.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text=f'{"Invert " if axis == "X" else ""}{axis}')
            row.prop(input.variables[f'curvein{axis.lower()}'], "invert", text="")


class RBFDRIVERS_PT_input_bbone_curveout_symmetry_settings(bpy.types.Panel):
    
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_input_bbone_curveout_symmetry_settings'
    bl_label = "Symmetry Settings"
    bl_options = {'INSTANCED'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.inputs.active is not None
                and object.rbf_drivers.active.inputs.active.type == 'BBONE')

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        input = context.object.rbf_drivers.active.inputs.active
        for axis in "XZ":
            row = layout.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text=f'{"Invert " if axis == "X" else ""}{axis}')
            row.prop(input.variables[f'curveout{axis.lower()}'], "invert", text="")


class RBFDRIVERS_PT_input_bbone_roll_symmetry_settings(bpy.types.Panel):
    
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_input_bbone_roll_symmetry_settings'
    bl_label = "Symmetry Settings"
    bl_options = {'INSTANCED'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.inputs.active is not None
                and object.rbf_drivers.active.inputs.active.type == 'BBONE')

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        input = context.object.rbf_drivers.active.inputs.active
        for direction in ('IN', 'OUT'):
            row = layout.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text=f'{"Invert " if direction == "IN" else ""}{direction.title()}')
            row.prop(input.variables[f'roll{direction.lower()}'], "invert", text="")


class RBFDRIVERS_PT_inputs(bpy.types.Panel):

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_inputs'
    bl_parent_id = RBFDRIVERS_PT_drivers.bl_idname
    bl_description = "RBF driver inputs"
    bl_label = "Inputs"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None)

    def draw(self, context: bpy.types.Context) -> None:
        object = context.object
        layout = self.layout
        inputs = object.rbf_drivers.active.inputs

        row = layout.row()
        col = row.column()
        col.template_list(RBFDRIVERS_UL_inputs.bl_idname, "",
                          inputs, "collection__internal__", inputs, "active_index")
        
        col = row.column(align=True)
        col.operator_menu_enum(RBFDRIVERS_OT_input_add.bl_idname, "type", text="", icon='ADD')
        col.operator(RBFDRIVERS_OT_input_remove.bl_idname, text="", icon='REMOVE')
        col.separator()
        col.operator(RBFDRIVERS_OT_input_move_up.bl_idname, text="", icon='TRIA_UP')
        col.operator(RBFDRIVERS_OT_input_move_down.bl_idname, text="", icon='TRIA_DOWN')

        input = inputs.active
        if input:
            layout.separator()
            type = input.type

            if   type == 'LOCATION': self.draw_location(context, input)
            elif type == 'ROTATION': self.draw_rotation(context, input)
            elif type == 'SCALE'   : self.draw_scale(context, input)
            elif type == 'BBONE'   : self.draw_bbone(context, input)

            col = layout_split(layout, "Influence")
            col.prop(input.id_data.data, input.influence_property_path, text="", slider=True)
            col.separator()

    def draw_transform_target(self, context: bpy.types.Context, target: RBFDriverInputTarget) -> None:
        col = layout_split(self.layout, "Target", align=True)
        col.prop_search(target, "object", context.blend_data, "objects", text="", icon='OBJECT_DATA')

        obj = target.object
        if obj is not None and obj.type == 'ARMATURE':
            row = col.row(align=True)
            row.alert = bool(target.bone_target) and target.bone_target not in obj.data.bones
            col.prop_search(target, "bone_target", obj.data, "bones", text="", icon='BONE_DATA')

        col.separator()

    def draw_location(self, context: bpy.types.Context, input: RBFDriverInput) -> None:
        layout = self.layout
        variables = input.variables
        self.draw_transform_target(context, variables[0].targets[0])

        col, dec = layout_split(layout, "Location", decorate_fill=False)
        row = col.row(align=True)
        for axis, variable in zip("XYZ", variables):
            row.prop(variable, "enabled", text=axis, toggle=True)

        if input.has_symmetry_target:
            dec.popover(panel=RBFDRIVERS_PT_input_location_symmetry_settings.bl_idname,
                        icon='MOD_MIRROR',
                        text="")
        else:
            dec.label(icon='BLANK1')

        col.prop(variables[0].targets[0], "transform_space", text="")
        col.separator()

    def draw_rotation(self, context: bpy.types.Context, input: RBFDriverInput) -> None:
        layout = self.layout
        variables = input.variables
        self.draw_transform_target(context, variables[0].targets[0])

        col, dec = layout_split(layout, "Rotation", decorate_fill=False)
        col.prop(input, "rotation_mode", text="")

        if input.has_symmetry_target:
            dec.popover(panel=RBFDRIVERS_PT_input_rotation_symmetry_settings.bl_idname,
                        icon='MOD_MIRROR',
                        text="")
        else:
            dec.label(icon='BLANK1')

        if len(input.rotation_mode) < 5:
            row = col.row(align=True)
            for key, var in zip("XYZ", variables[1:]):
                row.prop(var, "enabled", text=key, toggle=True)

        col.prop(variables[0].targets[0], "transform_space", text="")
        col.separator()

    def draw_scale(self, context: bpy.types.Context, input: RBFDriverInput) -> None:
        layout = self.layout
        variables = input.variables
        self.draw_transform_target(context, variables[0].targets[0])

        col, dec = layout_split(layout, "Scale", decorate_fill=False)
        row = col.row(align=True)
        for axis, variable in zip("XYZ", variables):
            row.prop(variable, "enabled", text=axis, toggle=True)

        if input.has_symmetry_target:
            dec.popover(panel=RBFDRIVERS_PT_input_scale_symmetry_settings.bl_idname,
                        icon='MOD_MIRROR',
                        text="")
        else:
            dec.label(icon='BLANK1')

        col.prop(variables[0].targets[0], "transform_space", text="")
        col.separator()

    def draw_bbone(self, context: bpy.types.Context, input: RBFDriverInput) -> None:
        variables = input.variables
        target = variables[0].targets[0]
        layout = self.layout

        col = layout_split(layout, "Target", align=True)
        col.prop_search(target, "object", context.blend_data, "objects", text="", icon='ARMATURE_DATA')

        obj = target.object
        row = col.row(align=True)
        if obj is not None and obj.type == 'ARMATURE':
            row.alert = bool(target.bone_target) and target.object is None or target.bone_target not in obj.data.bones
            row.prop_search(target, "bone_target", obj.data, "bones", text="", icon='BONE_DATA')
        else:
            row.alert = bool(target.bone_target)
            row.prop(target, "bone_target", text="", icon='BONE_DATA')

        col.separator()

        labels, values, decorations = layout_split(layout, align=True, decorate_fill=False)

        labels.label(text="Curve In")
        row = values.row(align=True)
        row.prop(variables["curveinx"], "enabled", text="X", toggle=True)
        row.prop(variables["curveinz"], "enabled", text="Z", toggle=True)

        if input.has_symmetry_target:
            decorations.popover(RBFDRIVERS_PT_input_bbone_curvein_symmetry_settings.bl_idname,
                                text="",
                                icon='MOD_MIRROR')
        else:
            decorations.label(icon='BLANK1')

        labels.label(text="Out")
        row = values.row(align=True)
        row.prop(variables["curveoutx"], "enabled", text="X", toggle=True)
        row.prop(variables["curveoutz"], "enabled", text="Z", toggle=True)

        if input.has_symmetry_target:
            decorations.popover(RBFDRIVERS_PT_input_bbone_curveout_symmetry_settings.bl_idname,
                                text="",
                                icon='MOD_MIRROR')
        else:
            decorations.label(icon='BLANK1')

        labels.separator()
        values.separator()
        decorations.separator()

        labels.label(text="Roll")
        row = values.row(align=True)
        row.prop(variables["rollin"], "enabled", text="In", toggle=True)
        row.prop(variables["rollout"], "enabled", text="Out", toggle=True)

        if input.has_symmetry_target:
            decorations.popover(RBFDRIVERS_PT_input_bbone_roll_symmetry_settings.bl_idname,
                                text="",
                                icon='MOD_MIRROR')
        else:
            decorations.label(icon='BLANK1')

        labels.separator()
        values.separator()
        decorations.separator()

        labels.label(text="Ease")
        row = values.row(align=True)
        row.prop(variables["easein"], "enabled", text="In", toggle=True)
        row.prop(variables["easeout"], "enabled", text="Out", toggle=True)

        labels.separator()
        values.separator()
        decorations.separator()

        labels.label(text="Scale In")
        row = values.row(align=True)
        row.prop(variables["scaleinx"], "enabled", text="X", toggle=True)
        row.prop(variables["scaleiny"], "enabled", text="Y", toggle=True)
        row.prop(variables["scaleinz"], "enabled", text="Z", toggle=True)

        labels.label(text="Out")
        row = values.row(align=True)
        row.prop(variables["scaleoutx"], "enabled", text="X", toggle=True)
        row.prop(variables["scaleouty"], "enabled", text="Y", toggle=True)
        row.prop(variables["scaleoutz"], "enabled", text="Z", toggle=True)

        layout.separator(factor=0.5)

    def draw_shape_key(self, context: bpy.types.Context, input: RBFDriverInput) -> None:
        var = input.variables[0]
        obj = var.targets[0].object
        col = layout_split(self.layout, "Target", align=True)

        col.prop_search(input, "object", context.blend_data, "objects", text="", icon='SHAPEKEY_DATA')

        if obj is not None and obj.type == 'MESH' and obj.data.shape_keys is not None:
            col.prop_search(obj.data.shape_keys, "key_blocks", var, "name", text="", icon='SHAPEKEY_DATA')
        else:
            col.prop(var, "name", text="", icon='SHAPEKEY_DATA')

    def draw_generic(self, context: bpy.types.Context, input: RBFDriverInput) -> None:
        var = input.variables[0]
        tgt = var.targets[0]

        row = self.layout.row(align=True)
        row.prop(var, "type", text="", icon_only=True)
        row.prop(var, "name", text="")

        if var.type == 'TRANSFORMS':
            self.draw_transform_target(context, tgt, align=True)
            col = layout_split(self.layout, "Channel")
            col.prop(tgt, "transform_type", text="")
            if var.transform_type.startswith('ROT'):
                col.prop(tgt, "rotation_mode", text="")
            col.prop(tgt, "transform_space", text="")

        elif var.type == 'SINGLE_PROP':
            col = layout_split(self.layout, "Target")
            row = col.row(align=True)
            row.prop(tgt, "id_type", text="", icon_only=True)
            col = row.col(align=True)
            col.prop_search(tgt, "object", context.blend_data, "objects", text="", icon="")
            row = col.row(align=True)
            id = tgt.id
            if id and tgt.data_path:
                try:
                    val = id.path_resolve(tgt.data_path)
                except ValueError:
                    row.alert = True
                else:
                    row.alert = isinstance(val, (float, int, bool))
            row.prop(tgt, "data_path", text="", icon='RNA')

        else:
            for key, tgt in zip("AB", (tgt, var.targets[1])):
                col = layout_split(self.layout, f'Target {key}')
                self.draw_transform_target(col, tgt)
                if var.type == 'LOC_DIFF':
                    col.prop(tgt, "transform_space", text="")




class RBFDRIVERS_UL_outputs(bpy.types.UIList):
    bl_idname = 'RBFDRIVERS_UL_outputs'

    def draw_item(self, context, layout, data, item: RBFDriverOutput, icon, active_data, active_prop) -> None:
        layout.prop(item, "name", text="", emboss=False, translate=False)
        row = layout.row()
        row.alignment = 'RIGHT'
        row.prop(item.id_data.data, item.influence_property_path, text="", slider=True)
        row.prop(item, "mute", text="", icon=f'CHECKBOX_{"DE" if item.mute else ""}HLT', emboss=False)
        row.separator(factor=0.25)


class RBFDRIVERS_PT_output_location_symmetry_settings(bpy.types.Panel):
    
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_output_location_symmetry_settings'
    bl_label = "Symmetry Settings"
    bl_options = {'INSTANCED'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.outputs.active is not None
                and object.rbf_drivers.active.outputs.active.type == 'LOCATION')

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        output = context.object.rbf_drivers.active.outputs.active
        for axis, channel in zip('XYZ', output.channels):
            row = layout.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text=f'{"Invert " if axis == "X" else ""}{axis}')
            row.prop(channel, "invert", text="")


class RBFDRIVERS_PT_output_rotation_symmetry_settings(bpy.types.Panel):
    
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_output_rotation_symmetry_settings'
    bl_label = "Symmetry Settings"
    bl_options = {'INSTANCED'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.outputs.active is not None
                and object.rbf_drivers.active.outputs.active.type == 'ROTATION')

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        output = context.object.rbf_drivers.active.outputs.active
        for axis, channel in zip('XYZ', output.channels[1:]):
            row = layout.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text=f'{"Invert " if axis == "X" else ""}{axis}')
            row.prop(channel, "invert", text="")


class RBFDRIVERS_PT_output_scale_symmetry_settings(bpy.types.Panel):
    
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_output_scale_symmetry_settings'
    bl_label = "Symmetry Settings"
    bl_options = {'INSTANCED'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.outputs.active is not None
                and object.rbf_drivers.active.outputs.active.type == 'SCALE')

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        output = context.object.rbf_drivers.active.outputs.active
        for axis, channel in zip('XYZ', output.channels):
            row = layout.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text=f'{"Invert " if axis == "X" else ""}{axis}')
            row.prop(channel, "invert", text="")


class RBFDRIVERS_PT_output_bbone_curvein_symmetry_settings(bpy.types.Panel):
    
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_output_bbone_curvein_symmetry_settings'
    bl_label = "Symmetry Settings"
    bl_options = {'INSTANCED'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.outputs.active is not None
                and object.rbf_drivers.active.outputs.active.type == 'BBONE')

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        output = context.object.rbf_drivers.active.outputs.active
        for axis in "XZ":
            row = layout.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text=f'{"Invert " if axis == "X" else ""}{axis}')
            row.prop(output.channels[f'curvein{axis.lower()}'], "invert", text="")


class RBFDRIVERS_PT_output_bbone_curveout_symmetry_settings(bpy.types.Panel):
    
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_output_bbone_curveout_symmetry_settings'
    bl_label = "Symmetry Settings"
    bl_options = {'INSTANCED'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.outputs.active is not None
                and object.rbf_drivers.active.outputs.active.type == 'BBONE')

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        output = context.object.rbf_drivers.active.outputs.active
        for axis in "XZ":
            row = layout.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text=f'{"Invert " if axis == "X" else ""}{axis}')
            row.prop(output.channels[f'curveout{axis.lower()}'], "invert", text="")


class RBFDRIVERS_PT_output_bbone_roll_symmetry_settings(bpy.types.Panel):
    
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_output_bbone_roll_symmetry_settings'
    bl_label = "Symmetry Settings"
    bl_options = {'INSTANCED'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.outputs.active is not None
                and object.rbf_drivers.active.outputs.active.type == 'BBONE')

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        output = context.object.rbf_drivers.active.outputs.active
        for direction in ('IN', 'OUT'):
            row = layout.row(align=True)
            row.alignment = 'RIGHT'
            row.label(text=f'{"Invert " if direction == "IN" else ""}{direction.title()}')
            row.prop(output.channels[f'roll{direction.lower()}'], "invert", text="")


class RBFDRIVERS_PT_outputs(bpy.types.Panel):

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_outputs'
    bl_parent_id = RBFDRIVERS_PT_drivers.bl_idname
    bl_description = "RBF driver outputs"
    bl_label = "Outputs"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.type != 'SHAPE_KEYS')

    def draw(self, context: bpy.types.Context) -> None:
        object = context.object
        layout = self.layout
        outputs = object.rbf_drivers.active.outputs

        row = layout.row()
        col = row.column()
        col.template_list(RBFDRIVERS_UL_outputs.bl_idname, "",
                          outputs, "collection__internal__", outputs, "active_index")
        
        col = row.column(align=True)
        col.operator_menu_enum(RBFDRIVERS_OT_output_add.bl_idname, "type", text="", icon='ADD')
        col.operator(RBFDRIVERS_OT_output_remove.bl_idname, text="", icon='REMOVE')
        col.separator()
        col.operator(RBFDRIVERS_OT_output_move_up.bl_idname, text="", icon='TRIA_UP')
        col.operator(RBFDRIVERS_OT_output_move_down.bl_idname, text="", icon='TRIA_DOWN')

        layout.separator(factor=0.5)

        output = outputs.active
        if output:
            type = output.type

            if type == 'LOCATION': self.draw_location(context, output)
            if type == 'ROTATION': self.draw_rotation(context, output)
            if type == 'SCALE'   : self.draw_scale(context, output)

            layout.separator(factor=0.5)

            col = layout_split(layout, "Influence")
            col.prop(output.id_data.data, output.influence_property_path, text="", slider=True)

            layout.separator(factor=0.5)

    def draw_transform_target(self, context: bpy.types.Context, channel: RBFDriverOutputChannel) -> None:

        col = layout_split(self.layout, "Target", align=True)
        col.prop_search(channel, "object", context.blend_data, "objects", text="", icon='OBJECT_DATA')

        obj = channel.object
        if obj is not None and obj.type == 'ARMATURE':
            row = col.row(align=True)
            row.alert = bool(channel.bone_target) and channel.bone_target not in obj.data.bones
            col.prop_search(channel, "bone_target", obj.data, "bones", text="", icon='BONE_DATA')

        col.separator()

    def draw_location(self, context: bpy.types.Context, output: RBFDriverOutput) -> None:
        layout = self.layout
        channels = output.channels
        channel = channels[0]
        self.draw_transform_target(context, channel)

        col, dec = layout_split(layout, "Location",
                                align=True,
                                decorate_fill=False)

        row = col.row(align=True)
        for axis, channel in zip('XYZ', channels):
            row.prop(channel, "enabled", text=axis, toggle=True)

        if output.has_symmetry_target:
            dec.popover(panel=RBFDRIVERS_PT_output_location_symmetry_settings.bl_idname,
                        icon='MOD_MIRROR',
                        text="")
        else:
            dec.label(icon='BLANK1')

    def draw_rotation(self, context: bpy.types.Context, output: RBFDriverOutput) -> None:
        layout = self.layout
        channels = output.channels
        channel = channels[0]
        self.draw_transform_target(context, channel)

        col, dec = layout_split(layout, "Rotation", decorate_fill=False)

        if output.rotation_mode == 'EULER':
            axes = 'XYZ'
            channels = channels[1:]
        else:
            axes = 'XYZ'

        tgt = channel.object
        if tgt is not None and tgt.type == 'ARMATURE':
            tgt = tgt.pose.bones.get(channel.bone_target)

        row = col.row()
        if tgt:
            mode = 'EULER' if len(tgt.rotation_mode) < 5 else tgt.rotation_mode
            row.alert = mode != output.rotation_mode

        row.prop(output, "rotation_mode", text="")
        dec.label(icon='BLANK1')

        row = col.row(align=True)
        for axis, channel in zip(axes, channels):
            row.prop(channel, "enabled", text=axis, toggle=True)

        if output.has_symmetry_target:
            dec.popover(panel=RBFDRIVERS_PT_output_rotation_symmetry_settings.bl_idname,
                        icon='MOD_MIRROR',
                        text="")
        else:
            dec.label(icon='BLANK1')

        if output.rotation_mode == 'QUATERNION':
            row = col.row()
            row.alignment = 'RIGHT'
            row.label(text="Use Logarithmic Map")
            row.prop(output, "use_logarithmic_map", text="",)

    def draw_scale(self, context: bpy.types.Context, output: RBFDriverOutput) -> None:
        layout = self.layout
        channels = output.channels
        channel = channels[0]
        self.draw_transform_target(context, channel)

        col, dec = layout_split(layout, "Scale",
                                align=True,
                                decorate_fill=False)

        row = col.row(align=True)
        for axis, channel in zip('XYZ', channels):
            row.prop(channel, "enabled", text=axis, toggle=True)

        if output.has_symmetry_target:
            dec.popover(panel=RBFDRIVERS_PT_output_scale_symmetry_settings.bl_idname,
                        icon='MOD_MIRROR',
                        text="")
        else:
            dec.label(icon='BLANK1')

    def draw_bbone(self, context: bpy.types.Context, output: RBFDriverInput) -> None:
        channels = output.channels
        channel = channels[0]
        layout = self.layout

        col = layout_split(layout, "Target", align=True)
        col.prop_search(channel, "object", context.blend_data, "objects", text="", icon='ARMATURE_DATA')

        obj = channel.object
        row = col.row(align=True)
        if obj is not None and obj.type == 'ARMATURE':
            row.alert = bool(channel.bone_target) and channel.object is None or channel.bone_target not in obj.data.bones
            row.prop_search(channel, "bone_target", obj.data, "bones", text="", icon='BONE_DATA')
        else:
            row.alert = bool(channel.bone_target)
            row.prop(channel, "bone_target", text="", icon='BONE_DATA')

        col.separator()

        labels, values, decorations = layout_split(layout, align=True, decorate_fill=False)

        labels.label(text="Curve In")
        row = values.row(align=True)
        row.prop(channels["curveinx"], "enabled", text="X", toggle=True)
        row.prop(channels["curveinz"], "enabled", text="Z", toggle=True)

        if input.has_symmetry_target:
            decorations.popover(RBFDRIVERS_PT_input_bbone_curvein_symmetry_settings.bl_idname,
                                text="",
                                icon='MOD_MIRROR')
        else:
            decorations.label(icon='BLANK1')

        labels.label(text="Out")
        row = values.row(align=True)
        row.prop(channels["curveoutx"], "enabled", text="X", toggle=True)
        row.prop(channels["curveoutz"], "enabled", text="Z", toggle=True)

        if input.has_symmetry_target:
            decorations.popover(RBFDRIVERS_PT_input_bbone_curveout_symmetry_settings.bl_idname,
                                text="",
                                icon='MOD_MIRROR')
        else:
            decorations.label(icon='BLANK1')

        labels.separator()
        values.separator()
        decorations.separator()

        labels.label(text="Roll")
        row = values.row(align=True)
        row.prop(channels["rollin"], "enabled", text="In", toggle=True)
        row.prop(channels["rollout"], "enabled", text="Out", toggle=True)

        if input.has_symmetry_target:
            decorations.popover(RBFDRIVERS_PT_input_bbone_roll_symmetry_settings.bl_idname,
                                text="",
                                icon='MOD_MIRROR')
        else:
            decorations.label(icon='BLANK1')

        labels.separator()
        values.separator()
        decorations.separator()

        labels.label(text="Ease")
        row = values.row(align=True)
        row.prop(channels["easein"], "enabled", text="In", toggle=True)
        row.prop(channels["easeout"], "enabled", text="Out", toggle=True)

        labels.separator()
        values.separator()
        decorations.separator()

        labels.label(text="Scale In")
        row = values.row(align=True)
        row.prop(channels["scaleinx"], "enabled", text="X", toggle=True)
        row.prop(channels["scaleiny"], "enabled", text="Y", toggle=True)
        row.prop(channels["scaleinz"], "enabled", text="Z", toggle=True)

        labels.label(text="Out")
        row = values.row(align=True)
        row.prop(channels["scaleoutx"], "enabled", text="X", toggle=True)
        row.prop(channels["scaleouty"], "enabled", text="Y", toggle=True)
        row.prop(channels["scaleoutz"], "enabled", text="Z", toggle=True)

        layout.separator(factor=0.5)


class RBFDRIVERS_UL_poses(bpy.types.UIList):
    bl_idname = 'RBFDRIVERS_UL_poses'

    def draw_item(self, context, layout, data, item, icon, active_data, active_prop, index, flt_flag) -> None:
        driver = context.object.rbf_drivers.active

        if driver is not None and driver.type == 'SHAPE_KEYS':
            icon = 'SHAPEKEY_DATA'
        else:
            icon = 'POSE_HLT'

        layout.prop(item, "name",
                    text="",
                    icon=icon,
                    emboss=False,
                    translate=False)

        if driver is not None:            
            if driver.type == 'SHAPE_KEYS':
                if index > 0:
                    key = driver.id_data.data.shape_keys
                    if key:
                        shape = key.key_blocks.get(item.name)
                        if shape:
                            row = layout.row()
                            row.alignment = 'RIGHT'
                            row.prop(shape, "value", text="")
            else:
                row = layout.row()
                row.alignment = 'RIGHT'
                row.prop(item.id_data.data, active_data.weight_property_path, index=index, text="")


class RBFDRIVERS_PT_poses(bpy.types.Panel):

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_poses'
    bl_parent_id = RBFDRIVERS_PT_drivers.bl_idname
    bl_description = "RBF driver poses"
    bl_label = "Poses"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None)

    def draw(self, context: bpy.types.Context) -> None:
        object = context.object
        layout = self.layout
        driver = object.rbf_drivers.active
        poses = driver.poses

        row = layout.row()
        col = row.column()
        col.template_list(RBFDRIVERS_UL_poses.bl_idname, "",
                          poses, "collection__internal__", poses, "active_index")

        col = row.column(align=True)
        col.operator(RBFDRIVERS_OT_pose_add.bl_idname, text="", icon='ADD')
        col.operator(RBFDRIVERS_OT_pose_remove.bl_idname, text="", icon='REMOVE')
        col.separator()
        col.operator_menu_enum(RBFDRIVERS_OT_pose_update.bl_idname, "layers", text="", icon='DOWNARROW_HLT')
        col.separator()
        col.operator(RBFDRIVERS_OT_pose_move_up.bl_idname, text="", icon='TRIA_UP')
        col.operator(RBFDRIVERS_OT_pose_move_down.bl_idname, text="", icon='TRIA_DOWN')

        pose = poses.active

        if pose is not None:
            index = poses.active_index

            if driver.type == 'SHAPE_KEYS':
                if object.type == 'MESH':
                    key = object.data.shape_keys
                    col = layout_split(layout, "Shape")
                    col.alert = key is None or pose.name not in key.key_blocks
                    col.enabled = col.alert or index > 0

                    if key:
                        col.prop_search(pose, "name", key, "key_blocks", text="", icon='SHAPEKEY_DATA')
                        if index > 0:
                            shape = key.key_blocks.get(pose.name)
                            if shape:
                                col = layout_split(layout, "Value")
                                col.prop(shape, "value", text="")
                    else:
                        col.prop(pose, "name", text="", icon='SHAPEKEY_DATA')
            else:
                col = layout_split(layout, "Weight")
                col.prop(poses.id_data.data, poses.weight_property_path, index=poses.active_index, text="")


class RBFDRIVERS_PT_pose_interpolation(bpy.types.Panel):

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_pose_interpolation'
    bl_parent_id = RBFDRIVERS_PT_poses.bl_idname
    bl_description = "RBF driver pose interpolation"
    bl_label = "Interpolation"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.poses.active is not None)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        driver = context.object.rbf_drivers.active
        pose = driver.poses.active

        col = layout_split(layout, "Falloff", decorate=False)
        col.row()
        col.prop(pose.falloff, "enabled", text="Override")

        if pose.falloff.enabled:
            draw_curve_manager_ui(col, pose.falloff)
        else:
            col = col.column()
            col.enabled = False
            draw_curve_manager_ui(col, driver.falloff)

        row = col.row()
        row.prop(driver.falloff, "radius", text="Radius")
        row.label(icon='BLANK1')



def draw_active_pose_data(layout: bpy.types.UILayout, data: ActivePoseData):
    labels, values, = layout_split(layout, align=True)
    type = data.type

    if type in ('LOCATION', 'SCALE'):
        pfix = f'{type.title()} '
        for axis, item in zip('XYZ', data):
            labels.label(text=f'{pfix if axis == "X" else ""}{axis}')
            values.prop(item, "value", text="")

    elif type == 'ROTATION':
        mode = data.rotation_mode
        pfix = "Rotation "
        if mode == 'EULER':
            for axis, item in zip('XYZ', data[1:]):
                labels.label(text=f'{pfix if axis == "X" else ""}{axis}')
                values.prop(item, "angle", text="")
        elif mode == 'QUATERNION':
            for axis, item in zip('WXYZ', data):
                labels.label(text=f'{pfix if axis == "W" else ""}{axis}')
                values.prop(item, "value", text="")
        else: # AXIS_ANGLE
            for axis, item in zip('WXYZ', data):
                labels.label(text=f'{pfix if axis == "W" else ""}{axis}')
                values.prop(item, "angle" if axis == 'W' else "value", text="")

        labels.separator()
        values.separator()
        labels.label(icon='BLANK1')

        split = values.split(factor=1/3)
        row = split.row()
        row.alignment = 'RIGHT'
        row.label(text="Edit Mode")
        split.row().prop(data, "rotation_mode", text="")
    
    elif type == 'BBONE':
        labels.label(text="Curve In X")
        values.prop(data["curveinx"], "value", text="")
        labels.label(text="Z")
        values.prop(data["curveinz"], "value", text="")

        labels.separator()
        values.separator()

        labels.label(text="Curve Out X")
        values.prop(data["curveoutx"], "value", text="")
        labels.label(text="Z")
        values.prop(data["curveoutz"], "value", text="")

        labels.separator()
        values.separator()

        labels.label(text="Roll In")
        values.prop(data["rollin"], "angle", text="")
        labels.label(text="Out")
        values.prop(data["rollout"], "angle", text="")

        labels.separator()
        values.separator()

        labels.label(text="Ease In")
        values.prop(data["easein"], "easing", text="")
        labels.label(text="Out")
        values.prop(data["easeout"], "easing", text="")

        labels.separator()
        values.separator()

        labels.label(text="Scale In X")
        values.prop(data["curveinx"], "value", text="")
        labels.label(text="Y")
        values.prop(data["curveiny"], "value", text="")
        labels.label(text="Z")
        values.prop(data["curveinz"], "value", text="")

        labels.separator()
        values.separator()

        labels.label(text="Scale Out X")
        values.prop(data["curveoutx"], "value", text="")
        labels.label(text="Y")
        values.prop(data["curveouty"], "value", text="")
        labels.label(text="Z")
        values.prop(data["curveoutz"], "value", text="")

    else:
        for item in data:
            labels.label(text=item.name)
            values.prop(item, "value", text="")


class RBFDRIVERS_PT_pose_input_values(bpy.types.Panel):

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_pose_input_values'
    bl_parent_id = RBFDRIVERS_PT_poses.bl_idname
    bl_description = "RBF driver pose input values"
    bl_label = "Input Values"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.poses.active is not None)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        driver = context.object.rbf_drivers.active
        for input in driver.inputs:
            layout_split(layout, " ").label(text=input.name)
            draw_active_pose_data(layout, input.active_pose)
            layout.separator()


class RBFDRIVERS_PT_pose_output_values(bpy.types.Panel):

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_pose_output_values'
    bl_parent_id = RBFDRIVERS_PT_poses.bl_idname
    bl_description = "RBF driver pose output values"
    bl_label = "Output Values"

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.poses.active is not None)

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        driver = context.object.rbf_drivers.active
        for output in driver.outputs:
            layout_split(layout, " ").label(text=output.name)
            draw_active_pose_data(layout, output.active_pose)
            layout.separator()

