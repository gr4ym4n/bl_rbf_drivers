
from typing import Dict, Iterator, List, Optional, Set, Tuple, Union, TYPE_CHECKING
from bpy.types import Operator, Panel, PropertyGroup, UIList
from bpy.props import CollectionProperty, EnumProperty, IntProperty, PointerProperty
from .core import RBFDNodeReferences
from .mixins import ActiveNodeTree
if TYPE_CHECKING:
    from bpy.types import Context, UILayout

INPUT_TYPE_ITEMS: List[Tuple[str, str, str, str, int]] = [
    ('LOCATION', "Location", "Location transform channels", 'CON_LOCLIMIT' , 0),
    ('ROTATION', "Rotation", "Rotation transform channels", 'CON_ROTLIMIT' , 1),
    ('SCALE'   , "Scale"   , "Scale transform channels"   , 'CON_SIZELIMIT', 2),
    None,
    ('ROTATION_DIFF', "Rotational Difference", "Angle between two bones or objects."   , 'DRIVER_ROTATIONAL_DIFFERENCE', 3),
    ('LOC_DIFF'     , "Distance"             , "Distance between two bones or objects.", 'DRIVER_DISTANCE'             , 4),
    None,
    ('SHAPE_KEY', "Shape Keys"  , "Shape key values"               , 'SHAPEKEY_DATA', 5),
    ('USER_DEF' , "User-defined", "Fully configurable input values", 'RNA'          , 6),
    ]

INPUT_TYPE_INDEX: List[str] = [
    _item[0] for _item in INPUT_TYPE_ITEMS if _item is not None
    ]

INPUT_TYPE_TABLE: Dict[str, int] = {
    _item[0]: _item[4] for _item in INPUT_TYPE_ITEMS if _item is not None
    }

INPUT_TYPE_ICONS: Dict[str, str] = {
    _item[0]: _item[3] for _item in INPUT_TYPE_ITEMS if _item is not None
    }

class RBFDInputTool(PropertyGroup):

    nodes: PointerProperty(
        type=RBFDNodeReferences,
        options=set()
        )

    type: EnumProperty(
        name="Type",
        items=INPUT_TYPE_ITEMS,
        get=lambda self: self.get("type", 0),
        options=set()
        )

    def __init__(self) -> None:
        type = self.type
        refs = self.nodes.internal__
        tree = self.id_data
        self.name = "Input"
        if type in {'LOCATION', 'ROTATION', 'SCALE'}:
            node = tree.nodes.new('RBFDTargetNode')
            node.name = "Target"
            ref = refs.add()
            ref["identifier"] = node.name
            ref["name"] = "Target"


class RBFDInputTools(PropertyGroup):

    internal__: CollectionProperty(
        type=RBFDInputTool,
        options=set()
        )

    active_index: IntProperty(
        name="Input",
        min=0,
        default=0,
        options=set()
        )

    @property
    def active(self) -> Optional[RBFDInputTool]:
        index = self.active_index
        if index < len(self):
            return self[index]

    def __contains__(self, name: str) -> bool:
        return name in self.internal__

    def __getitem__(self, key: Union[int, str, slice]) -> Union[RBFDInputTool,
                                                                List[RBFDInputTool]]:
        return self.internal__[key]

    def __iter__(self) -> Iterator[RBFDInputTool]:
        return iter(self.internal__)

    def __len__(self) -> int:
        return len(self.internal__)

    def get(self, name: str) -> Optional[RBFDInputTool]:
        return self.internal__.get(name)

    def keys(self) -> Iterator[str]:
        return self.internal__.keys()

    def items(self) -> Iterator[Tuple[str, RBFDInputTool]]:
        return self.internal__.items()

    def new(self, type: str) -> RBFDInputTool:
        if not isinstance(type, str):
            raise TypeError()
        if type not in INPUT_TYPE_INDEX:
            raise ValueError()
        tool = self.internal__.add()
        tool["type"] = INPUT_TYPE_TABLE[type]
        tool.__init__()
        return tool

    def remove(self, tool: RBFDInputTool) -> None:
        pass


class RBFDInputBuild(ActiveNodeTree, Operator):
    bl_idname = 'rbf_drivers.input_build'
    bl_label = "Add"
    bl_options = {'UNDO', 'INTERNAL'}

    type: EnumProperty(
        name="Type",
        description="The type of input to build",
        items=INPUT_TYPE_ITEMS,
        options=set()
        )

    def execute(self, context: 'Context') -> Set[str]:
        context.space_data.node_tree.tools.inputs.new(self.type)
        return {'FINISHED'}


class RBFDInputToolsList(UIList):
    bl_idname = 'RBFD_UL_inputs'
    
    def draw_item(self, _0, layout: 'UILayout', _1, tool: RBFDInputTool, _2, _3, _4) -> None:
        layout.prop(tool, "name",
                    text="",
                    icon=INPUT_TYPE_ICONS[tool.type],
                    emboss=False,
                    translate=False)


class RBFDInputToolsPanel(ActiveNodeTree, Panel):
    bl_idname = 'RBFD_PT_inputs'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Builder"
    bl_label = "Inputs"

    def draw(self, context: 'Context') -> None:
        layout = self.layout
        inputs = context.space_data.node_tree.tools.inputs
        row = layout.row()
        row.template_list(RBFDInputToolsList.bl_idname, "",
                          inputs, "internal__",
                          inputs, "active_index")
        col = row.column(align=True)
        col.operator_menu_enum(RBFDInputBuild.bl_idname, "type", text="", icon='ADD')

        tool = inputs.active
        if tool:
            type = tool.type
            if type in {'LOCATION', 'ROTATION', 'SCALE'}:
                ref = tool.nodes.get("Target")
                if ref:
                    node = ref.resolve()
                    if node:
                        socket = node.outputs[0]
                        layout.prop_search(socket, "id", context.blend_data, "objects", text="Object", icon='OBJECT_DATA')
                        ob = socket.id
                        if ob and ob.type == 'ARMATURE':
                            layout.prop_search(socket, "bone_target", ob.data, "bones", text="Bone", icon='BONE_DATA')



