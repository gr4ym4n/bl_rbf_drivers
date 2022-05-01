
from typing import Set, TYPE_CHECKING
from bpy.types import Operator
from bpy.props import CollectionProperty, EnumProperty, IntProperty
from ..api.selection_item import RBFDriverSelectionItem
from ..api.output import OUTPUT_TYPE_ITEMS
from ..gui.generic import RBFDRIVERS_UL_selection_list
if TYPE_CHECKING:
    from bpy.types import Context, Event
    from ..api.outputs import RBFDriverOutputs
    from ..api.driver import RBFDriver


class RBFDRIVERS_OT_output_add(Operator):

    bl_idname = "rbf_driver.output_add"
    bl_label = "Add Output"
    bl_description = "Add an RBF driver output"
    bl_options = {'INTERNAL', 'UNDO'}

    active_index: IntProperty(
        name="Shape",
        min=0,
        default=0,
        options=set()
        )

    shape_keys: CollectionProperty(
        name="Shapes",
        type=RBFDriverSelectionItem,
        options=set()
        )

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

    def invoke(self, context: 'Context', _: 'Event') -> Set[str]:
        object = context.object
        driver: 'RBFDriver' = object.rbf_drivers.active

        if driver.type == 'SHAPE_KEY':
            data = self.shape_keys
            data.clear()

            try:
                key = object.data.shape_keys
            except:
                key = None

            if key:
                ignore = tuple(driver.outputs.keys())
                for item in key.key_blocks[1:]:
                    name = item.name

                    if name not in ignore:
                        item = data.add()
                        item.name = name
                        item.icon = 'SHAPEKEY_DATA'

            return context.window_manager.invoke_props_dialog(self)
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
        driver: 'RBFDriver' = context.object.rbf_drivers.active
        outputs: 'RBFDriverOutputs' = driver.outputs

        if driver.type == 'SHAPE_KEY':
            for item in self.shape_keys:
                if item.selected and item.name not in outputs:
                    output = outputs.new('SHAPE_KEY')
                    output.name = item.name
                    output.object = driver.id_data
        else:
            outputs.new(self.type)

        return {'FINISHED'}

class RBFDRIVERS_OT_output_remove(Operator):

    bl_idname = "rbf_driver.output_remove"
    bl_label = "Remove Output"
    bl_description = "Remove the selected RBF driver output"
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.outputs.active is not None)

    def execute(self, context: 'Context') -> Set[str]:
        outputs: 'RBFDriverOutputs' = context.object.rbf_drivers.active.outputs
        outputs.remove(outputs.active)
        return {'FINISHED'}


class RBFDRIVERS_OT_output_move_up(Operator):

    bl_idname = "rbf_driver.output_move_up"
    bl_label = "Move Down"
    bl_description = "Move output upwards within the list of inputs"
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.outputs.active is not None
                and object.rbf_drivers.active.outputs.active_index > 0)

    def execute(self, context: 'Context') -> Set[str]:
        outputs: 'RBFDriverOutputs' = context.object.rbf_drivers.active.outputs
        outputs.move(outputs.active_index, outputs.active_index - 1)
        return {'FINISHED'}


class RBFDRIVERS_OT_output_move_down(Operator):

    bl_idname = "rbf_driver.output_move_down"
    bl_label = "Move Down"
    bl_description = "Move input downwards within the list of inputs"
    bl_options = {'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        object = context.object
        return (object is not None
                and object.is_property_set("rbf_drivers")
                and object.rbf_drivers.active is not None
                and object.rbf_drivers.active.outputs.active is not None
                and object.rbf_drivers.active.outputs.active_index < len(object.rbf_drivers.active.outputs) - 1)

    def execute(self, context: 'Context') -> Set[str]:
        outputs: 'RBFDriverOutputs' = context.object.rbf_drivers.active.outputs
        outputs.move(outputs.active_index, outputs.active_index + 1)
        return {'FINISHED'}