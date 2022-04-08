
from typing import List, Optional, Set, Tuple, Union, TYPE_CHECKING
from bpy.types import Operator
from bpy.props import EnumProperty
from ..api.drivers import DriverNewEvent
from ..app.events import dispatch_event
from ..app.symmetry_manager import set_symmetry_target
if TYPE_CHECKING:
    from bpy.types import Context
    from ..api.drivers import RBFDrivers


def new_type_items():
    items = []
    cache = [
        ('NONE'          , "Generic"                 , "", 'DRIVER'       , 0),
        ('NONE_SYM'      , "Generic (Symmetrical)"   , "", 'MOD_MIRROR'   , 1),
        None,
        ('SHAPE_KEYS'    , "Shape Keys"              , "", 'SHAPEKEY_DATA', 2),
        ('SHAPE_KEYS_SYM', "Shape Keys (Symmetrical)", "", 'MOD_MIRROR'   , 3),
        ]
    def get_items(_: Operator, context: Optional['Context']) -> List[Union[Tuple[str, str, str, str, int], None]]:
        items.clear()
        if context is None or context.object is None or context.object.type != 'MESH':
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

        if type.startswith('SHAPE') and object.type != 'MESH':
            self.report({'ERROR'}, "Shape Keys RBF driver requires a mesh object")
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
        drivers.collection__internal__.move(drivers.active_index, drivers.active_index - 1)
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
        drivers.collection__internal__.move(drivers.active_index, drivers.active_index + 1)
        drivers.active_index += 1
        return {'FINISHED'}
