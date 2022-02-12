
import typing
import bpy
from rbf_drivers.output import RBFDriverOutput, RBFDriverOutputChannel
from .lib.curve_mapping import draw_curve_manager_ui
from .input import RBFDriverInput, RBFDriverInputTarget

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

    def draw_item(self, context, layout, data, item, icon, active_data, active_prop) -> None:
        layout.prop(item, "name",
                    icon_value=bpy.types.UILayout.enum_item_icon(item, "type", item.type),
                    text="",
                    emboss=False,
                    translate=False)

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
            if object.type == 'MESH':
                layout.operator_menu_enum(RBFDRIVERS_OT_new.bl_idname, "type", text="Add", icon='ADD')
            else:
                layout.operator(RBFDRIVERS_OT_new.bl_idname, text="Add", icon='ADD').type = 'NONE'
        else:
            drivers = object.rbf_drivers
            row = layout.row()
            col = row.column()
            col.template_list(RBFDRIVERS_UL_drivers.bl_idname, "",
                              drivers, "collection__internal__", drivers, "active_index")
            
            col = row.column(align=True)

            if object.type == 'MESH':
                col.operator_menu_enum(RBFDRIVERS_OT_new.bl_idname, "type", text="", icon='ADD')
            else:
                col.operator(RBFDRIVERS_OT_new.bl_idname, text="", icon='ADD').type = 'NONE'

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
            type = input.type

            if type == 'LOCATION': self.draw_location(context, input)
            if type == 'ROTATION': self.draw_rotation(context, input)
            if type == 'SCALE'   : self.draw_scale(context, input)

            col = layout_split(layout, "Influence")
            col.prop(input.id_data.data, input.influence_property_path, text="", slider=True)

    def draw_transform_target(self, context: bpy.types.Context, target: RBFDriverInputTarget) -> None:

        col = layout_split(self.layout, "Target", align=True)
        col.prop_search(target, "object", context.blend_data, "objects", text="", icon='OBJECT_DATA')

        obj = target.object
        if obj is not None and obj.type == 'ARMATURE':
            row = col.row(align=True)
            row.alert = bool(target.bone_target) and target.bone_target not in obj.data.bones
            col.prop_search(target, "bone_target", obj.data, "bones", text="", icon='BONE_DATA')

    def draw_location(self, context: bpy.types.Context, input: RBFDriverInput) -> None:
        vars = input.variables
        self.draw_transform_target(context, vars[0].targets[0])

        col = layout_split(self.layout, "Location")
        row = col.row(align=True)
        for key, var in zip("XYZ", vars):
            row.prop(var, "enabled", text=key, toggle=True)

        col.prop(vars[0].targets[0], "transform_space", text="")

    def draw_rotation(self, context: bpy.types.Context, input: RBFDriverInput) -> None:
        vars = input.variables
        self.draw_transform_target(context, vars[0].targets[0])

        col = layout_split(self.layout, "Rotation")
        col.prop(input, "rotation_mode", text="")

        mode = input.rotation_mode

        if len(mode) < 5:
            row = col.row(align=True)
            for key, var in zip("XYZ", vars):
                row.prop(var, "enabled", text=key, toggle=True)

        col.prop(vars[0].targets[0], "transform_space", text="")

    def draw_scale(self, context: bpy.types.Context, input: RBFDriverInput) -> None:
        vars = input.variables
        self.draw_transform_target(context, vars[0].targets[0])

        col = layout_split(self.layout, "Scale")
        row = col.row(align=True)
        for key, var in zip("XYZ", vars):
            row.prop(var, "enabled", text=key, toggle=True)

        col.prop(vars[0].targets[0], "transform_space", text="")


class RBFDRIVERS_UL_outputs(bpy.types.UIList):
    bl_idname = 'RBFDRIVERS_UL_outputs'

    def draw_item(self, context, layout, data, item, icon, active_data, active_prop) -> None:
        layout.prop(item, "name", text="", emboss=False, translate=False)
        row = layout.row(align=True)
        row.alignment = 'RIGHT'
        row.prop(item.id_data.data, item.influence_property_path, text="", slider=True)

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

        output = outputs.active
        if output:
            type = output.type

            if type == 'LOCATION': self.draw_location(context, output)
            if type == 'ROTATION': self.draw_rotation(context, output)
            if type == 'SCALE'   : self.draw_scale(context, output)

            col = layout_split(layout, "Influence")
            col.prop(output.id_data.data, output.influence_property_path, text="", slider=True)

    def draw_transform_target(self, context: bpy.types.Context, channel: RBFDriverOutputChannel) -> None:

        col = layout_split(self.layout, "Target", align=True)
        col.prop_search(channel, "object", context.blend_data, "objects", text="", icon='OBJECT_DATA')

        obj = channel.object
        if obj is not None and obj.type == 'ARMATURE':
            row = col.row(align=True)
            row.alert = bool(channel.bone_target) and channel.bone_target not in obj.data.bones
            col.prop_search(channel, "bone_target", obj.data, "bones", text="", icon='BONE_DATA')

    def draw_location(self, context: bpy.types.Context, output: RBFDriverOutput) -> None:
        channels = output.channels
        channel = channels[0]
        self.draw_transform_target(context, channel)

        target = channel.object
        if target is not None and target.type == 'ARMATURE' and channel.bone_target:
            target = target.pose.bones.get(channel.bone_target)

        if target is not None:
            props, decorations = layout_split(self.layout, "Location", align=True, decorate_fill=False)
            for index, (label, channel) in enumerate(zip("XYZ", channels)):
                row = props.row(align=True)
                row.prop(target, "location", index=index, text=label)
                row.separator(factor=0.5)
                row.prop(channel, "enabled", text="")
                if not channel.enabled:
                    decorations.label(icon='BLANK1')
                else:
                    decorations.prop(channel, "mute",
                                    text="",
                                    icon=f'MUTE_IPO_{"OFF" if channel.mute else "ON"}',
                                    emboss=False)

    def draw_rotation(self, context: bpy.types.Context, output: RBFDriverOutput) -> None:
        channels = output.channels
        channel = channels[0]
        self.draw_transform_target(context, channel)

        target = channel.object
        if target is not None and target.type == 'ARMATURE' and channel.bone_target:
            target = target.pose.bones.get(channel.bone_target)

        if target is not None:
            prop = f'rotation_{output.rotation_mode.lower()}'
            props, decorations = layout_split(self.layout, "Location", align=True, decorate_fill=False)

            if output.rotation_mode == 'EULER':
                axes = 'XYZ'
                channels = channels[1:]
            else:
                axes = 'WXYZ'

            for index, (label, channel) in enumerate(zip(axes, channels)):
                row = props.row(align=True)
                row.prop(target, prop, index=index, text=label)
                row.separator(factor=0.5)
                row.prop(channel, "enabled", text="")
                if not channel.enabled:
                    decorations.label(icon='BLANK1')
                else:
                    decorations.prop(channel, "mute",
                                    text="",
                                    icon=f'MUTE_IPO_{"OFF" if channel.mute else "ON"}',
                                    emboss=False)

    def draw_scale(self, context: bpy.types.Context, output: RBFDriverOutput) -> None:
        channels = output.channels
        channel = channels[0]
        self.draw_transform_target(context, channel)

        target = channel.object
        if target is not None and target.type == 'ARMATURE' and channel.bone_target:
            target = target.pose.bones.get(channel.bone_target)

        if target is not None:
            props, decorations = layout_split(self.layout, "scale", align=True, decorate_fill=False)
            for index, (label, channel) in enumerate(zip("XYZ", channels)):
                row = props.row(align=True)
                row.prop(target, "scale", index=index, text=label)
                row.separator(factor=0.5)
                row.prop(channel, "enabled", text="")
                if not channel.enabled:
                    decorations.label(icon='BLANK1')
                else:
                    decorations.prop(channel, "mute",
                                    text="",
                                    icon=f'MUTE_IPO_{"OFF" if channel.mute else "ON"}',
                                    emboss=False)

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

