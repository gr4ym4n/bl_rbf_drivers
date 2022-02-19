
from re import S
import typing
import logging
import bpy
from rbf_drivers.driver import DRIVER_TYPE_INDEX, DRIVER_TYPE_ITEMS, RBFDriver
from rbf_drivers.lib.driver_utils import driver_find
from rbf_drivers.lib.symmetry import symmetrical_target
from rbf_drivers.output import OUTPUT_CHANNEL_DEFINITIONS, RBFDriverOutput, RBFDriverOutputs, output_drivers_remove, output_drivers_update, output_idprops_remove, output_idprops_update, output_influence_idprop_create, output_influence_idprop_remove, output_logmap_idprops_remove, output_pose_data_append, output_pose_data_idprops_remove, output_pose_data_idprops_update, output_pose_data_remove, output_pose_data_update, output_symmetry_assign, output_uses_logmap
from .lib.curve_mapping import nodetree_node_remove, nodetree_node_update

from .mixins import LAYER_TYPE_ITEMS, LAYER_TYPE_INDEX

from .input import (INPUT_VARIABLE_DEFINITIONS, RBFDriverInput, RBFDriverInputs,
                    input_influence_idprop_create,
                    input_influence_idprop_remove,
                    input_influence_idprop_remove_all,
                    input_influence_sum_driver_remove,
                    input_influence_sum_driver_update,
                    input_influence_sum_idprop_ensure,
                    input_influence_sum_idprop_remove,
                    input_pose_data_append,
                    input_pose_data_remove,
                    input_pose_data_update,
                    input_pose_distance_driver_remove,
                    input_pose_distance_driver_remove_all,
                    input_pose_distance_driver_update,
                    input_pose_distance_driver_update_all,
                    input_pose_distance_fcurve_update,
                    input_pose_distance_fcurve_update_all,
                    input_pose_distance_idprop_remove,
                    input_pose_distance_idprop_update,
                    input_pose_radii_update, input_symmetry_assign, input_symmetry_target)

from .pose import (RBFDriverPose, pose_distance_sum_driver_remove_all,
                   pose_distance_sum_driver_update_all,
                   pose_distance_sum_idprop_remove, pose_symmetry_assign, pose_symmetry_target,
                   pose_weight_driver_remove,
                   pose_weight_driver_remove_all,
                   pose_weight_driver_update_all,
                   pose_weight_idprop_remove,
                   pose_weight_idprop_update)

log = logging.getLogger("rbf_drivers")


class ShapeKeyTarget(bpy.types.PropertyGroup):
    pass


def new_type_items():
    items = []
    cache = [
        ('NONE'          , "Generic"                 , "", 'DRIVER'       , 0),
        ('NONE_SYM'      , "Generic (Symmetrical)"   , "", 'MOD_MIRROR'   , 1),
        None,
        ('SHAPE_KEYS'    , "Shape Keys"              , "", 'SHAPEKEY_DATA', 2),
        ('SHAPE_KEYS_SYM', "Shape Keys (Symmetrical)", "", 'MOD_MIRROR'   , 3),
        ]
    def get_items(operator: bpy.types.Operator,
                  context: typing.Union[bpy.types.Context, None]
                  ) -> typing.List[typing.Union[typing.Tuple[str, str, str, str, int], None]]:
        items.clear()
        if context is None or context.object is None or context.object.type != 'MESH':
            items.append(cache[0])
            items.append(cache[1])
        else:
            items.extend(cache)
        return items
    return get_items


class RBFDRIVERS_OT_new(bpy.types.Operator):
    bl_idname = "rbf_driver.add"
    bl_label = "Add Driver"
    bl_description = "Create a new RBF driver"
    bl_options = {'INTERNAL', 'UNDO'}

    type: bpy.props.EnumProperty(
        name="Type",
        description="Type of RBF driver(s) to create",
        items=new_type_items(),
        default=0,
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

        type = self.type
        if type.endswith('_SYM'):
            symmetrical = True
            type = type[:-4]
        else:
            symmetrical = False

        drivers = object.rbf_drivers
        names = [driver.name for driver in drivers]
        index = 0
        name = "RBF Driver"
        new_drivers = []

        if symmetrical:
            while name in names or f'{name}.L' in names or f'{name}.R' in names:
                index += 1
                name = f'RBF Driver.{str(index).zfill(3)}'
        else:
            while name in names:
                index += 1
                name = f'RBF Driver.{str(index).zfill(3)}'

        if symmetrical:
            for suffix in (".L", ".R"):
                driver = drivers.collection__internal__.add()
                driver["name"] = f'{name}{suffix}'
                new_drivers.append(driver)
        else:
            driver = drivers.collection__internal__.add()
            driver["name"] = name
            new_drivers.append(driver)

        for driver in new_drivers:
            driver["type"] = DRIVER_TYPE_INDEX[type]
            driver.falloff.__init__()

            poses = driver.poses
            rest_pose = poses.collection__internal__.add()
            rest_pose.falloff.__init__()

        if symmetrical:
            new_drivers[0]["symmetry_identifier"] = new_drivers[1].identifier
            new_drivers[1]["symmetry_identifier"] = new_drivers[0].identifier
            new_drivers[0].poses[0]["symmetry_identifier"] = new_drivers[1].poses[0].identifier
            new_drivers[1].poses[0]["symmetry_identifier"] = new_drivers[0].poses[0].identifier

        shapekeys = type == 'SHAPE_KEYS'

        if not shapekeys:
            for driver in new_drivers:
                driver.poses[0]["name"] = "Rest"
        else:
            for driver in new_drivers:
                key = object.data.shape_keys
                if key is None:
                    shape = object.shape_key_add(name="Basis", from_mix=False)
                else:
                    shape = key.reference_key
                driver.poses[0]["name"] = shape.name
        
        for driver in new_drivers:
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
        object = context.object
        drivers = object.rbf_drivers
        driver: RBFDriver = drivers.active

        if driver.has_symmetry_target:
            mirror = object.rbf_drivers.search(driver.symmetry_identifier)
            if mirror:
                for input in mirror.inputs:
                    input["symmetry_identifier"] = ""
                    for variable in input.variables:
                        variable["symmetry_identifier"] = ""
                        for target in variable.targets:
                            target["symmetry_identifier"] = ""

                for output in mirror.outputs:
                    output["symmetry_identifier"] = ""
                    for channel in output.channels:
                        channel["symmetry_identifier"] = ""

                for pose in mirror.poses:
                    pose["symmetry_identifier"] = ""
        
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

        curve = driver.falloff.curve
        nodetree_node_update(curve.node_identifier, curve)

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
        drivers = context.object.rbf_drivers
        driver: RBFDriver = drivers.active

        if driver.has_symmetry_target:
            mirror = drivers.search(driver.symmetry_identifier)
            if mirror is None:
                log.warning(f'Search failed for symmetry target of {driver}.', stack_info=True)
                self.execute__internal__(driver)
            else:
                input_symmetry_assign(self.execute__internal__(driver),
                                      self.execute__internal__(mirror))
        else:
            self.execute__internal__(driver)

        return {'FINISHED'}

    def execute__internal__(self, driver: RBFDriver) -> RBFDriverInput:
        inputs = driver.inputs

        names = [input.name for input in inputs]
        index = 0
        name = f'Input'
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

        if poses.active:
            input.active_pose.__init__(input, poses.active_index)

        inputs.active_index = len(inputs)-1
        return input


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
        object = context.object
        driver: RBFDriver = object.rbf_drivers.active
        target = [(driver, driver.inputs, driver.inputs.active)]

        if driver.has_symmetry_target:
            m_input = input_symmetry_target(target[0][2])
            if m_input is None:
                log.warning((f'Search failed for symmetry target of {target[0][2]}.'))
            else:
                target.append((m_input.rbf_driver, m_input.rbf_driver.inputs, m_input))

        for args in target:
            self.execute__internal__(*args)

        return {'FINISHED'}

    def execute__internal__(self, driver: RBFDriver, inputs: RBFDriverInputs, input: RBFDriverInput) -> None:

        input_pose_distance_driver_remove_all(input)
        input_pose_distance_idprop_remove(input)

        input_influence_idprop_remove(input)
        input_influence_sum_driver_update(inputs)

        inputs.collection__internal__.remove(inputs.find(input.name))
        inputs.active_index = max(len(inputs)-1, inputs.active_index)

        poses = driver.poses

        pose_distance_sum_driver_update_all(poses, inputs)
        pose_weight_driver_update_all(poses, inputs)


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
        target = [(driver, inputs.active_index)]

        input: RBFDriverInput = inputs.active
        if input.has_symmetry_target:
            m_input = input_symmetry_target(input)
            if input is None:
                log.warning((f'Search failed for symmetry target of {input}.'))
            else:
                m_driver = m_input.driver
                m_inputs = m_driver.inputs
                target.append((m_driver, m_inputs.find(m_input.name)))

        for args in target:
            self.execute__internal__(*args)

        return {'FINISHED'}

    def execute__internal__(self, driver: RBFDriver, index: int) -> None:
        inputs = driver.inputs
        inputs.collection__internal__.move(index, index - 1)

        input_influence_sum_driver_update(inputs)
        pose_distance_sum_driver_update_all(driver.poses, inputs)

        if index == inputs.active_index:
            inputs.active_index -= 1


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
        target = [(driver, inputs.active_index)]

        input: RBFDriverInput = inputs.active
        if input.has_symmetry_target:
            m_input = input_symmetry_target(input)
            if input is None:
                log.warning((f'Search failed for symmetry target of {input}.'))
            else:
                m_driver = m_input.driver
                m_inputs = m_driver.inputs
                target.append((m_driver, m_inputs.find(m_input.name)))

        for args in target:
            self.execute__internal__(*args)

        return {'FINISHED'}

    def execute__internal__(self, driver: RBFDriver, index: int) -> None:
        inputs = driver.inputs
        inputs.collection__internal__.move(index, index + 1)

        input_influence_sum_driver_update(inputs)
        pose_distance_sum_driver_update_all(driver.poses, inputs)

        if inputs.active_index == index:
            inputs.active_index += 1


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
        drivers = context.object.rbf_drivers
        driver: RBFDriver = drivers.active

        if driver.has_symmetry_target:
            mirror = drivers.search(driver.symmetry_identifier)
            if mirror is None:
                log.warning(f'Search failed for symmetry target of {driver}.', stack_info=True)
                self.execute__internal__(driver)
            else:
                output_symmetry_assign(self.execute__internal__(driver),
                                       self.execute__internal__(mirror))
        else:
            self.execute__internal__(driver)
        
        return {'FINISHED'}

    def execute__internal__(self, driver: RBFDriver) -> RBFDriverOutput:
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

        if poses.active:
            output.active_pose.__init__(output, poses.active_index)

        outputs.active_index = len(outputs) - 1
        return output


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
        object = context.object
        driver: RBFDriver = object.rbf_drivers.active
        target = [(driver, driver.outputs, driver.outputs.active)]

        if driver.has_symmetry_target:
            m_output = input_symmetry_target(target[0][2])
            if m_output is None:
                log.warning((f'Search failed for symmetry target of {target[0][2]}.'))
            else:
                m_driver = m_output.rbf_driver
                target.append((m_driver, m_driver.outputs, m_output))

        for args in target:
            self.execute__internal__(*args)

        return {'FINISHED'}

    def execute__internal__(self, driver: RBFDriver, outputs: RBFDriverOutputs, output: RBFDriverOutput) -> None:
        output_drivers_remove(output)
        output_idprops_remove(output)
        outputs.collection__internal__.remove(outputs.active_index)
        outputs.active_index = max(len(outputs)-1, outputs.active_index)


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
        drivers = context.object.rbf_drivers
        driver: RBFDriver = drivers.active

        if driver.has_symmetry_target:
            mirror = drivers.search(driver.symmetry_identifier)
            if mirror is None:
                log.warning(f'Search failed for symmetry target of {driver}.', stack_info=True)
                self.execute__internal__(driver, False)
            else:
                pose_symmetry_assign(self.execute__internal__(driver, True),
                                     self.execute__internal__(mirror, True))
        else:
            self.execute__internal__(driver, False)

        return {'FINISHED'}

    def execute__internal__(self, driver: RBFDriver, mirror: typing.Optional[bool]=False) -> RBFDriverPose:
        poses = driver.poses

        pose = poses.collection__internal__.add()
        pose.falloff.__init__()

        object = driver.id_data

        if object.type == 'MESH' and driver.type == 'SHAPE_KEYS':
            shape = None
            if self.type == 'USE':
                key = object.data.shape_keys
                if key:
                    name = symmetrical_target(self.shape_target) if mirror else self.shape_target
                    shape = key.key_blocks.get(name)
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
                output_pose_data_append(output)

        for input in driver.inputs:
            input_pose_data_append(input)

        driver.update()
        poses.active_index = len(poses)-1
        return pose


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
        object = context.object
        driver = object.rbf_drivers.active
        target = [(driver, driver.poses.active)]

        if target[0][1].has_symmetry_target:
            m_pose = pose_symmetry_target(target[0][1])
            if m_pose is None:
                log.warning((f'Search failed for symmetry target of {target[0][1]}.'))
            else:
                target.append((m_pose.rbf_driver, m_pose))

        for args in target:
            self.execute__internal__(*args)

        return {'FINISHED'}

    def execute__internal__(self, driver: RBFDriver, pose: RBFDriverPose) -> None:
        poses = driver.poses
        index = poses.find(pose.name)
        count = len(poses) - 1
        is_shape_keys = driver.type == 'SHAPE_KEYS'

        nodetree_node_remove(pose.falloff.curve.node_identifier)
        poses.collection__internal__.remove(index)

        for input in driver.inputs:
            input_pose_data_remove(input, index)
            input_pose_radii_update(input)
            input_pose_distance_idprop_update(input, count)
            input_pose_distance_driver_remove(input, count)
            input_pose_distance_driver_update_all(input, count)
            input_pose_distance_fcurve_update_all(input, count)

        pose_weight_driver_remove(poses, count, is_shape_keys)
        pose_weight_idprop_update(poses)

        if not is_shape_keys:
            for output in driver.outputs:
                output_pose_data_remove(output, index)
                output_idprops_update(output, count)
                output_drivers_update(output, poses)
        
        if poses.active_index == index:
            poses.active_index = min(count-1, poses.active_index)


class RBFDRIVERS_OT_pose_update(bpy.types.Operator):
    bl_idname = "rbf_driver.pose_update"
    bl_label = "Update Pose"
    bl_description = "Update the selected RBF driver pose"
    bl_options = {'INTERNAL', 'UNDO'}

    layers: bpy.props.EnumProperty(
        name="Update",
        items=[
            ('INPUTS' , "Update Inputs" , "", 'NONE', 0),
            ('OUTPUTS', "Update Outputs", "", 'NONE', 1),
            ('ALL'    , "Update Inputs and Outputs"    , "", 'NONE', 2),
            ],
        default='ALL',
        options=set()
        )

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.poses.active is not None)

    def execute(self, context: bpy.types.Context) -> typing.Set[str]:
        object = context.object
        driver = object.rbf_drivers.active
        target = [(driver, driver.poses.active)]

        if target[0][1].has_symmetry_target:
            m_pose = pose_symmetry_target(target[0][1])
            if m_pose is None:
                log.warning((f'Search failed for symmetry target of {target[0][1]}.'))
            else:
                target.append((m_pose.rbf_driver, m_pose))

        for args in target:
            self.execute__internal__(*args)

        return {'FINISHED'}

    def execute__internal__(self, driver: RBFDriver, pose: RBFDriverPose) -> None:
        poses = driver.poses
        index = poses.find(pose.name)
        count = len(poses)

        if self.layers in ('INPUTS', 'ALL'):
            for input in driver.inputs:
                input_pose_data_update(input, index)
                input_pose_radii_update(input)
                input_pose_distance_driver_update(input, index)
                input_pose_distance_fcurve_update_all(input, count)
                if poses.active_index == index:
                    input.active_pose.__init__(input, index)

        if self.layers in ('OUTPUTS', 'ALL'):
            for output in driver.outputs:
                output_pose_data_update(output, index)
                if poses.active_index == index:
                    output.active_pose.__init__(output, index)


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
        object = context.object
        driver = object.rbf_drivers.active
        target = [(driver, driver.poses.active)]

        if target[0][1].has_symmetry_target:
            m_pose = pose_symmetry_target(target[0][1])
            if m_pose is None:
                log.warning((f'Search failed for symmetry target of {target[0][1]}.'))
            else:
                target.append((m_pose.rbf_driver, m_pose))

        for args in target:
            self.execute__internal__(*args)

        return {'FINISHED'}

    def execute__internal__(self, driver: RBFDriver, pose: RBFDriverPose) -> None:
        poses = driver.poses
        index = poses.find(pose.name)

        if index > 0:
            poses.collection__internal__.move(index, index - 1)
            if poses.active_index == index:
                poses["active_index"] = index - 1

            for input in driver.inputs:
                input.pose_radii.data__internal__.move(index, index - 1)

                for variable in input.variables:
                    variable.data.data__internal__.move(index, index - 1)

                input_pose_distance_driver_update(input, index)
                input_pose_distance_driver_update(input, index - 1)

                input_pose_distance_fcurve_update(input, index)
                input_pose_distance_fcurve_update(input, index - 1)

                if poses.active_index == index:
                    input.active_pose.__init__(input, index - 1)

            if driver.type != 'SHAPE_KEYS':
                for output in driver.outputs:
                    for channel in output.channels:
                        channel.data.data__internal__.move(index, index - 1)

                    if poses.active_index == index:
                        output.active_pose.__init__(output, index - 1)

                    output.update()


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
        object = context.object
        driver = object.rbf_drivers.active
        target = [(driver, driver.poses.active)]

        if target[0][1].has_symmetry_target:
            m_pose = pose_symmetry_target(target[0][1])
            if m_pose is None:
                log.warning((f'Search failed for symmetry target of {target[0][1]}.'))
            else:
                target.append((m_pose.rbf_driver, m_pose))

        for args in target:
            self.execute__internal__(*args)

        return {'FINISHED'}

    def execute__internal__(self, driver: RBFDriver, pose: RBFDriverPose) -> None:
        poses = driver.poses
        index = poses.find(pose.name)

        if index < len(poses) - 1:
            poses.collection__internal__.move(index, index + 1)
            if poses.active_index == index:
                poses["active_index"] = index + 1

            for input in driver.inputs:
                input.pose_radii.data__internal__.move(index, index + 1)

                for variable in input.variables:
                    variable.data.data__internal__.move(index, index + 1)

                input_pose_distance_driver_update(input, index)
                input_pose_distance_driver_update(input, index + 1)

                input_pose_distance_fcurve_update(input, index)
                input_pose_distance_fcurve_update(input, index + 1)

                if poses.active_index == index:
                    input.active_pose.__init__(input, index + 1)

            if driver.type != 'SHAPE_KEYS':
                for output in driver.outputs:
                    for channel in output.channels:
                        channel.data.data__internal__.move(index, index + 1)

                    if poses.active_index == index:
                        output.active_pose.__init__(output, index + 1)

                    output.update()

