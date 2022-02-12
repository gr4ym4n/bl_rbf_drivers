
import typing
import bpy
from rbf_drivers.driver import DRIVER_TYPE_INDEX, DRIVER_TYPE_ITEMS
from rbf_drivers.lib.driver_utils import driver_find
from rbf_drivers.output import OUTPUT_CHANNEL_DEFINITIONS, output_drivers_remove, output_idprops_remove, output_influence_idprop_create, output_influence_idprop_remove, output_logmap_idprops_remove, output_pose_data_idprops_remove, output_pose_data_idprops_update, output_uses_logmap
from .lib.curve_mapping import nodetree_node_remove, nodetree_node_update

from .mixins import ID_TYPE_INDEX, LAYER_TYPE_ITEMS, LAYER_TYPE_INDEX

from .input import (INPUT_VARIABLE_DEFINITIONS,
                    input_influence_idprop_create,
                    input_influence_idprop_remove,
                    input_influence_idprop_remove_all,
                    input_influence_sum_driver_remove,
                    input_influence_sum_driver_update,
                    input_influence_sum_idprop_ensure,
                    input_influence_sum_idprop_remove,
                    input_pose_distance_driver_remove,
                    input_pose_distance_driver_remove_all, input_pose_distance_driver_update, input_pose_distance_fcurve_update,
                    input_pose_distance_idprop_remove,
                    input_pose_distance_idprop_update)

from .pose import (pose_distance_sum_driver_remove_all,
                   pose_distance_sum_driver_update_all,
                   pose_distance_sum_idprop_remove,
                   pose_distance_sum_idprop_update,
                   pose_weight_driver_remove_all,
                   pose_weight_driver_update_all,
                   pose_weight_fcurve_update_all,
                   pose_weight_idprop_remove,
                   pose_weight_idprop_update)


class ShapeKeyTarget(bpy.types.PropertyGroup):
    pass


class RBFDRIVERS_OT_new(bpy.types.Operator):
    bl_idname = "rbf_driver.add"
    bl_label = "Add Driver"
    bl_description = "Create a new RBF driver"
    bl_options = {'INTERNAL', 'UNDO'}

    type: bpy.props.EnumProperty(
        items=DRIVER_TYPE_ITEMS,
        default='NONE',
        options=set()
        )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return object is not None and object.type != 'EMPTY'

    def execute(self, context: bpy.types.Context) -> typing.Set[str]:
        object = context.object
        type = self.type

        if type == 'OBJECT' and object.type != 'MESH':
            self.report({'ERROR'}, "Shape Keys RBF driver requires a mesh object")
            return {'CANCELLED'}

        drivers = object.rbf_drivers

        names = [driver.name for driver in drivers]
        index = 0
        name = "RBFDriver"
        while name in names:
            index += 1
            name = f'RBFDrivers.{str(index).zfill(3)}'

        driver = drivers.collection__internal__.add()
        driver["name"] = name
        driver["type"] = DRIVER_TYPE_INDEX[type]
        driver.falloff.__init__()

        poses = driver.poses
        rest_pose = poses.collection__internal__.add()
        rest_pose.falloff.__init__()

        shapekeys = type == 'SHAPE_KEYS'

        if not shapekeys:
            rest_pose["name"] = "Rest"
        else:
            key = object.data.shape_keys
            if key is None:
                shape = object.shape_key_add(name="Basis", from_mix=False)
            else:
                shape = key.reference_key
            rest_pose["name"] = shape.name

        driver.update()
        drivers.active_index = len(drivers)-1
        return {'FINISHED'}

class RBFDRIVERS_OT_remove(bpy.types.Operator):
    bl_idname = "rbf_driver.remove"
    bl_label = "Remove Driver"
    bl_description = "Remove the selected RBF driver"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None)

    def execute(self, context: bpy.types.Context) -> typing.Set[str]:
        drivers = context.object.rbf_drivers
        driver = drivers.active
        
        poses = driver.poses
        shape_keys = driver.type == 'SHAPE_KEYS'

        pose_weight_driver_remove_all(poses, shape_keys)
        pose_weight_idprop_remove(poses)
        pose_distance_sum_driver_remove_all(poses)
        pose_distance_sum_idprop_remove(poses)

        for pose in poses:
            nodetree_node_remove(pose.falloff.curve.node_identifier)

        inputs = driver.inputs

        input_influence_sum_driver_remove(inputs)
        input_influence_sum_idprop_remove(inputs)
        input_influence_idprop_remove_all(inputs)

        for input in inputs:
            input_pose_distance_driver_remove_all(input)
            input_pose_distance_idprop_remove(input)

        for output in driver.outputs:
            output_drivers_remove(output)
            output_idprops_remove(output)

        nodetree_node_update(driver.falloff.curve.node_identifier)

        drivers.collection__internal__.remove(drivers.active_index)
        drivers.active_index = max(len(drivers)-1, drivers.active_index)
        return{'FINISHED'}

class RBFDRIVERS_OT_move_up(bpy.types.Operator):

    bl_idname = "rbf_driver.move_up"
    bl_label = "Move Driver Up"
    bl_description = "Move the selected RBF driver up within the list of drivers"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active_index >= 1)

    def execute(self, context: bpy.types.Context) -> typing.Set[str]:
        drivers = context.object.rbf_drivers
        drivers.collection__internal__.move(drivers.active_index, drivers.active_index - 1)
        drivers.active_index -= 1
        return {'FINISHED'}

class RBFDRIVERS_OT_move_down(bpy.types.Operator):

    bl_idname = "rbf_driver.move_down"
    bl_label = "Move Driver Down"
    bl_description = "Move the selected RBF driver down within the list of drivers"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active_index < len(object.rbf_drivers) - 1)

    def execute(self, context: bpy.types.Context) -> typing.Set[str]:
        drivers = context.object.rbf_drivers
        drivers.collection__internal__.move(drivers.active_index, drivers.active_index + 1)
        drivers.active_index += 1
        return {'FINISHED'}

class RBFDRIVERS_OT_input_add(bpy.types.Operator):
    bl_idname = "rbf_driver.input_add"
    bl_label = "Add Input"
    bl_description = "Add an RBF driver input"
    bl_options = {'INTERNAL', 'UNDO'}

    type: bpy.props.EnumProperty(
        name="Type",
        items=LAYER_TYPE_ITEMS,
        default=LAYER_TYPE_ITEMS[0][0],
        options=set()
        )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None)

    def execute(self, context: bpy.types.Context) -> typing.Set[str]:
        driver = context.object.rbf_drivers.active
        inputs = driver.inputs

        names = [input.name for input in inputs]
        index = 0
        name = "Input"
        while name in names:
            index += 1
            name = f'Input.{str(index).zfill(3)}'

        input = inputs.collection__internal__.add()
        input["name"] = name
        input["type"] = LAYER_TYPE_INDEX[self.type]

        for defn in INPUT_VARIABLE_DEFINITIONS[self.type]:
            data = input.variables.collection__internal__.add()
            defn = defn.copy()
            tgts = defn.pop("targets", [{}])

            for key, value in defn.items():
                data[key] = value

            data.targets["size__internal__ "] = len(tgts)

            for spec in tgts:
                item = data.targets.data__internal__.add()
                for key, value in spec.items():
                    item[key] = value

        poses = driver.poses
        pose_count = len(poses)

        for var in input.variables:
            val = var.default
            for _ in range(pose_count):
                var.data.data__internal__.add()["value"] = val

        input_influence_idprop_create(input)
        input_pose_distance_idprop_update(input, pose_count)

        input_influence_sum_idprop_ensure(inputs)
        input_influence_sum_driver_update(inputs)

        pose_distance_sum_driver_update_all(poses, inputs)

        inputs.active_index = len(inputs)-1
        return {'FINISHED'}

class RBFDRIVERS_OT_input_remove(bpy.types.Operator):
    bl_idname = "rbf_driver.input_remove"
    bl_label = "Remove Input"
    bl_description = "Remove the selected RBF driver input"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.inputs.active is not None)

    def execute(self, context: bpy.types.Context) -> typing.Set[str]:
        driver = context.object.rbf_drivers.active
        inputs = driver.inputs

        input = inputs.active
        input_pose_distance_driver_remove_all(input)
        input_pose_distance_idprop_remove(input)

        input_influence_idprop_remove(input)
        input_influence_sum_driver_update(inputs)

        inputs.collection__internal__.remove(inputs.active_index)
        inputs.active_index = max(len(inputs)-1, inputs.active_index)

        poses = driver.poses
        pose_distance_sum_driver_update_all(poses, inputs)
        pose_weight_driver_update_all(poses, inputs)

        return {'FINISHED'}

class RBFDRIVERS_OT_input_move_up(bpy.types.Operator):

    bl_idname = "rbf_driver.input_move_up"
    bl_label = "Move Input Up"
    bl_description = "Move the selected RBF driver input up within the list of inputs"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.inputs.active is not None
                and object.rbf_drivers.active.inputs.active_index >= 1)

    def execute(self, context: bpy.types.Context) -> typing.Set[str]:
        driver = context.object.rbf_drivers.active
        inputs = driver.inputs

        inputs.collection__internal__.move(inputs.active_index, inputs.active_index - 1)
        inputs.active_index -= 1

        input_influence_sum_driver_update(inputs)
        pose_distance_sum_driver_update_all(driver.poses, inputs)

        return {'FINISHED'}

class RBFDRIVERS_OT_input_move_down(bpy.types.Operator):

    bl_idname = "rbf_driver.input_move_down"
    bl_label = "Move Input Down"
    bl_description = "Move the selected RBF driver input down within the list of inputs"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.inputs.active is not None
                and object.rbf_drivers.active.inputs.active_index < len(object.rbf_drivers.active.inputs) - 1)

    def execute(self, context: bpy.types.Context) -> typing.Set[str]:
        driver = context.object.rbf_drivers.active
        inputs = driver.inputs

        inputs.collection__internal__.move(inputs.active_index, inputs.active_index + 1)
        inputs.active_index += 1

        input_influence_sum_driver_update(inputs)
        pose_distance_sum_driver_update_all(driver.poses, inputs)

        return {'FINISHED'}

class RBFDRIVERS_OT_output_add(bpy.types.Operator):
    bl_idname = "rbf_driver.output_add"
    bl_label = "Add Output"
    bl_description = "Add an RBF driver output"
    bl_options = {'INTERNAL', 'UNDO'}

    type: bpy.props.EnumProperty(
        name="Type",
        items=LAYER_TYPE_ITEMS,
        default=LAYER_TYPE_ITEMS[0][0],
        options=set()
        )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.type != 'SHAPE_KEYS')

    def execute(self, context: bpy.types.Context) -> typing.Set[str]:
        driver = context.object.rbf_drivers.active
        outputs = driver.outputs

        names = [output.name for output in outputs]
        index = 0
        name = "Output"
        while name in names:
            index += 1
            name = f'Output.{str(index).zfill(3)}'

        output = outputs.collection__internal__.add()
        output["name"] = name
        output["type"] = LAYER_TYPE_INDEX[self.type]

        for channel_spec in OUTPUT_CHANNEL_DEFINITIONS[self.type]:
            channel = output.channels.collection__internal__.add()
            for key, value in channel_spec.items():
                channel[key] = value

        poses = driver.poses
        pose_count = len(poses)

        for channel in output.channels:
            default = channel.default
            for _ in range(pose_count):
                channel.data.data__internal__.add()["value"] = default

        output_influence_idprop_create(output)
        output_pose_data_idprops_update(output)

        outputs.active_index = len(outputs) - 1
        return {'FINISHED'}

class RBFDRIVERS_OT_output_remove(bpy.types.Operator):
    bl_idname = "rbf_driver.output_remove"
    bl_label = "Remove Output"
    bl_description = "Remove the selected RBF driver output"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.outputs.active is not None)

    def execute(self, context: bpy.types.Context) -> typing.Set[str]:
        driver = context.object.rbf_drivers.active
        outputs = driver.outputs

        output = outputs.active
        output_drivers_remove(output)
        output_idprops_remove(output)

        outputs.collection__internal__.remove(outputs.active_index)
        outputs.active_index = max(len(outputs)-1, outputs.active_index)

        return {'FINISHED'}

class RBFDRIVERS_OT_output_move_up(bpy.types.Operator):

    bl_idname = "rbf_driver.output_move_up"
    bl_label = "Move Output Up"
    bl_description = "Move the selected RBF driver output up within the list of output"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.outputs.active is not None
                and object.rbf_drivers.active.outputs.active_index >= 1)

    def execute(self, context: bpy.types.Context) -> typing.Set[str]:
        driver = context.object.rbf_drivers.active
        outputs = driver.outputs

        outputs.collection__internal__.move(outputs.active_index, outputs.active_index - 1)
        outputs.active_index -= 1

        return {'FINISHED'}

class RBFDRIVERS_OT_output_move_down(bpy.types.Operator):

    bl_idname = "rbf_driver.output_move_down"
    bl_label = "Move Output Down"
    bl_description = "Move the selected RBF driver output down within the list of outputs"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.outputs.active is not None
                and object.rbf_drivers.active.outputs.active_index < len(object.rbf_drivers.active.outputs) - 1)

    def execute(self, context: bpy.types.Context) -> typing.Set[str]:
        driver = context.object.rbf_drivers.active
        outputs = driver.outputs

        outputs.collection__internal__.move(outputs.active_index, outputs.active_index + 1)
        outputs.active_index += 1

        return {'FINISHED'}

class RBFDRIVERS_OT_pose_add(bpy.types.Operator):
    bl_idname = "rbf_driver.pose_add"
    bl_label = "Add Pose"
    bl_description = "Add an RBF driver pose"
    bl_options = {'INTERNAL', 'UNDO'}

    shapes: bpy.props.CollectionProperty(
        type=ShapeKeyTarget,
        options=set()
        )

    shape_target: bpy.props.StringProperty(
        name="Shape Key",
        default="",
        options=set()
        )

    type: bpy.props.EnumProperty(
        name="Add Pose",
        items=[
            ('NEW', "New Shape Key", "Create a new pose and shape key"),
            ('USE', "Use Existing Shape Key", "Create a new pose for an existing shape key"),
            ],
        default='NEW',
        options=set()
        )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None)

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> typing.Set[str]:
        object = context.object

        if (object.type == 'MESH'
            and object.rbf_drivers.active.type == 'SHAPE_KEYS'
            and self.type == 'USE'
            ):
            self.shape_target = ""

            shapes = self.shapes
            shapes.clear()

            key = object.data.shape_keys
            if key:
                ref = key.reference_key
                for shape in key.key_blocks:
                    if (shape != ref
                        and not driver_find(key, f'key_blocks["{shape.name}"].value')
                        ):
                        shapes.add().name = shape.name

            return context.window_manager.invoke_props_dialog(self)
    
        return self.execute(context)

    def draw(self, context: bpy.types.Context) -> None:
        self.layout.prop_search(self, "shape_target", self, "shapes", icon='SHAPEKEY_DATA')

    def execute(self, context: bpy.types.Context) -> typing.Set[str]:
        object = context.object
        driver = object.rbf_drivers.active
        poses = driver.poses

        pose = poses.collection__internal__.add()
        pose.falloff.__init__()

        if object.type == 'MESH' and driver.type == 'SHAPE_KEYS':

            shape = None
            if self.type == 'USE':
                key = object.data.shape_keys
                if key:
                    shape = key.key_blocks.get(self.shape_target)
            if shape is None:
                shape = object.shape_key_add(from_mix=False)

            pose["name"] = shape.name
        else:
            names = [pose.name for pose in poses]
            index = 0
            name = "Pose"
            while name in names:
                index += 1
                name = f'Pose.{str(index).zfill(3)}'

            pose["name"] = name

            for output in driver.outputs:
                for channel in output.channels:
                    channel.data.data__internal__.add()["value"] = channel.value

        # Append variable data state
        for input in driver.inputs:
            for variable in input.variables:
                variable.data.data__internal__.add()["value"] = variable.value

        # Rebuild driver
        driver.update()

        # Select the pose
        poses.active_index = len(poses)-1

        return {'FINISHED'}

class RBFDRIVERS_OT_pose_remove(bpy.types.Operator):
    bl_idname = "rbf_driver.pose_remove"
    bl_label = "Remove Pose"
    bl_description = "Remove the selected RBF driver pose"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.poses.active is not None
                and object.rbf_drivers.active.poses.active_index > 0)

    def execute(self, context: bpy.types.Context) -> typing.Set[str]:
        driver = context.object.rbf_drivers.active
        poses = driver.poses
        index = poses.active_index
        final_index = len(poses) - 1

        for input in driver.inputs:
            input_pose_distance_driver_remove(input, final_index)
            for variable in input.variables:
                variable.data.data__internal__.remove(index)
        
        for output in driver.outputs:
            for channel in output.channels:
                channel.data.data__internal__.remove(index)

        nodetree_node_remove(poses.active.falloff.curve.node_identifier)
        poses.collection__internal__.remove(index)
        poses.active_index = max(len(poses)-1, index)
        driver.update()

        return {'FINISHED'}

class RBFDRIVERS_OT_pose_move_up(bpy.types.Operator):

    bl_idname = "rbf_driver.pose_move_up"
    bl_label = "Move Pose Up"
    bl_description = "Move the selected RBF driver pose up within the list of poses"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.poses.active is not None
                and object.rbf_drivers.active.poses.active_index >= 1)

    def execute(self, context: bpy.types.Context) -> typing.Set[str]:
        driver = context.object.rbf_drivers.active
        poses = driver.poses
        index = poses.active_index

        poses.collection__internal__.move(poses.active_index, poses.active_index - 1)
        poses.active_index -= 1

        for input in driver.inputs:
            input.pose_radii.data__internal__.move(index, index - 1)

            for variable in input.variables:
                variable.data.data__internal__.move(index, index - 1)

            input_pose_distance_driver_update(input, index)
            input_pose_distance_driver_update(input, index - 1)

            input_pose_distance_fcurve_update(input, index)
            input_pose_distance_fcurve_update(input, index - 1)

        for output in driver.outputs:
            for channel in output.channels:
                channel.data.data__internal__.move(index, index - 1)
            output.update()

        return {'FINISHED'}
    
class RBFDRIVERS_OT_pose_move_down(bpy.types.Operator):

    bl_idname = "rbf_driver.pose_move_down"
    bl_label = "Move Pose Down"
    bl_description = "Move the selected RBF driver pose down within the list of poses"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.poses.active is not None
                and object.rbf_drivers.active.poses.active_index < len(object.rbf_drivers.active.poses) - 1)

    def execute(self, context: bpy.types.Context) -> typing.Set[str]:
        driver = context.object.rbf_drivers.active
        poses = driver.poses
        index = poses.active_index

        poses.collection__internal__.move(poses.active_index, poses.active_index + 1)
        poses.active_index += 1

        for input in driver.inputs:
            input.pose_radii.data__internal__.move(index, index + 1)

            for variable in input.variables:
                variable.data.data__internal__.move(index, index + 1)

            input_pose_distance_driver_update(input, index)
            input_pose_distance_driver_update(input, index + 1)

            input_pose_distance_fcurve_update(input, index)
            input_pose_distance_fcurve_update(input, index + 1)

        for output in driver.outputs:
            for channel in output.channels:
                channel.data.data__internal__.move(index, index + 1)
            output.update()

        return {'FINISHED'}