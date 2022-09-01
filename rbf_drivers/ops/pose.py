
from typing import Set, TYPE_CHECKING
from bpy.types import Operator
from bpy.props import EnumProperty, IntProperty
if TYPE_CHECKING:
    from bpy.types import Context
    from ..api.poses import Poses
    from ..api.driver import RBFDriver


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
        poses: 'Poses' = context.object.rbf_drivers.active.poses
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
        poses: 'Poses' = context.object.rbf_drivers.active.poses
        poses.remove(poses.active)
        return {'FINISHED'}


class RBFDRIVERS_OT_pose_update(Operator):
    bl_idname = "rbf_driver.pose_update"
    bl_label = "Update Pose"
    bl_description = "Update the selected RBF driver pose"
    bl_options = {'INTERNAL', 'UNDO'}

    data_layer: EnumProperty(
        items=[
            ('ALL'   , "All"   , ""),
            ('INPUT' , "Input" , ""),
            ('OUTPUT', "Output", ""),
            ],
        default='ALL',
        options=set()
        )

    pose_index: IntProperty(
        name="Pose",
        default=-1,
        options=set()
        )

    item_index: IntProperty(
        name="Item",
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

        pose_index = self.pose_index
        item_index = self.item_index
        data_layer = self.data_layer

        if pose_index < 0:
            pose = driver.poses.active
        else:
            if pose_index >= len(driver.poses):
                self.report({'ERROR'}, f'Invalid pose index: {pose_index}')
                return {'CANCELLED'}

            pose = driver.poses[pose_index]

        if data_layer == 'ALL':
            inputs  = driver.inputs
            outputs = driver.outputs
        elif data_layer == 'INPUT':
            inputs  = driver.inputs
            outputs = tuple()
        else:
            inputs  = tuple()
            outputs = driver.outputs

        if item_index >= 0:
            if inputs:
                if item_index >= len(inputs):
                    self.report({'ERROR'}, f'Invalid item index {item_index}')
                    return {'CANCELLED'}
                inputs = (inputs[item_index],)

            if outputs:
                if item_index >= len(outputs):
                    self.report({'ERROR'}, f'Invalid item index {item_index}')
                    return {'CANCELLED'}
                outputs = (outputs[item_index],)

        pose.update(inputs=inputs, outputs=outputs)
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
        poses: 'Poses' = context.object.rbf_drivers.active.poses
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
        poses: 'Poses' = context.object.rbf_drivers.active.poses
        poses.move(poses.active_index, poses.active_index + 1)
        return {'FINISHED'}
