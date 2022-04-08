
from typing import Set, TYPE_CHECKING
from bpy.types import Operator
from bpy.props import EnumProperty
from ..api.output import OUTPUT_TYPE_ITEMS
if TYPE_CHECKING:
    from bpy.types import Context
    from ..api.outputs import RBFDriverOutputs


class RBFDRIVERS_OT_output_display_settings(Operator):
    bl_idname = "rbf_driver.output_display_settings"
    bl_label = "Display Settings"
    bl_description = "Modify output display settings"
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
        outputs = context.object.rbf_drivers.active.outputs

        layout = self.layout
        layout.separator()

        split = layout.row().split(factor=0.3)
        
        column = split.column()
        column.alignment = 'RIGHT'
        column.label(text="Display")

        column = split.column()
        column.prop(outputs, "display_mode", text="")
        column.separator()
        column.prop(outputs, "display_influence")

        layout.separator()

    def execute(self, context: 'Context') -> Set[str]:

        def draw(*args) -> None:
            RBFDRIVERS_OT_output_display_settings.draw_func(*args)

        context.window_manager.popover(draw, from_active_button=True)
        return {'FINISHED'}


class RBFDRIVERS_OT_output_add(Operator):
    bl_idname = "rbf_driver.output_add"
    bl_label = "Add Output"
    bl_description = "Add an RBF driver output"
    bl_options = {'INTERNAL', 'UNDO'}

    type: EnumProperty(
        name="Type",
        items=OUTPUT_TYPE_ITEMS,
        default=OUTPUT_TYPE_ITEMS[0][0],
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
        outputs: 'RBFDriverOutputs' = context.object.rbf_drivers.active.outputs
        outputs.new(self.type)
        return {'FINISHED'}


class RBFDRIVERS_OT_output_remove(Operator):
    bl_idname = "rbf_driver.output_remove"
    bl_label = "Remove Output"
    bl_description = "Remove the selected RBF driver output"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.outputs.active is not None)

    def execute(self, context: 'Context') -> Set[str]:
        outputs: 'RBFDriverOutputs' = context.object.rbf_drivers.active.outputs
        outputs.remove(outputs.active)
        return {'FINISHED'}


class RBFDRIVERS_OT_output_move_up(Operator):
    bl_idname = "rbf_driver.output_move_up"
    bl_label = "Move Output Up"
    bl_description = "Move the selected RBF driver output up within the list of outputs"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.outputs.active is not None
                and object.rbf_drivers.active.outputs.active_index >= 1)

    def execute(self, context: 'Context') -> Set[str]:
        outputs: 'RBFDriverOutputs' = context.object.rbf_drivers.active.outputs
        outputs.move(outputs.active_index, outputs.active_index - 1)
        return {'FINISHED'}


class RBFDRIVERS_OT_output_move_down(Operator):
    bl_idname = "rbf_driver.output_move_down"
    bl_label = "Move Output Down"
    bl_description = "Move the selected RBF driver output down within the list of outputs"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.type != 'EMPTY'
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.outputs.active is not None
                and object.rbf_drivers.active.outputs.active_index < len(object.rbf_drivers.active.inputs) - 1)

    def execute(self, context: 'Context') -> Set[str]:
        outputs: 'RBFDriverOutputs' = context.object.rbf_drivers.active.outputs
        outputs.move(outputs.active_index, outputs.active_index + 1)
        return {'FINISHED'}
