
from typing import TYPE_CHECKING, Optional
from bpy.types import Menu, Panel, UIList
from rbf_drivers.api.input import INPUT_TYPE_ICONS
from rbf_drivers.api.output import OUTPUT_TYPE_ICONS
from .drivers import RBFDRIVERS_PT_drivers
from .utils import GUIUtils, idprop_data_render
from ..lib.curve_mapping import draw_curve_manager_ui
from ..ops.pose import (RBFDRIVERS_OT_pose_add,
                        RBFDRIVERS_OT_pose_remove,
                        RBFDRIVERS_OT_pose_update,
                        RBFDRIVERS_OT_pose_move_up,
                        RBFDRIVERS_OT_pose_move_down)
if TYPE_CHECKING:
    from bpy.types import Context, UILayout
    from ..api.input import RBFDriverInput
    from ..api.inputs import RBFDriverInputs
    from ..api.output_channel import RBFDriverOutputChannel
    from ..api.output import RBFDriverOutput
    from ..api.pose import RBFDriverPose
    from ..api.driver import RBFDriver


class RBFDRIVERS_UL_poses(UIList):
    bl_idname = 'RBFDRIVERS_UL_poses'

    def draw_item(self,
                  context: 'Context',
                  layout: 'UILayout', _0,
                  pose: 'RBFDriverPose',
                  icon: str, _1, _2,
                  index: int, _3) -> None:

        driver = context.object.rbf_drivers.active

        if driver is not None and driver.type == 'SHAPE_KEYS':
            icon = 'SHAPEKEY_DATA'
        else:
            icon = 'POSE_HLT'

        layout.prop(pose, "name",
                    text="",
                    icon=icon,
                    emboss=False,
                    translate=False)

        if driver is not None:            
            if driver.type == 'SHAPE_KEYS':
                if index > 0:
                    key = driver.id_data.data.shape_keys
                    if key:
                        shape = key.key_blocks.get(pose.name)
                        if shape:
                            row = layout.row()
                            row.alignment = 'RIGHT'
                            row.prop(shape, "value", text="")
            else:
                idprop = pose.weight
                subrow = layout.row()
                subrow.alignment = 'RIGHT'
                subrow.label(text=f'{idprop.value or 0.0:.3f} ')


class RBFDRIVERS_MT_pose_context_menu(Menu):
    bl_label = "Pose Specials Menu"
    bl_idname = 'RBFDRIVERS_MT_pose_context_menu'

    def draw(self, _: 'Context') -> None:
        layout = self.layout
        for label, layer in [
            ("Update Inputs"          , 'INPUT' ),
            ("Update Outputs"         , 'OUTPUT'),
            ("Update Inputs & Outputs", 'ALL'   )
            ]:
            props = layout.operator(RBFDRIVERS_OT_pose_update.bl_idname,
                                    icon='TRACKING_BACKWARDS',
                                    text=label)
            props.data_layer = layer
            props.pose_index = -1
            props.item_index = -1


class RBFDRIVERS_PT_poses(GUIUtils, Panel):

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_poses'
    bl_parent_id = RBFDRIVERS_PT_drivers.bl_idname
    bl_description = "RBF driver poses"
    bl_label = "Poses"

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None)

    def draw(self, context: 'Context') -> None:
        driver = context.object.rbf_drivers.active
        layout = self.subpanel(self.layout)
        layout.separator(factor=0.5)

        poses = driver.poses

        row = layout.row()
        row.scale_y = 0.6
        row.alignment = 'RIGHT'
        row.label(text="Weight")
        row.separator(factor=4.5)

        row = layout.row()
        col = row.column()
        col.template_list(RBFDRIVERS_UL_poses.bl_idname, "",
                          poses, "collection__internal__", poses, "active_index", rows=6)

        ops = row.column(align=True)
        ops.operator(RBFDRIVERS_OT_pose_add.bl_idname, text="", icon='ADD')
        ops.operator(RBFDRIVERS_OT_pose_remove.bl_idname, text="", icon='REMOVE')
        ops.separator()
        ops.menu(RBFDRIVERS_MT_pose_context_menu.bl_idname, text="", icon='DOWNARROW_HLT')
        ops.separator()
        ops.operator(RBFDRIVERS_OT_pose_move_up.bl_idname, text="", icon='TRIA_UP')
        ops.operator(RBFDRIVERS_OT_pose_move_down.bl_idname, text="", icon='TRIA_DOWN')

        pose = poses.active
        if pose:
            self.draw_pose_settings(layout, driver, pose, poses.active_index)

    def draw_pose_settings(self, layout: 'UILayout', driver: 'RBFDriver', pose: 'RBFDriverPose', pose_index: int) -> None:

        layout.separator()
        column = self.split_layout(layout, " ")
        idprop_data_render(column, pose.influence, text="Influence", slider=True)

        layout.separator()

        interpolation = pose.interpolation
        column = self.split_layout(layout, "Interpolation", decorate=False)

        row = column.row()
        row.prop(interpolation, "use_curve", text="Override Default")
        row.label(icon='BLANK1')

        if interpolation.use_curve:
            draw_curve_manager_ui(column, interpolation)
        else:
            subcolumn = column.column()
            subcolumn.enabled = False
            draw_curve_manager_ui(subcolumn, driver.interpolation)

        row = column.row()
        idprop_data_render(row, pose.radius, text="Radius")
        row.label(icon='BLANK1')

        inputs = driver.inputs
        if len(inputs):
            self.draw_input_values(layout, inputs, pose_index)

        outputs = driver.outputs
        if len(outputs):
            self.draw_output_values(layout, outputs, pose_index)

    def draw_input_values(self, layout: 'UILayout', inputs: 'RBFDriverInputs', pose_index: int):
        layout.separator()
        labels, column = self.split_layout(layout)
        labels.separator(factor=0.5)
        labels.label(text="Inputs")

        input: 'RBFDriverInput'
        for item_index, input in enumerate(inputs):
            subcolumn = column.column(align=True)
            row = subcolumn.box().row()
            row.prop(input, "ui_show_pose",
                     text="",
                     icon=f'DISCLOSURE_TRI_{"DOWN" if input.ui_show_pose else "RIGHT"}',
                     emboss=False)
            row.label(icon=INPUT_TYPE_ICONS[input.type], text=input.name)

            subrow = row.row()
            subrow.alignment = 'RIGHT'

            props = subrow.operator(RBFDRIVERS_OT_pose_update.bl_idname,
                                    icon='IMPORT',
                                    text="",
                                    emboss=False)
            props.data_layer = 'INPUT'
            props.pose_index = pose_index
            props.item_index = item_index

            if input.ui_show_pose:
                box = subcolumn.box()
                labels, values, decorations = self.split_layout(box, factor=0.25, align=True, decorate_fill=False)

                type = input.type

                if type in {'LOCATION', 'SCALE'}:
                    for variable in input.variables:
                        axis = variable.name
                        labels.label(text=f'{type.title() + " " if axis == "X" else ""}{axis}')
                        values.prop(variable.data[pose_index], "value", text="")
                        decorations.label(icon=f'DECORATE{"_KEYFRAME" if variable.is_enabled else ""}')

                elif type == 'ROTATION':
                    variables = input.variables

                    mode = input.rotation_mode
                    if mode == 'EULER':
                        variables = variables[1:]
                    elif mode == 'TWIST':
                        variables = variables['WXYZ'.index(input.rotation_axis)]
                    
                    for index, variable in enumerate(variables):
                        axis = variable.name
                        labels.label(text=f'{"Rotation " if index == 0 else ""}{axis}')
                        values.prop(variable.data[pose_index], "value", text="")
                        decorations.label(icon=f'DECORATE{"_KEYFRAME" if variable.is_enabled else ""}')

                elif type == 'ROTATION_DIFF':
                    labels.label(text="Difference")
                    values.prop(input.variables[0].data[pose_index], "angle", text="")
                    decorations.label(icon='DECORATE_KEYFRAME')
                
                elif type == 'LOC_DIFF':
                    labels.label(text="Distance")
                    values.prop(input.variables[0].data[pose_index], "value", text="")
                    decorations.label(icon='DECORATE_KEYFRAME')

                else:
                    for variable in input.variables:
                        labels.label(text=variable.name)
                        values.prop(variable.data[pose_index], "value", text="")
                        decorations.label(icon=f'DECORATE{"_KEYFRAME" if variable.is_enabled else ""}')

    def draw_output_values(self, layout: 'UILayout', outputs: 'RBFDriverInputs', pose_index: int):

        layout.separator()
        labels, column = self.split_layout(layout, align=True, decorate=False)
        labels.separator(factor=1/3)
        labels.label(text="Outputs")
        column.scale_y = 1/1.5

        output: 'RBFDriverOutput'
        for item_index, output in enumerate(outputs):
            row = column.row()
            box = row.box()
            
            sub = row.column()
            sub.scale_y = 1.6
            props = sub.operator(RBFDRIVERS_OT_pose_update.bl_idname, icon='TRACKING_BACKWARDS', text="")
            props.data_layer = 'OUTPUT'
            props.pose_index = pose_index
            props.item_index = item_index

            row = box.row(align=True)
            row.prop(output, "ui_show_pose",
                     text="",
                     icon=f'{"DOWNARROW_HLT" if output.ui_show_pose else "RIGHTARROW"}',
                     emboss=False)
            row.label(text=output.name)

            column.separator(factor=0.5)

            if output.ui_show_pose:
                type = output.type
                if type in {'LOCATION', 'SCALE'}:
                    labels = 'XYZ'
                    fields = ["value"] * 4
                    channels = output.channels
                elif type == 'ROTATION':
                    mode = output.rotation_mode
                    if mode == 'EULER':
                        labels = 'XYZ'
                        fields = ["angle"] * 4
                        channels = output.channels[1:]
                    else:
                        labels = 'WXYZ'
                        fields = ["value"] * 4 if mode == 'QUATERNION' else ["angle"] + (["value"] * 4)
                        channels = output.channels
                else:
                    labels = [channel.name for channel in output.channels]
                    fields = ["value"] * 4
                    channels = output.channels

                for label, field, channel in zip(labels, fields, channels):
                    row = column.row()
                    box = row.box()
                    row.label(icon='BLANK1')
                    
                    row = box.row(align=True)
                    row.label(icon=f'RADIOBUT_{"ON" if channel.is_enabled else "OFF"}',
                            text=f'{label or channel.name}')

                    row = row.row()
                    row.alignment = 'RIGHT'

                    if field == "angle":
                        row.label(text=f'{getattr(channel.data[pose_index], field):.2f}\N{DEGREE SIGN}')
                    else:
                        row.label(text=f'{getattr(channel.data[pose_index], field):.3f}')

                    column.separator(factor=0.5)


        # layout.separator()
        # labels, column = self.split_layout(layout)
        # labels.separator(factor=0.5)
        # labels.label(text="Outputs")

        # output: 'RBFDriverOutput'
        # for item_index, output in enumerate(outputs):
        #     subcolumn = column.column(align=True)
        #     row = subcolumn.box().row()
        #     row.prop(output, "ui_show_pose",
        #                 text="",
        #                 icon=f'DISCLOSURE_TRI_{"DOWN" if output.ui_show_pose else "RIGHT"}',
        #                 emboss=False)
        #     row.label(icon=OUTPUT_TYPE_ICONS[output.type], text=output.name)

        #     subrow = row.row()
        #     subrow.alignment = 'RIGHT'

        #     props = subrow.operator(RBFDRIVERS_OT_pose_update.bl_idname,
        #                             icon='IMPORT',
        #                             text="",
        #                             emboss=False)
        #     props.data_layer = 'OUTPUT'
        #     props.pose_index = pose_index
        #     props.item_index = item_index

        #     if output.ui_show_pose:
        #         box = subcolumn.box()
        #         labels, values, decorations = self.split_layout(box, factor=0.25, align=True, decorate_fill=False)

        #         type = output.type

        #         if type in {'LOCATION', 'SCALE'}:
        #             for channel in output.channels:
        #                 axis = channel.name
        #                 labels.label(text=f'{type.title() + " " if axis == "X" else ""}{axis}')
        #                 values.prop(channel.data[pose_index], "value", text="")
        #                 decorations.label(icon=f'DECORATE{"_KEYFRAME" if channel.is_enabled else ""}')

        #         elif type == 'ROTATION':
        #             channels = output.channels

        #             mode = output.rotation_mode
        #             if mode == 'EULER':
        #                 channels = channels[1:]
        #             elif mode == 'TWIST':
        #                 channels = channels['WXYZ'.index(output.rotation_axis)]
                    
        #             for index, channel in enumerate(channels):
        #                 axis = channel.name
        #                 labels.label(text=f'{"Rotation " if index == 0 else ""}{axis}')
        #                 values.prop(channel.data[pose_index], "value", text="")
        #                 decorations.label(icon=f'DECORATE{"_KEYFRAME" if channel.is_enabled else ""}')

        #         else:
        #             for channel in output.channels:
        #                 labels.label(text=channel.name)
        #                 values.prop(channel.data[pose_index], "value", text="")
        #                 decorations.label(icon=f'DECORATE{"_KEYFRAME" if channel.is_enabled else ""}')
                
