
from itertools import filterfalse
from operator import attrgetter
from typing import Iterator, List, Optional, Set, Tuple, Union, TYPE_CHECKING
from bpy.types import Object, Operator, PropertyGroup
from bpy.props import BoolProperty, CollectionProperty, EnumProperty, IntProperty, StringProperty
from mathutils import Matrix
import numpy as np
from ..lib.symmetry import is_symmetrical, symmetrical_target
from ..lib.rotation_utils import (quaternion_to_euler,
                                  quaternion_to_swing_twist_x,
                                  quaternion_to_swing_twist_y,
                                  quaternion_to_swing_twist_z)
from ..api.inputs import (INPUT_ROTATION_AXIS_TABLE,
                         INPUT_ROTATION_MODE_TABLE,
                         INPUT_ROTATION_ORDER_TABLE)
from ..api.driver import DRIVER_TYPE_TABLE
from ..app.name_manager import outputname
from ..app.output_channel_driver_manager import outputs_activate_valid
from ..app.pose_weight_driver_manager import pose_weight_drivers_update
from ..app.property_manager import pose_idprops_create
from ..app.utils import idprop_remove
if TYPE_CHECKING:
    from bpy.types import Context, Event, PoseBone
    from idprop.types import IDPropertyGroup
    from ..api.driver import RBFDriver
    from ..api.drivers import RBFDrivers


def new_type_items():
    items = []
    cache = [
        ('NONE'    , "Generic"              , "", 'DRIVER'    , 0),
        ('NONE_SYM', "Generic (Symmetrical)", "", 'MOD_MIRROR', 1),
        None,
        ('SHAPE_KEY'    , "Shape Keys"              , "", 'SHAPEKEY_DATA', 2),
        ('SHAPE_KEY_SYM', "Shape Keys (Symmetrical)", "", 'MOD_MIRROR'   , 3),
        ]
    def get_items(_: Operator, context: Optional['Context']) -> List[Union[Tuple[str, str, str, str, int], None]]:
        items.clear()
        if (context is None
            or context.object is None
            or context.object.type not in {'MESH', 'LATTICE', 'CURVE'}
            ):
            items.append(cache[0])
            items.append(cache[1])
        else:
            items.extend(cache)
        return items
    return get_items


class RBFDRIVERS_OT_new(Operator):
    bl_idname = "rbf_driver.new"
    bl_label = "Add Driver"
    bl_description = "Create a new RBF driver"
    bl_options = {'INTERNAL', 'UNDO'}

    type: EnumProperty(
        name="Type",
        description="Type of RBF driver(s) to create",
        items=new_type_items(),
        default=0,
        options=set()
        )

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return object is not None and object.type != 'EMPTY'

    def execute(self, context: 'Context') -> Set[str]:
        object = context.object
        type = self.type

        if type.startswith('SHAPE') and object.type not in {'MESH', 'LATTICE', 'CURVE'}:
            self.report({'ERROR'}, "Shape Keys RBF driver requires a mesh, lattice or curve object")
            return {'CANCELLED'}

        if type.endswith('_SYM'):
            symmetrical = True
            type = type[:-4]
        else:
            symmetrical = False

        drivers: 'RBFDrivers' = object.rbf_drivers
        names = [driver.name for driver in drivers]
        index = 0
        name = "RBF Driver"

        if symmetrical:
            while name in names or f'{name}.L' in names or f'{name}.R' in names:
                index += 1
                name = f'RBF Driver.{str(index).zfill(3)}'
        else:
            while name in names:
                index += 1
                name = f'RBF Driver.{str(index).zfill(3)}'

        if symmetrical:
            drivers.new(mirror=drivers.new(name=f'{name}.L', type=type))
        else:
            drivers.new(name=name, type=type)

        return {'FINISHED'}


class RBFDRIVERS_OT_remove(Operator):
    bl_idname = "rbf_driver.remove"
    bl_label = "Remove Driver"
    bl_description = "Remove the selected RBF driver"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None)

    def execute(self, context: 'Context') -> Set[str]:
        drivers = context.object.rbf_drivers
        drivers.remove(drivers.active)
        return {'FINISHED'}


class RBFDRIVERS_OT_symmetrize(Operator):
    bl_idname = "rbf_driver.symmetrize"
    bl_label = "Symmetrize"
    bl_description = "Create mirrored clone of RBF driver"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.has_symmetry_target is False
                and is_symmetrical(object.rbf_drivers.active.name))

    def execute(self, context: 'Context') -> Set[str]:
        drivers = context.object.rbf_drivers
        drivers.new(mirror=drivers.active)
        return {'FINISHED'}


class RBFDRIVERS_OT_make_generic(Operator):
    bl_idname = "rbf_driver.make_generic"
    bl_label = "Generic"
    bl_description = "Convert RBF driver to generic type"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.type == 'SHAPE_KEY')

    def execute(self, context: 'Context') -> Set[str]:
        drivers: 'RBFDrivers' = context.object.rbf_drivers

        driver: 'RBFDriver' = drivers.active
        driver["type"] = DRIVER_TYPE_TABLE['NONE']

        if driver.has_symmetry_target:
            mirror = drivers.search(driver.symmetry_identifier)
            if mirror:
                mirror["type"] = DRIVER_TYPE_TABLE['NONE']

        return {'FINISHED'}


class RBFDRIVERS_OT_move_up(Operator):

    bl_idname = "rbf_driver.move_up"
    bl_label = "Move Driver Up"
    bl_description = "Move the selected RBF driver up within the list of drivers"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active_index >= 1)

    def execute(self, context: 'Context') -> Set[str]:
        drivers = context.object.rbf_drivers
        drivers.internal__.move(drivers.active_index, drivers.active_index - 1)
        drivers.active_index -= 1
        return {'FINISHED'}


class RBFDRIVERS_OT_move_down(Operator):

    bl_idname = "rbf_driver.move_down"
    bl_label = "Move Driver Down"
    bl_description = "Move the selected RBF driver down within the list of drivers"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active_index < len(object.rbf_drivers) - 1)

    def execute(self, context: 'Context') -> Set[str]:
        drivers = context.object.rbf_drivers
        drivers.internal__.move(drivers.active_index, drivers.active_index + 1)
        drivers.active_index += 1
        return {'FINISHED'}


class LegacyDriver(PropertyGroup):
    
    index: IntProperty(min=0, default=0)

    data_target: StringProperty(
        name="Data",
        default="",
        options=set()
        )

    bone_target: StringProperty(
        name="Bone",
        default="",
        options=set()
        )

    import_flag: BoolProperty(
        name="Upgrade",
        description="Upgrade the RBF driver",
        default=True,
        options=set()
        )

    show_detail: BoolProperty(
        name="Show Detail",
        default=False,
        options=set()
        )


class RBFDRIVERS_OT_upgrade(Operator):
    bl_idname = "rbf_driver.upgrade"
    bl_label = "Upgrade RBF Drivers"
    bl_description = "Search for legacy (version < 2.0.0) RBF drivers and upgrade them"
    bl_options = {'REGISTER', 'UNDO'}

    active_index: IntProperty(
        name="Driver",
        description="Legacy RBF driver",
        min=0,
        default=0,
        options=set()
        )

    legacy_drivers: CollectionProperty(
        type=LegacyDriver,
        options=set()
        )

    def invoke(self, context: 'Context', event: 'Event') -> Set[str]:
        items = self.legacy_drivers
        items.clear()

        def is_armature(object: 'Object') -> bool:
            return object.type == 'ARMATURE'

        def iter_drivers(bone: 'PoseBone') -> Iterator['IDPropertyGroup']:
            drivers = bone.get("rbf_drivers")
            if drivers:
                for driver in drivers.get("data__internal", []):
                    yield driver

        for object in filter(is_armature, context.blend_data.objects):
            for bone in object.pose.bones:
                for index, data in enumerate(iter_drivers(bone)):
                    item: LegacyDriver = items.add()
                    item.index = index
                    item.name = data.get("name", "")
                    item.data_target = object.name
                    item.bone_target = bone.name

        if len(items) == 0:
            def draw(self, context):
                layout = self.layout
                layout.label(text="No legacy RBF drivers found.")

            context.window_manager.popup_menu(draw, title="Upgrade RBF Drivers")
            return {'CANCELLED'}

        return context.window_manager.invoke_props_dialog(self, width=300)

    def draw(self, _: 'Context') -> None:
        layout = self.layout
        layout.separator()

        column = layout.column(align=True)
        for item in self.legacy_drivers:
            row = column.box().row()

            row.prop(item, "show_detail",
                     text="",
                     icon=f'{"DOWNARROW_HLT" if item.show_detail else "RIGHTARROW"}',
                     emboss=False)

            row.label(text=item.name, icon='DRIVER')
            row.prop(item, "import_flag",
                     text="",
                     icon=f'CHECKBOX_{"" if item.import_flag else "DE"}HLT',
                     emboss=False)

            if item.show_detail:
                box = column.box()

                row = box.row()
                row.label(icon='BLANK1')
                row.label(icon='OBJECT_DATA', text=item.data_target)

                row = box.row()
                row.label(icon='BLANK1')
                row.label(icon='BONE_DATA', text=item.bone_target)

        layout.separator()

    def execute(self, context: 'Context') -> Set[str]:
        object = context.object

        for legacy in filter(attrgetter("import_flag"), self.legacy_drivers):
            bone = context.blend_data.objects[legacy.data_target].pose.bones[legacy.bone_target]
            data = bone["rbf_drivers"]["data__internal"][legacy.index]

            name = data.get("name", "")
            if name:
                sym = symmetrical_target(name)
                if sym and sym in object.rbf_drivers:
                    object.rbf_drivers.new(mirror=output.rbf_drivers[sym])
                    continue

            driven = data.get("driven_properties", {}).get("data__internal", [])

            if all(prop.get("type") == 2 for prop in driven):
                driver = object.rbf_drivers.new(type='SHAPE_KEY')
            else:
                driver = object.rbf_drivers.new()

            posedata = []
            identity = (1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1., 0., 0., 0., 0., 1.)

            for index, item in enumerate(data.get("poses", {}).get("data__internal", [])):

                values = tuple(item.get("matrix", identity))
                # matrix = Matrix((values[:4], values[4:8], values[8:12], values[12:]))
                matrix = Matrix(((values[0], values[4], values[8] , values[12]),
                                 (values[1], values[5], values[9] , values[13]),
                                 (values[2], values[6], values[10], values[14]),
                                 (values[3], values[7], values[11], values[15])))
                posedata.append(matrix)

                if index == 0:
                    pose = driver.poses[0]
                    pose["name"] = item.get("name", "Rest")
                else:
                    pose = driver.poses.internal__.add()
                    pose["name"] = item.get("name", "")
                    pose_idprops_create(pose)
                    pose.interpolation.__init__(type='SIGMOID', interpolation='LINEAR')

            # Location Input
            flags = tuple(map(bool, data.get("use_location", (0, 0, 0))))
            if any(flags):
                input = driver.inputs.new(type='LOCATION')
                input.object = bone.id_data
                input.bone_target = bone.name

                matrix = np.array([m.to_translation() for m in posedata], dtype=float)
                for variable, flag, values in zip(input.variables, flags, matrix.T):
                    variable["is_enabled"] = flag
                    variable.data.__init__(values)

            # Rotation Input
            flags = tuple(map(bool, data.get("use_rotation", (0, 0, 0, 0))))
            if any(flags):
                input = driver.inputs.new(type='ROTATION')
                input.object = bone.id_data
                input.bone_target = bone.name

                ROTATION_MODES = (
                    'AUTO',
                    'XYZ',
                    'XZY',
                    'YXZ',
                    'YZX',
                    'ZXY',
                    'ZYX',
                    'QUATERNION',
                    'SWING_TWIST_X',
                    'SWING_TWIST_Y',
                    'SWING_TWIST_Z',
                    )

                mode = ROTATION_MODES[data.get("rotation_mode", 0)]
                matrix = np.array([m.to_quaternion() for m in posedata], dtype=float)

                if all(flags):
                    input["rotation_mode"] = INPUT_ROTATION_MODE_TABLE['QUATERNION']

                elif len(mode) < 5:
                    order = mode if len(mode) == 3 else 'XYZ'
                    input["rotation_mode"]  = INPUT_ROTATION_MODE_TABLE['EULER']
                    input["rotation_order"] = INPUT_ROTATION_ORDER_TABLE[order]
                    flags = (False,) + flags[1:]
                    for row in matrix:
                        row[:] = (0.,) + tuple(quaternion_to_euler(row, order=order))

                elif mode == 'SWING_TWIST_X':

                    if flags == (False, True, False, False):
                        input["rotation_mode"] = INPUT_ROTATION_MODE_TABLE['TWIST']
                        input["rotation_axis"] = INPUT_ROTATION_AXIS_TABLE['X']
                        for row in matrix:
                            row[:] = quaternion_to_swing_twist_x(row, quaternion=True)

                    elif flags == (True, False, True, True):
                        input["rotation_mode"] = INPUT_ROTATION_MODE_TABLE['SWING']
                        input["rotation_axis"] = INPUT_ROTATION_AXIS_TABLE['X']

                    else:
                        input["rotation_mode"] = INPUT_ROTATION_MODE_TABLE['QUATERNION']
                        flags = (True, True, True, True)
                        self.log.warning()

                elif mode == 'SWING_TWIST_Y':

                    if flags == (False, False, True, False):
                        input["rotation_mode"] = INPUT_ROTATION_MODE_TABLE['TWIST']
                        input["rotation_axis"] = INPUT_ROTATION_AXIS_TABLE['Y']
                        for row in matrix:
                            row[:] = quaternion_to_swing_twist_y(row, quaternion=True)

                    elif flags == (True, True, False, True):
                        input["rotation_mode"] = INPUT_ROTATION_MODE_TABLE['SWING']
                        input["rotation_axis"] = INPUT_ROTATION_AXIS_TABLE['Y']

                    else:
                        input["rotation_mode"] = INPUT_ROTATION_MODE_TABLE['QUATERNION']
                        flags = (True, True, True, True)
                        self.log.warning()

                elif mode == 'SWING_TWIST_Z':

                    if flags == (False, False, False, True):
                        input["rotation_mode"] = INPUT_ROTATION_MODE_TABLE['TWIST']
                        input["rotation_axis"] = INPUT_ROTATION_AXIS_TABLE['Z']
                        for row in matrix:
                            row[:] = quaternion_to_swing_twist_z(row, quaternion=True)

                    elif flags == (True, True, True, False):
                        input["rotation_mode"] = INPUT_ROTATION_MODE_TABLE['SWING']
                        input["rotation_axis"] = INPUT_ROTATION_AXIS_TABLE['Z']
                    
                    else:
                        input["rotation_mode"] = INPUT_ROTATION_MODE_TABLE['QUATERNION']
                        flags = (True, True, True, True)
                        self.log.warning()

                for variable, flag, values in zip(input.variables, flags, matrix.T):
                    variable["is_enabled"] = flag
                    variable.data.__init__(values)

            # Scale Input
            flags = tuple(map(bool, data.get("use_scale", (0, 0, 0))))
            if any(flags):
                input = driver.inputs.new(type='SCALE')
                input.object = bone.id_data
                input.bone_target = bone.name

                matrix = np.array([m.to_scale() for m in posedata], dtype=float)
                for variable, flag, values in zip(input.variables, flags, matrix.T):
                    variable["is_enabled"] = flag
                    variable.data.__init__(values)

            pose_weight_drivers_update(driver)

            TRANSFORM_TYPES = (
                'LOC_X', 'LOC_Y', 'LOC_Z', '',
                'ROT_W', 'ROT_X', 'ROT_Y', 'ROT_Z', '',
                'SCALE_X', 'SCALE_Y', 'SCALE_Z')

            for item in driven:
                type = item.get("type", 0)
                sampledata = [x.get("value", 0.0) for x in item.get("samples", {}).get("data__internal", [])]

                # Single Property Output
                if type == 1:
                    output = driver.outputs.new(type='SINGLE_PROP')
                    output.channels[0].data.__init__(sampledata)
                    output.object = item.get("id", None)
                    output.data_path = item.get("data_path")

                # Shape Key Output
                elif type == 2:
                    output = driver.outputs.new(type='SHAPE_KEY')
                    output.channels[0].data.__init__(sampledata)
                    output.object = item.get("id", None)
                    output.name = item.get("shape_key", "")

                # TRANSFORM
                elif type == 0:
                    type = TRANSFORM_TYPES[item.get("transform_type", 0)]
                    if type.startswith('LOC'):
                        output = None
                        for member in driver.outputs:
                            if (member.type == 'LOCATION'
                                and member.object == item.get("id", None)
                                and member.bone_target == item.get("bone_target", "")
                                ):
                                output = member
                                break

                        if output is None:
                            output = driver.outputs.new(type='LOCATION')
                            output.object = item.get("id", None)
                            output.bone_target = item.get("bone_target", "")
                            output["name"] = outputname(output)

                        output[f"use_{type[-1].lower()}"] = True

                        channel = output.channels['XYZ'.index(type[-1])]
                        channel["is_enabled"] = True
                        channel.data.__init__(sampledata)

                    elif type.startswith('ROT'):
                        output = None
                        for member in driver.outputs:
                            if (member.type == 'ROTATION'
                                and member.object == item.get("id", None)
                                and member.bone_target == item.get("bone_target", "")
                                ):
                                output = member
                                break

                        if output is None:
                            output = driver.outputs.new(type='ROTATION')
                            output.object = item.get("id", None)
                            output.bone_target = item.get("bone_target", "")
                            output.rotation_mode = ('EULER', 'AXIS_ANGLE', 'QUATERNION')[item.get("rotation_mode", 0)]
                            output["name"] = outputname(output)

                        if output.rotation_mode == 'EULER':
                            output[f"use_{type[-1].lower()}"] = True

                        channel = output.channels['WXYZ'.index(type[-1])]
                        channel["is_enabled"] = True
                        channel.data.__init__(sampledata)

                    elif type.startswith('SCALE'):
                        output = None
                        for member in driver.outputs:
                            if (member.type == 'SCALE'
                                and member.object == item.get("id", None)
                                and member.bone_target == item.get("bone_target", "")
                                ):
                                output = member
                                break

                        if output is None:
                            output = driver.outputs.new(type='SCALE')
                            output.object = item.get("id", None)
                            output.bone_target = item.get("bone_target", "")
                            output["name"] = outputname(output)

                        output[f"use_{type[-1].lower()}"] = True
                        
                        channel = output.channels['XYZ'.index(type[-1])]
                        channel["is_enabled"] = True
                        channel.data.__init__(sampledata)

            id = data.get("id__internal", None)
            if id is not None:
                prefix = 'RBF'
                suffix = f'rbfn.{str(id).zfill(3)}'

                for key in list(bone.id_data.data.keys()):
                    if key.startswith(prefix) and key.endswith(suffix):
                        idprop_remove(bone.id_data.data, key, remove_drivers=True)

                for key in list(bone.keys()):
                    if key.startswith(prefix) and key.endswith(suffix):
                        idprop_remove(bone, key, remove_drivers=True)

            outputs_activate_valid(driver.outputs)

        for legacy in filter(attrgetter("import_flag"), self.legacy_drivers):
            bone = context.blend_data.objects[legacy.data_target].pose.bones[legacy.bone_target]
            data = list(bone["rbf_drivers"]["data__internal"])

            data[legacy.index] = {"removed": 1}
            if any(item.get("removed", 0) for item in data):
                bone["rbf_drivers"]["data__internal"] = data

        for legacy in filter(attrgetter("import_flag"), self.legacy_drivers):
            bone = context.blend_data.objects[legacy.data_target].pose.bones[legacy.bone_target]
            data = bone.get("rbf_drivers", {}).get("internal__", [])
            data = list(filterfalse(lambda item: item.get("removed", 0), data))
            if not len(data):
                try:
                    del bone["rbf_drivers"]
                except: pass

            

        return {'FINISHED'}