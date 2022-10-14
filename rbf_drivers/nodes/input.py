
from typing import TYPE_CHECKING, Any, Dict, Iterable, Optional, Sequence
from bpy.types import Node, NodeCustomGroup, NodeTree
from bpy.props import BoolProperty, EnumProperty, IntProperty
from ..data import Input, InputMapping, InputType, TransformType, VectorDataType
from ..core import RBFDriverNode, RBFDriverNodeGroup, RBFDriverNodeSubtree
if TYPE_CHECKING:
    from bpy.types import Context, Node, UILayout
    from ..sockets.input import RBFDriverNodeSocketInput, RBFDriverNodeSocketInputMapping


class RBFDriverNodeInput:
    bl_width_default = 180



class RBFDriverNodeInputTransformChannel(RBFDriverNodeInput, RBFDriverNode, Node):
    bl_idname = 'RBFDriverNodeInputTransformChannel'
    bl_label = "Transform Channel"

    def transform_type_update(self, _=None):
        self.inputs[0].hide = not self.transform_type.startswith('ROT')
        self.invalidate()

    transform_type: EnumProperty(
        items=[
            ('LOC_X'  , "X Location", ""),
            ('LOC_Y'  , "Y Location", ""),
            ('LOC_Z'  , "Z Location", ""),
            ('ROT_W'  , "W Rotation", ""),
            ('ROT_X'  , "X Rotation", ""),
            ('ROT_Y'  , "Y Rotation", ""),
            ('ROT_Z'  , "Z Rotation", ""),
            ('SCALE_X', "X Scale"   , ""),
            ('SCALE_Y', "Y Scale"   , ""),
            ('SCALE_Z', "Z Scale"   , ""),
            ],
        default='LOC_X',
        options=set(),
        update=transform_type_update
        )

    def init(self, _: 'Context') -> None:
        self.inputs.new('RBFDriverNodeSocketRotationMode', "Mode").hide = True
        self.inputs.new('RBFDriverNodeSocketTransformTarget', "Target")
        self.inputs.new('RBFDriverNodeSocketTransformSpace', "Space")
        self.outputs.new('RBFDriverNodeSocketInput', "Input")

    def draw_buttons(self, _: 'Context', layout: 'UILayout') -> None:
        layout.prop(self, "transform_type", text="")

    def data(self, _: 'RBFDriverNodeSocketInput') -> Input:
        inputs = self.inputs
        return Input(
            type=InputType.TRANSFORMS,
            name=self.transform_type[-1].lower(),
            targets=({
                inputs[1].data().clone(transform_type=TransformType[self.transform_type],
                                       transform_space=inputs[2].data(),
                                       rotation_mode=inputs[0].data())
            },))

class RBFDriverNodeInputLocDiff(RBFDriverNodeInput, RBFDriverNode, Node):
    bl_idname = 'RBFDriverNodeInputLocDiff'
    bl_label = "Distance"

    def init(self, _) -> None:
        self.inputs.new('RBFDriverNodeSocketTransformTarget', "Target 1")
        self.inputs.new('RBFDriverNodeSocketTransformSpace', "Space 1")
        self.inputs.new('RBFDriverNodeSocketTransformTarget', "Target 2")
        self.inputs.new('RBFDriverNodeSocketTransformSpace', "Space 2")
        self.outputs.new('RBFDriverNodeSocketInput', "Input")

    def data(self, _: 'RBFDriverNodeSocketInput') -> Input:
        inputs = self.inputs
        return Input(
            type=InputType.LOC_DIFF,
            name="distance",
            targets=(
                inputs[0].data().clone(transform_space=inputs[1].data()),
                inputs[2].data().clone(transform_space=inputs[3].data()),
            )
        )


class RBFDriverNodeInputRotationDiff(RBFDriverNodeInput, RBFDriverNode, Node):
    bl_idname = 'RBFDriverNodeInputRotationDiff'
    bl_label = "Rotational Difference"

    def init(self, _: 'Context') -> None:
        self.inputs.new('RBFDriverNodeSocketTransformTarget', "Target 1").group = "A"
        self.inputs.new('RBFDriverNodeSocketTransformTarget', "Target 2").group = "B"
        self.outputs.new('RBFDriverNodeSocketInput', "Input")

    def data(self, _: 'RBFDriverNodeSocketInput') -> Input:
        return Input(
            type=InputType.ROTATION_DIFF,
            name="angle",
            targets=tuple(i.data() for i in self.inputs)
            )


class RBFDriverNodeInputTransformGroup:
    bl_width_default = 180

    use_x: BoolProperty(
        name="X",
        default=True,
        options=set(),
        update=lambda self, _: self.rebuild()
        )

    use_y: BoolProperty(
        name="Y",
        default=True,
        options=set(),
        update=lambda self, _: self.rebuild()
        )

    use_z: BoolProperty(
        name="Z",
        default=True,
        options=set(),
        update=lambda self, _: self.rebuild()
        )

    def init(self, context: 'Context') -> None:
        import bpy
        inputs = self.inputs
        inputs.new('RBFDriverNodeSocketTransformTarget', "Target")
        inputs.new('RBFDriverNodeSocketTransformSpace', "Space")
        self.outputs.new('RBFDriverNodeSocketInputMapping', "Inputs")
        tree = bpy.data.node_groups.new("RBFDriverInputTransformGroup", 'RBFDriverNodeTreeInput')
        tree.owner = self.id_data
        self.node_tree = tree
        self.rebuild()

    def draw_buttons(self, _: 'Context', layout: 'UILayout') -> None:
        row = layout.row(align=True)
        for axis in 'xyz':
            row.prop(self, f'use_{axis}')
        tree = self.node_tree
        if tree:
            row.operator("rbfdriver.group_edit", text="", icon='NODETREE').group_name=tree.name

    def rebuild(self, ttype: Optional[str]='LOC', dtype: Optional[str]='LOCATION', **props: Dict[str, Any]) -> None:
        tree = self.node_tree
        if tree:
            nodes = tree.nodes
            links = tree.links
            nodes.clear()
            links.clear()
            grp_i = nodes.new('NodeGroupInput')
            grp_o = nodes.new('NodeGroupOutput')
            flags = (self.use_x, self.use_y, self.use_z)
            count = sum(flags)
            if count:
                array = nodes.new('RBFDriverNodeInputMapping')
                # FIXME not carrying angles !!!
                if count == 3:
                    array.type = dtype
                else:
                    array.length = count
                links.new(array.outputs[0], grp_o.inputs[0])
                index = 0
                for axis, flag in zip('XYZ', flags):
                    if flag:
                        node = nodes.new('RBFDriverNodeInputTransformChannel')
                        node.name = axis
                        node.transform_type = f'{ttype}_{axis}'
                        for key, val in props.items():
                            setattr(node, key, val)
                        links.new(grp_i.outputs[0], node.inputs[1])
                        links.new(grp_i.outputs[1], node.inputs[2])
                        links.new(node.outputs[0], array.inputs[index])
                        index += 1


class RBFDriverNodeInputLocation(RBFDriverNodeInputTransformGroup, RBFDriverNodeGroup, NodeCustomGroup):
    bl_idname = 'RBFDriverNodeInputLocation'
    bl_label = "Input Location"

    def rebuild(self) -> None:
        super().rebuild('LOC')


class RBFDriverNodeInputScale(RBFDriverNodeInputTransformGroup, RBFDriverNodeGroup, NodeCustomGroup):
    bl_idname = 'RBFDriverNodeInputScale'
    bl_label = "Input Scale"

    def rebuild(self) -> None:
        super().rebuild('SCALE')


class RBFDriverNodeInputRotation(RBFDriverNodeInputTransformGroup, RBFDriverNodeGroup, NodeCustomGroup):
    bl_idname = 'RBFDriverNodeInputRotation'
    bl_label = "Input Rotation"

    def _updatemode(self, _) -> None:
        tree = self.node_tree
        if tree:
            mode = self.rotation_mode
            if mode == 'EULER':
                mode = self.rotation_order
            elif mode == 'SWING':
                mode = 'QUATERNION'
            elif mode == 'TWIST':
                mode = f'SWING_TWIST_{self.rotation_axis}'
            for node in tree.nodes:
                if isinstance(node, RBFDriverNodeInputTransformChannel):
                    node.rotation_mode == mode

    rotation_axis: EnumProperty(
        name="Axis",
        description="The axis of rotation",
        items=[
            ('X', "X", "X axis"),
            ('Y', "Y", "Y axis"),
            ('Z', "Z", "Z axis"),
            ],
        default='Y',
        options=set(),
        update=_updatemode
        )

    rotation_order: EnumProperty(
        name="Order",
        description="Rotation order",
        items=[
            ('AUTO', "Auto", "Euler using the rotation order of the target."),
            ('XYZ' , "XYZ" , "Euler using the XYZ rotation order."          ),
            ('XZY' , "XZY" , "Euler using the XZY rotation order."          ),
            ('YXZ' , "YXZ" , "Euler using the YXZ rotation order."          ),
            ('YZX' , "YZX" , "Euler using the YZX rotation order."          ),
            ('ZXY' , "ZXY" , "Euler using the ZXY rotation order."          ),
            ('ZYX' , "ZYX" , "Euler using the ZYX rotation order."          ),
            ],
        default='AUTO',
        options=set(),
        update=_updatemode
        )

    rotation_mode: EnumProperty(
        name="Mode",
        description="Rotation mode",
        items=[
            ('EULER'     , "Euler"     , "Euler angles"       ),
            ('QUATERNION', "Quaternion", "Quaternion rotation"),
            ('SWING'     , "Swing"     , "Swing rotation"     ),
            ('TWIST'     , "Twist"     , "Twist rotation"     ),
            ],
        default='EULER',
        options=set(),
        update=_updatemode
        )

    def rebuild(self) -> None:
        mode = self.rotation_mode
        if mode == 'EULER':
            super().rebuild('ROT', rotation_mode=self.rotation_order)
        elif mode == 'TWIST':
            # TODO
            pass
        else:
            tree = self.node_tree
            if tree:
                nodes = tree.nodes
                links = tree.links
                nodes.clear()
                links.clear()
                grp_i = nodes.new('NodeGroupInput')
                grp_o = nodes.new('NodeGroupOutput')
                array = nodes.new('RBFDriverNodeInputMapping')
                if mode == 'SWING':
                    mode = f'QUATERNION_AIM_{self.rotation_axis}'
                array.mode = mode
                links.new(array.outputs[0], grp_o.inputs[0])
                for index, axis in enumerate('WXYZ'):
                    node = nodes.new('RBFDriverNodeInputTransformChannel')
                    node.name = axis
                    node.rotation_mode = 'QUATERNION'
                    node.transform_type = f'ROT_{axis}'
                    links.new(grp_i.outputs[0], node.inputs[0])
                    links.new(grp_i.outputs[1], node.inputs[1])
                    links.new(node.outputs[0], array.inputs[index])

    def draw_buttons(self, context: 'Context', layout: 'UILayout') -> None:
        row = layout.row(align=True)
        row.prop(self, "rotation_mode", text="")
        mode = self.rotation_mode
        if mode == 'EULER':
            row = row.row(align=True)
            row.ui_units_x = 5
            row.prop(self, "rotation_order", text="")
            row = layout.row()
            for axis in 'xyz':
                row.prop(self, f'use_{axis}')
        elif mode in {'SWING', 'TWIST'}:
            row = row.row(align=True)
            row.ui_units_x = 4
            row.prop(self, "rotation_axis", text="")
        tree = self.node_tree
        if tree:
            row = row.row()
            row.operator('rbfdriver.group_edit', text="", icon='NODETREE').group_name=tree.name


class RBFDriverNodeInputMapping(RBFDriverNode, Node):
    bl_idname = 'RBFDriverNodeInputMapping'
    bl_label = "Input Mapping"
    bl_width_default = 120

    def _resize(self, size: int) -> Sequence['RBFDriverNodeSocketInput']:
        inputs = self.inputs
        while len(inputs) > size: inputs.remove(inputs[0])
        while len(inputs) < size: inputs.new('RBFDriverNodeSocketInput', str(len(inputs)))
        return inputs

    def _format(self, keys: Sequence[str]) -> None:
        for socket, name in zip(self._resize(len(keys)), keys):
            socket.name = name

    def _format_array(self) -> None:
        self._format(tuple(map(str, range(self.length))))

    def _format_location(self) -> None:
        self._format('XYZ')

    def _format_euler(self) -> None:
        self._format('XYZ')

    def _format_quaternion(self) -> None:
        self._format('WXYZ')

    def _format_quaternion_aim_x(self) -> None:
        self._format('WXYZ')

    def _format_quaternion_aim_y(self) -> None:
        self._format('WXYZ')

    def _format_quaternion_aim_z(self) -> None:
        self._format('WXYZ')

    def _format_color(self) -> None:
        self._format('RGB')

    def _update(self, _: 'Context') -> None:
        getattr(self, f'_format_{self.type.lower()}')()

    type: EnumProperty(
        items=[
            ('ARRAY', "Array", ""),
            ('LOCATION', "Location", ""),
            ('EULER', "Euler", ""),
            ('QUATERNION', "Quaternion", ""),
            ('QUATERNION_AIM_X', "Aim X", ""),
            ('QUATERNION_AIM_Y', "Aim Y", ""),
            ('QUATERNION_AIM_Z', "Aim Z", ""),
            ('COLOR', "Color", ""),
            ],
        default='ARRAY',
        options=set(),
        update=_update
        )

    length: IntProperty(
        name="Length",
        min=0,
        default=0,
        options=set(),
        update=_update
        )

    def init(self, context: 'Context') -> None:
        self["length"] = 1
        self.inputs.new('RBFDriverNodeSocketInput', "0")
        self.outputs.new('RBFDriverNodeSocketInputMapping', "Array")

    def data(self, _: 'RBFDriverNodeSocketInputMapping') -> InputMapping:
        return InputMapping(tuple(i.data() for i in self.inputs), VectorDataType[self.type])

    def draw_buttons(self, context: 'Context', layout: 'UILayout') -> None:
        row = layout.row(align=True)
        row.prop(self, "type", text="")
        if self.type == 'ARRAY':
            row = row.row(align=True)
            row.ui_units_x = 4
            row.prop(self, "length", text="")


class RBFDriverNodeTreeInput(RBFDriverNodeSubtree, NodeTree):
    bl_idname = 'RBFDriverNodeTreeInput'
    bl_label = "Input Transforms"


CLASSES = [
    RBFDriverNodeInputTransformChannel,
    RBFDriverNodeInputLocDiff,
    RBFDriverNodeInputRotationDiff,
    RBFDriverNodeInputMapping,
    RBFDriverNodeInputLocation,
    RBFDriverNodeInputRotation,
    RBFDriverNodeInputScale,
    RBFDriverNodeTreeInput,
]
