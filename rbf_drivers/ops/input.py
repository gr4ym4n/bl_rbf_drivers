
from typing import Set, TYPE_CHECKING
from bpy.types import Operator
from bpy.props import EnumProperty, IntProperty, StringProperty
from ..api.input import INPUT_TYPE_ITEMS
if TYPE_CHECKING:
    from bpy.types import Context
    from ..api.inputs import RBFDriverInputs


class RBFDRIVERS_OT_input_display_settings(Operator):
    bl_idname = "rbf_driver.input_display_settings"
    bl_label = "Display Settings"
    bl_description = "Modify input display settings"
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
        inputs = context.object.rbf_drivers.active.inputs
        layout = self.layout

        layout.separator()
        split = layout.row().split(factor=0.3)
        
        column = split.column()
        column.alignment = 'RIGHT'
        column.label(text="Display")
        split.column().prop(inputs, "display_mode", text="")

        layout.separator()

    def execute(self, context: 'Context') -> Set[str]:

        def draw(*args) -> None:
            RBFDRIVERS_OT_input_display_settings.draw_func(*args)

        context.window_manager.popover(draw, from_active_button=True)
        return {'FINISHED'}


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
        inputs: 'RBFDriverInputs' = context.object.rbf_drivers.active.inputs
        inputs.new(self.type)
        return {'FINISHED'}


class RBFDRIVERS_OT_input_remove(Operator):
    bl_idname = "rbf_driver.input_remove"
    bl_label = "Remove Input"
    bl_description = "Remove the selected RBF driver input"
    bl_options = {'INTERNAL', 'UNDO'}

    input: StringProperty()

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.inputs.active is not None)

    def execute(self, context: 'Context') -> Set[str]:
        inputs: 'RBFDriverInputs' = context.object.rbf_drivers.active.inputs
        inputs.remove(inputs.active)
        return {'FINISHED'}


class RBFDRIVERS_OT_input_move(Operator):
    bl_idname = "rbf_driver.input_move"
    bl_label = "Move Input"
    bl_description = "Move the selected RBF driver input"
    bl_options = {'INTERNAL', 'UNDO'}

    direction: EnumProperty(
        name="Direction",
        description="The direction to move the input",
        items=[
            ('UP'  , "Up"  , ""),
            ('DOWN', "Down", ""),
            ],
        default='UP',
        options=set()
        )

    input: StringProperty(
        name="Input",
        description="The name of the input to move",
        default="",
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
        inputs: 'RBFDriverInputs' = context.object.rbf_drivers.active.inputs

        index = inputs.find(self.input)
        if index == -1:
            self.report({'ERROR'}, f'Input "{self.input}" not found.')
            return {'CANCELLED'}

        direction = self.direction
        if direction == 'UP' and index == 0:
            self.report({'INFO'}, "Cannot move first input up")
            return {'CANCELLED'}

        if direction == 'DOWN' and index == len(inputs) - 1:
            self.report({'INFO'}, "Cannot move last input down")
            return {'CANCELLED'}
        
        inputs.move(index, index-1 if direction == 'UP' else index+1)
        return {'FINISHED'}
