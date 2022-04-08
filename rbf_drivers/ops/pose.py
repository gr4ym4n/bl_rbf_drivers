
from typing import Set, TYPE_CHECKING
from bpy.types import Operator
from bpy.props import EnumProperty, IntProperty
if TYPE_CHECKING:
    from bpy.types import Context, Event, UIPopupMenu
    from ..api.poses import RBFDriverPoses
    from ..api.driver import RBFDriver


class RBFDRIVERS_OT_pose_display_settings(Operator):
    bl_idname = "rbf_driver.pose_display_settings"
    bl_label = "Display Settings"
    bl_description = "Modify pose display settings"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None)

    @staticmethod
    def draw_func(self, context: 'Context') -> None:
        poses = context.object.rbf_drivers.active.poses
        layout = self.layout
        layout.separator()

        split = layout.split(factor=0.3)
        
        row = split.row()
        row.alignment = 'RIGHT'
        row.label(text="Display")

        col = split.column()
        col.prop(poses, "display_radius")
        col.prop(poses, "display_influence")
        col.prop(poses, "display_weight")

        layout.separator()

    def execute(self, context: 'Context') -> Set[str]:

        def draw(*args) -> None:
            RBFDRIVERS_OT_pose_display_settings.draw_func(*args)

        context.window_manager.popover(draw, from_active_button=True)
        return {'FINISHED'}


class RBFDRIVERS_OT_pose_add(Operator):
    bl_idname = "rbf_driver.pose_add"
    bl_label = "Add Pose"
    bl_description = "Add an RBF driver pose"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None)

    def execute(self, context: 'Context') -> Set[str]:
        # TODO handle type for shape key drivers
        poses: 'RBFDriverPoses' = context.object.rbf_drivers.active.poses
        poses.new()
        return {'FINISHED'}


class RBFDRIVERS_OT_pose_remove(Operator):
    bl_idname = "rbf_driver.pose_remove"
    bl_label = "Remove Pose"
    bl_description = "Remove the selected RBF driver pose"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.poses.active is not None
                and object.rbf_drivers.active.poses.active_index > 0)

    def execute(self, context: 'Context') -> Set[str]:
        poses: 'RBFDriverPoses' = context.object.rbf_drivers.active.poses
        poses.remove(poses.active)
        return {'FINISHED'}


class RBFDRIVERS_OT_pose_update(Operator):
    bl_idname = "rbf_driver.pose_update"
    bl_label = "Update Pose"
    bl_description = "Update the selected RBF driver pose"
    bl_options = {'INTERNAL', 'UNDO'}

    layer: EnumProperty(
        items=[
            ('ALL'   , "All"   , ""),
            ('INPUT' , "Input" , ""),
            ('OUTPUT', "Output", ""),
            ],
        default='ALL',
        options=set()
        )

    index: IntProperty(
        name="Index",
        default=-1,
        options=set()
        )

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None)

    def execute(self, context: 'Context') -> Set[str]:
        driver: 'RBFDriver' = context.object.rbf_drivers.active

        index = self.index
        layer = self.layer

        if index < 0:
            pose = driver.poses.active
        else:
            if index >= len(driver.poses):
                self.report({'ERROR'}, f'Invalid pose index: {index}')
                return {'CANCELLED'}

            pose = driver.poses[index]

        if layer == 'ALL':
            inputs  = driver.inputs
            outputs = driver.outputs
        elif layer == 'INPUT':
            inputs  = driver.inputs
            outputs = tuple()
        else:
            inputs  = tuple()
            outputs = driver.outputs

        pose.update(inputs=inputs, outputs=outputs)
        return {'FINISHED'}


class RBFDRIVERS_OT_pose_data_update(Operator):
    bl_idname = "rbf_driver.pose_data_update"
    bl_label = "Update Pose Data"
    bl_description = "Update the selected RBF driver pose data"
    bl_options = {'INTERNAL', 'UNDO'}

    layer: EnumProperty(
        items=[
            ('ALL'   , "All"   , ""),
            ('INPUT' , "Input" , ""),
            ('OUTPUT', "Output", ""),
            ],
        default='ALL',
        options=set()
        )

    index: IntProperty(
        name="Index",
        default=0,
        options=set()
        )

    @staticmethod
    def draw_menu(menu: 'UIPopupMenu', context: 'Context', layer: str, index: int) -> None:
        layout = menu.layout
        props = layout.operator(RBFDRIVERS_OT_pose_update.bl_idname, text="Update From Target")
        props.layer = layer
        props.index = index

    def invoke(self, context: 'Context', event: 'Event') -> Set[str]:
        layer = self.layer
        index = self.index

        def draw_menu(menu: 'UIPopupMenu', context: 'Context'):
            RBFDRIVERS_OT_pose_data_update.draw_menu(menu, context, layer, index)

        context.window_manager.popup_menu(draw_menu)
        return self.execute(context)

    def execute(self, _: 'Context') -> Set[str]:
        return {'FINISHED'}


class RBFDRIVERS_OT_pose_move_up(Operator):

    bl_idname = "rbf_driver.pose_move_up"
    bl_label = "Move Pose Up"
    bl_description = "Move the selected RBF driver pose up within the list of poses"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.poses.active is not None
                and object.rbf_drivers.active.poses.active_index >= 1)

    def execute(self, context: 'Context') -> Set[str]:
        poses: 'RBFDriverPoses' = context.object.rbf_drivers.active.poses
        poses.move(poses.active_index, poses.active_index - 1)
        return {'FINISHED'}


class RBFDRIVERS_OT_pose_move_down(Operator):

    bl_idname = "rbf_driver.pose_move_down"
    bl_label = "Move Pose Down"
    bl_description = "Move the selected RBF driver pose down within the list of poses"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.poses.active is not None
                and object.rbf_drivers.active.poses.active_index < len(object.rbf_drivers.active.poses) - 1)

    def execute(self, context: 'Context') -> Set[str]:
        poses: 'RBFDriverPoses' = context.object.rbf_drivers.active.poses
        poses.move(poses.active_index, poses.active_index + 1)
        return {'FINISHED'}
