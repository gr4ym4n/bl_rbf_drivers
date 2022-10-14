
from typing import Set, TYPE_CHECKING
from bpy.types import Operator
from bpy.props import CollectionProperty, EnumProperty, IntProperty
from ..api.input import INPUT_DATA_TYPE_TABLE, INPUT_TYPE_ITEMS, INPUT_TYPE_TABLE
from ..api.selection_item import RBFDriverSelectionItem
from ..gui.generic import RBFDRIVERS_UL_selection_list
if TYPE_CHECKING:
    from bpy.types import Context, Event
    from ..api.input_variables import InputVariables
    from ..api.input import Input
    from ..api.input import Inputs
    from ..api.driver import RBFDriver


class RBFDRIVERS_OT_input_add(Operator):
    bl_idname = "rbf_driver.input_add"
    bl_label = "Add Input"
    bl_description = "Add an RBF driver input"
    bl_options = {'INTERNAL', 'UNDO'}

    type: EnumProperty(
        name="Type",
        items=INPUT_TYPE_ITEMS,
        default=INPUT_TYPE_ITEMS[0][0],
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
        inputs: 'Inputs' = context.object.rbf_drivers.active.inputs
        inputs.new(self.type)
        return {'FINISHED'}


class RBFDRIVERS_OT_input_remove(Operator):
    bl_idname = "rbf_driver.input_remove"
    bl_label = "Remove Input"
    bl_description = "Remove the selected RBF driver input"
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.inputs.active is not None)

    def execute(self, context: 'Context') -> Set[str]:
        inputs: 'Inputs' = context.object.rbf_drivers.active.inputs
        inputs.remove(inputs.active)
        return {'FINISHED'}


class RBFDRIVERS_OT_input_decompose(Operator):
    bl_idname = "rbf_driver.input_decompose"
    bl_label = "Decompose"
    bl_description = "Decompose input channels into user-defined variables"
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.inputs.active is not None
                and object.rbf_drivers.active.inputs.active.type != 'USER_DEF')

    def execute(self, context: 'Context') -> Set[str]:
        driver: 'RBFDriver' = context.object.rbf_drivers.active
        input: 'Input' = driver.inputs.active
        if input.type in {'LOCATION', 'SCALE'}:
            for index, variable in zip((2, 1, 0), reversed(input.variables)):
                if not variable.is_enabled:
                    input.variables.internal__.remove(index)

        elif input.type == 'ROTATION':
            mode = input.rotation_mode
            if mode == 'EULER':
                input["data_type"] = INPUT_DATA_TYPE_TABLE['ANGLE']
                for index, variable in zip((3, 2, 1, 0), reversed(input.variables)):
                    if not variable.is_enabled:
                        input.variables.internal__.remove(index)
            elif mode == 'TWIST':
                input["data_type"] = INPUT_DATA_TYPE_TABLE['ANGLE']
                axis = 'WXYZ'.index(mode.rotation_axis)
                for index in reversed(range(4)):
                    if index != axis:
                        input.variables.internal__.remove(index)
            else:
                input["data_type"] = INPUT_DATA_TYPE_TABLE['QUATERNION']
                input["use_swing"] = mode == 'SWING'

        input["type"] = INPUT_TYPE_TABLE['USER_DEF']
        return {'FINISHED'}


class RBFDRIVERS_OT_input_move_up(Operator):
    bl_idname = "rbf_driver.input_move_up"
    bl_label = "Move Up"
    bl_description = "Move input upwards within the list of inputs"
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.inputs.active is not None
                and object.rbf_drivers.active.inputs.active_index > 0)

    def execute(self, context: 'Context') -> Set[str]:
        inputs: 'Inputs' = context.object.rbf_drivers.active.inputs
        inputs.move(inputs.active_index, inputs.active_index - 1)
        return {'FINISHED'}


class RBFDRIVERS_OT_input_move_down(Operator):

    bl_idname = "rbf_driver.input_move_down"
    bl_label = "Move Down"
    bl_description = "Move input downwards within the list of inputs"
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.inputs.active is not None
                and object.rbf_drivers.active.inputs.active_index < len(object.rbf_drivers.active.inputs) - 1)

    def execute(self, context: 'Context') -> Set[str]:
        inputs: 'Inputs' = context.object.rbf_drivers.active.inputs
        inputs.move(inputs.active_index, inputs.active_index + 1)
        return {'FINISHED'}

class RBFDRIVERS_OT_input_variable_add(Operator):
    bl_idname = "rbf_driver.input_variable_add"
    bl_label = "Add Variable"
    bl_description = "Add new input variable"
    bl_options = {'UNDO', 'INTERNAL'}

    active_index: IntProperty(
        name="Shape Key",
        min=0,
        default=0,
        options=set()
        )

    shape_keys: CollectionProperty(
        type=RBFDriverSelectionItem,
        options=set()
        )

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        if object is not None and object.is_property_set("rbf_drivers"):
            driver = object.rbf_drivers.active
            if driver is not None:
                input = driver.inputs.active
                if input is not None and len(input.variables) <= 16:
                    type = input.type
                    if type == 'SHAPE_KEY':
                        object = input.object
                        return (object is not None
                                and object.type in {'MESH', 'LATTICE', 'CURVE'}
                                and object.data.shape_keys is not None)
                    return type == 'USER_DEF'
        return False

    def invoke(self, context: 'Context', event: 'Event') -> Set[str]:
        input: 'Input' = context.object.rbf_drivers.active.inputs.active
        if input.type == 'SHAPE_KEY':
            object = input.object
            shapes = self.shape_keys
            shapes.clear()
            if object and object.data.shape_keys:
                ignore = list(input.variables.keys())
                for item in object.data.shape_keys.key_blocks[1:]:
                    name = item.name
                    if name not in ignore:
                        item = shapes.add()
                        item.name = name
                        item.icon = 'SHAPEKEY_DATA'
            return context.window_manager.invoke_props_dialog(self, width=600)
        else:
            return self.execute(context)

    def draw(self, _: 'Context') -> None:
        layout = self.layout
        layout.separator()
        layout.template_list(RBFDRIVERS_UL_selection_list.bl_idname, "",
                             self, "shape_keys",
                             self, "active_index")
        layout.separator()

    def execute(self, context: 'Context') -> Set[str]:
        input: 'Input' = context.object.rbf_drivers.active.inputs.active
        if input.type == 'SHAPE_KEY':
            for item in self.shape_keys:
                if item.selected:
                    input.variables.new(name=item.name)
        else:
            input.variables.new()
        return {'FINISHED'}


class RBFDRIVERS_OT_input_variable_remove(Operator):
    bl_idname = "rbf_driver.input_variable_remove"
    bl_label = "Remove Variable"
    bl_description = "Remove the input variable"
    bl_options = {'UNDO', 'INTERNAL'}

    index: IntProperty(
        min=0,
        default=0,
        options=set()
        )

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.inputs.active is not None
                and object.rbf_drivers.active.inputs.active.type in {'USER_DEF', 'SHAPE_KEY'})

    def execute(self, context: 'Context') -> Set[str]:
        index = self.index
        variables: 'InputVariables' = context.object.rbf_drivers.active.inputs.active.variables

        if index >= len(variables):
            self.report({'ERROR'}, f'Variable index {index} out of range 0-{len(variables)}')
            return {'CANCELLED'}

        variables.remove(variables[index])
        return {'FINISHED'}