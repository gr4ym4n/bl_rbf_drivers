
from typing import List, Optional, Set, Tuple, TYPE_CHECKING
from bpy.types import Operator
from bpy.props import EnumProperty, StringProperty
from ..api.input import INPUT_TYPE_ITEMS
from ..api.output import OUTPUT_TYPE_ITEMS
if TYPE_CHECKING:
    from bpy.types import Context


def type_items():
    def get_items(self, _: Optional['Context']=None) -> List[Tuple[str, str, str]]:
        return INPUT_TYPE_ITEMS if self.kind == 'INPUT' else OUTPUT_TYPE_ITEMS
    return get_items


class RBFDRIVERS_OT_layer_add(Operator):
    bl_idname = "rbf_driver.layer_add"
    bl_label = "Add"
    bl_options = {'INTERNAL', 'UNDO'}

    kind: EnumProperty(
        name="Kind",
        description="The kind of layer to add (input or output)",
        items=[
            ('INPUT' , "Input" , ""),
            ('OUTPUT', "Output", ""),
            ],
        default='INPUT',
        options=set()
        )

    type: EnumProperty(
        name="Type",
        items=type_items(),
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
        getattr(context.object.rbf_drivers.active, f'{self.kind.lower()}s').new(self.type)
        return {'FINISHED'}

class RBFDRIVERS_OT_layer_remove(Operator):
    bl_idname = "rbf_driver.layer_remove"
    bl_label = "Add"
    bl_options = {'INTERNAL', 'UNDO'}

    kind: EnumProperty(
        name="Kind",
        description="The kind of layer to add (input or output)",
        items=[
            ('INPUT' , "Input" , ""),
            ('OUTPUT', "Output", ""),
            ],
        default='INPUT',
        options=set()
        )

    name: StringProperty(
        name="Name",
        description="The name of the layer to remove",
        default="",
        options=set()
        )

    def execute(self, context: 'Context') -> Set[str]:
        layers = getattr(context.object.rbf_drivers.active, f'{self.kind.lower()}s')
        layer = layers.get(self.name)

        if layer:
            layers.remove(layer)
            result = {'FINISHED'}
        else:
            self.report({'ERROR'}, f'{self.kind.title()} "{self.name}" not found.')
            result = {'CANCELLED'}

        return result

        
        
