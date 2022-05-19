
from typing import TYPE_CHECKING, Sequence, TypeVar
from bpy.types import Menu, Panel, UIList
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
    from ..api.input_variable import RBFDriverInputVariable
    from ..api.input import RBFDriverInput
    from ..api.output_channel import RBFDriverOutputChannel
    from ..api.output import RBFDriverOutput
    from ..api.pose import RBFDriverPose
    from ..api.driver import RBFDriver

IOLayer = TypeVar("IOLayer", 'RBFDriverInput', 'RBFDriverOutput')
IOChannel = TypeVar("IOChannel", 'RBFDriverInputVariable', 'RBFDriverOutputChannel')


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

    def draw_header(self, _: 'Context') -> None:
        self.layout.label(icon='CON_ARMATURE')

    def draw(self, context: 'Context') -> None:
        driver = context.object.rbf_drivers.active
        poses = driver.poses
        layout = self.subpanel(self.layout)
        layout.separator(factor=0.5)

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
        row.prop(interpolation, "use_curve", text="Override")
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
            self.draw_value_sets(layout, 'INPUT', inputs, pose_index)

        outputs = driver.outputs
        if len(outputs):
            self.draw_value_sets(layout, 'OUTPUT', outputs, pose_index)

    def draw_value_sets(self, layout: 'UILayout', data_layer: str, layers: Sequence[IOLayer], pose_index: int) -> None:
        layout.separator()
        labels, region = self.split_layout(layout, align=True, decorate=False)
        labels.separator(factor=1/3)
        labels.label(text=f'{data_layer.title()}s')

        layer: IOLayer
        for item_index, layer in enumerate(layers):
            section = region.row()
            content = section.column(align=True)
            
            subcol = section.column(align=True)
            subcol.separator(factor=0.25)

            props = subcol.operator(RBFDRIVERS_OT_pose_update.bl_idname, icon='TRACKING_BACKWARDS', text="")
            props.data_layer = data_layer
            props.pose_index = pose_index
            props.item_index = item_index

            header = content.column(align=True)
            header.scale_y = 0.75

            header = header.box().row(align=True)
            header.prop(layer, "ui_show_pose",
                        text="",
                        icon=f'{"DOWNARROW_HLT" if layer.ui_show_pose else "RIGHTARROW"}',
                        emboss=False)
            header.label(text=layer.name)

            if (layer.has_symmetry_target
                and layer.type in {'LOCATION', 'ROTATION'}
                and layer.use_mirror_x
                ):
                subrow = header.row()
                subrow.alignment = 'RIGHT'
                subrow.label(icon='MOD_MIRROR')

            if layer.ui_show_pose:
                type = layer.type
                channels = layer.channels if data_layer == 'OUTPUT' else layer.variables
                fields = ["value"] * len(channels)

                if type in {'LOCATION', 'SCALE'}:
                    labels = 'XYZ'
                elif type == 'ROTATION':
                    mode = layer.rotation_mode
                    if mode == 'EULER':
                        labels = 'XYZ'
                        fields = ["angle"] * 4
                        channels = channels[1:]
                    else:
                        labels = 'WXYZ'
                        if mode == 'AXIS_ANGLE':
                            fields[0] = "angle"
                elif type == 'ROTATION_DIFF':
                    labels = ["Difference"]
                    fields[0] = "angle"
                elif type == 'LOC_DIFF':
                    labels = ["Distance"]
                elif type == 'SHAPE_KEY':
                    labels = [channel.name or "?" for channel in channels]
                else:
                    labels = [channel.name or channel.data_path or "?" for channel in channels]

                box = content.box()
                subcol = box.column(align=True)
                subcol.separator()

                for label, field, channel in zip(labels, fields, channels):
                    row = subcol.row(align=True)
                    row.label(icon=f'RADIOBUT_{"ON" if channel.is_enabled else "OFF"}')
                    row.separator()
                    row.prop(channel.data[pose_index], field, text=label)
                    row.separator()

                subcol.separator()
            region.separator()
