
from typing import TYPE_CHECKING
from bpy.types import Menu, Panel, UIList
from rbf_drivers.gui.outputs import output_draw_path
from .drivers import RBFDRIVERS_PT_drivers
from .utils import idprop_data_render, layout_split, pose_weight_render
from ..lib.curve_mapping import draw_curve_manager_ui
from ..ops.pose import (RBFDRIVERS_OT_pose_add, RBFDRIVERS_OT_pose_display_settings,
                        RBFDRIVERS_OT_pose_remove,
                        RBFDRIVERS_OT_pose_update,
                        RBFDRIVERS_OT_pose_data_update,
                        RBFDRIVERS_OT_pose_move_up,
                        RBFDRIVERS_OT_pose_move_down)
if TYPE_CHECKING:
    from bpy.types import Context, UILayout
    from ..api.pose_data import RBFDriverPoseData, RBFDriverPoseDataGroup, RBFDriverPoseDatum
    from ..api.pose_interpolation import RBFDriverPoseInterpolation
    from ..api.driver import RBFDriver


LI_SPLIT = 0.5

def draw_active_pose_data(layout: 'UILayout', data: 'RBFDriverPoseData', layer: str) -> None:
    group: 'RBFDriverPoseDataGroup'
    datum: 'RBFDriverPoseDatum'

    for index, group in enumerate(data):
        split = layout.row().split(factor=1/3)
        
        row = split.row()
        row.alignment = 'RIGHT'
        row.label(text=group.name)

        labels, values, decorations = layout_split(split.column(),
                                                   align=True,
                                                   decorate_fill=False)
        for datum in group:
            labels.label(text=datum.name)
            values.prop(datum, datum.type.lower(), text="")
        
        props = decorations.operator(RBFDRIVERS_OT_pose_data_update.bl_idname,
                                     text="",
                                     icon='DOWNARROW_HLT')
        props.layer = layer
        props.index = index





class RBFDRIVERS_UL_poses(UIList):
    bl_idname = 'RBFDRIVERS_UL_poses'

    def draw_item(self, context, layout, _1, pose, icon, active_data, _2, index, _3) -> None:
        driver = context.object.rbf_drivers.active

        if driver is not None and driver.type == 'SHAPE_KEYS':
            icon = 'SHAPEKEY_DATA'
        else:
            icon = 'POSE_HLT'

        spl = layout.split(factor=LI_SPLIT)

        spl.row().prop(pose, "name",
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
                row = spl.row(align=True)
                idprop_data_render(row, pose.radius   , text="")
                idprop_data_render(row, pose.influence, text="", slider=True)
                idprop_data_render(row, pose.weight   , text="", index=index)


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
            props = layout.operator(RBFDRIVERS_OT_pose_update.bl_idname, text=label)
            props.layer = layer
            props.index = -1


class RBFDRIVERS_PT_poses(Panel):

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
        layout = self.layout
        offset = layout.row()
        header = offset.row()
        offset.operator(RBFDRIVERS_OT_pose_display_settings.bl_idname,
                        icon='PRESET',
                        text="",
                        emboss=False)

        poses = driver.poses

        head = []
        if poses.display_radius    : head.append("radius")
        if poses.display_influence : head.append("influence")
        if poses.display_weight    : head.append("weight")

        if head:
            split = header.split(factor=1.0 - 0.15 * len(head))
            split.label(icon='BLANK1')

            row = split.row(align=True)
            for item in head:
                col = row.column()
                col.alignment = 'CENTER'
                col.label(text=item.title())

        row = layout.row()
        col = row.column()
        col.template_list(RBFDRIVERS_UL_poses.bl_idname, "",
                          poses, "collection__internal__", poses, "active_index")

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
            layout.separator(factor=0.5)

            labels, values = layout_split(layout)
            labels.label(text="Radius")
            idprop_data_render(values, pose.radius, text="")
            labels.label(text="Influence")
            idprop_data_render(values, pose.influence, text="", slider=True)
            labels.label(text="Weight")
            idprop_data_render(values, pose.weight, text="", index=poses.active_index)

            layout.separator(factor=0.5)

            col = layout_split(layout, "Interpolation")
            col.row(align=True).prop(pose, "interpolation_curve", expand=True)

            col = layout_split(layout, " ", decorate=False)
            src = driver if pose.interpolation_curve == 'DEFAULT' else pose
            draw_curve_manager_ui(col, src.interpolation)

            outputs = driver.outputs

            col = layout.column(align=True)
            for index, output in enumerate(outputs):
                labels, values, decorations = layout_split(col, align=True, decorate_fill=False)

                labels.separator(factor=0.5)
                labels = labels.row(align=True)
                labels.alignment = 'RIGHT'

                if index == 0:
                    labels.label(text="Output Values")

                icon = 'DOWNARROW_HLT' if output.ui_show_pose else 'RIGHTARROW'
                labels.prop(output, "ui_show_pose", text="", icon=icon, emboss=False)

                row = values.box().row()
                if outputs.display_mode == 'PATH':
                    output_draw_path(row, output)
                else:
                    row.label(text=output.name)

                if not output.ui_show_pose:
                    row.row()
                else:
                    box = values.box()
                    box.separator(factor=0.5)

                    pose_index = poses.active_index
                    lbls, vals, decs = layout_split(box, factor=0.5, align=True, decorate_fill=False)

                    type = output.type
                    if type in {'LOCATION', 'SCALE'}:
                        for channel in output.channels:
                            axis = channel.name
                            lbls.label(text=f'{type.title() + " " if axis == "X" else ""}{axis}')
                            vals.prop(channel.data[pose_index], "value", text="")
                            decs.label(icon=f'DECORATE{"_DRIVER" if channel.is_enabled else ""}')

                    elif type == 'ROTATION':
                        mode = output.rotation_mode
                        if mode == 'EULER':
                            for channel in output.channels[1:]:
                                axis = channel.name
                                lbls.label(text=f'{"Rotation " if axis == "X" else ""}{axis}')
                                vals.prop(channel.data[pose_index], "value", text="")
                                decs.label(icon=f'DECORATE{"_DRIVER" if channel.is_enabled else ""}')

                        elif mode == 'AXIS_ANGLE':
                            for channel in output.channels:
                                if channel.name == 'W':
                                    prop = "angle"
                                    labels.label(text="Rotation W")
                                else:
                                    prop = "value"
                                    labels.label(text=channel.name)
                                vals.prop(channel.data[pose_index], prop, text="")
                                decs.label(icon=f'DECORATE{"_DRIVER" if channel.is_enabled else ""}')

                        else:# mode == QUATERNION
                            for channel in output.channels:
                                axis = channel.name
                                lbls.label(text=f'{"Rotation " if axis == "W" else ""}{axis}')
                                vals.prop(channel.data[pose_index], "value", text="")
                                decs.label(icon=f'DECORATE{"_DRIVER" if channel.is_enabled else ""}')

                    box.separator(factor=0.5)


                decorations.separator(factor=0.5)
                props = decorations.operator(RBFDRIVERS_OT_pose_data_update.bl_idname,
                                             text="",
                                             icon='DOWNARROW_HLT')
                props.layer = 'INPUT'
                props.index = index





class RBFDRIVERS_PT_pose_input_values(Panel):

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_pose_input_values'
    bl_parent_id = RBFDRIVERS_PT_poses.bl_idname
    bl_description = "RBF driver pose input values"
    bl_label = "Input Values"

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.poses.active is not None)

    def draw(self, context: 'Context') -> None:
        layout = self.layout
        driver = context.object.rbf_drivers.active
        draw_active_pose_data(layout, driver.inputs.active_pose_data, 'INPUT')


class RBFDRIVERS_PT_pose_output_values(Panel):

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_idname = 'RBFDRIVERS_PT_pose_output_values'
    bl_parent_id = RBFDRIVERS_PT_poses.bl_idname
    bl_description = "RBF driver pose output values"
    bl_label = "Output Values"

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.poses.active is not None)

    def draw(self, context: 'Context') -> None:
        layout = self.layout
        driver = context.object.rbf_drivers.active

        pose_index = driver.poses.active_index
        outputs = driver.outputs
        display_mode = outputs.display_mode

        for index, output in enumerate(outputs):
            row = layout.row()
            row.alignment = 'RIGHT'

            if display_mode == 'PATH':
                output_draw_path(row, output)
            else:
                row.label(text=output.name)

            op = row.operator(RBFDRIVERS_OT_pose_data_update.bl_idname, text="", icon='DOWNARROW_HLT')
            op.layer = 'OUTPUT'
            op.index = index

            labels, values, decorations = layout_split(layout, align=True, decorate_fill=False)

            type = output.type
            if type in {'LOCATION', 'SCALE'}:
                for channel in output.channels:
                    axis = channel.name
                    labels.label(text=f'{type.title() + " " if axis == "X" else ""}{axis}')
                    values.prop(channel.data[pose_index], "value", text="")
                    decorations.label(icon=f'DECORATE{"_DRIVER" if channel.is_enabled else ""}')

            elif type == 'ROTATION':
                mode = output.rotation_mode
                if mode == 'EULER':
                    for channel in output.channels[1:]:
                        axis = channel.name
                        labels.label(text=f'{"Rotation " if axis == "X" else ""}{axis}')
                        values.prop(channel.data[pose_index], "value", text="")
                        decorations.label(icon=f'DECORATE{"_DRIVER" if channel.is_enabled else ""}')

                elif mode == 'AXIS_ANGLE':
                    for channel in output.channels:
                        if channel.name == 'W':
                            prop = "angle"
                            labels.label(text="Rotation W")
                        else:
                            prop = "value"
                            labels.label(text=channel.name)
                        values.prop(channel.data[pose_index], prop, text="")
                        decorations.label(icon=f'DECORATE{"_DRIVER" if channel.is_enabled else ""}')

                else:# mode == QUATERNION
                    for channel in output.channels:
                        axis = channel.name
                        labels.label(text=f'{"Rotation " if axis == "W" else ""}{axis}')
                        values.prop(channel.data[pose_index], "value", text="")
                        decorations.label(icon=f'DECORATE{"_DRIVER" if channel.is_enabled else ""}')

            # TODO other output types
            # box.separator()