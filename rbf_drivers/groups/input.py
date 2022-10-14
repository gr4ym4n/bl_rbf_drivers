
from typing import TYPE_CHECKING, Any, Dict, Tuple, Union
from bpy.types import NodeCustomGroup
from bpy.props import BoolProperty, EnumProperty
from .base import RBFDriverNodeGroup
from ..utils.layout import layout_nodes_columns
if TYPE_CHECKING:
    from bpy.types import Context, NodeGroupOutput, UILayout
    from ..nodes.variable import RBFDriverNodeVariable
    from ..nodes.vector import RBFDriverNodeVector
    from ..trees.input import RBFDriverNodeTreeInput


def io_clear(ntree):
    ntree.inputs.clear()
    ntree.outputs.clear()


def io_xform(ntree):
    io_clear(ntree)
    inputs = ntree.inputs
    inputs.new('RBFDriverNodeSocketTransformTarget', "Target")
    inputs.new('RBFDriverNodeSocketTransformSpace', "Space")
    ntree.outputs.new('RBFDriverNodeSocketVector', "Vector")


def io_ldiff(ntree):
    io_clear(ntree)
    inputs = ntree.inputs
    inputs.new('RBFDriverNodeSocketTransformTarget', "Target 1")
    inputs.new('RBFDriverNodeSocketTransformSpace', "Space 1")
    inputs.new('RBFDriverNodeSocketTransformTarget', "Target 2")
    inputs.new('RBFDriverNodeSocketTransformSpace', "Space 2")
    ntree.outputs.new('RBFDriverNodeSocketVector', "Vector")


def io_rdiff(ntree):
    io_clear(ntree)
    inputs = ntree.inputs
    inputs.new('RBFDriverNodeSocketTransformTarget', "Target 1")
    inputs.new('RBFDriverNodeSocketTransformTarget', "Target 2")
    ntree.outputs.new('RBFDriverNodeSocketVector', "Vector")


def io_nodes(ntree):
    nodes = ntree.nodes
    i = nodes.new('NodeGroupInput')
    o = nodes.new('NodeGroupOutput')
    i.location = (-400, 0)
    o.location = (400, 0)
    return i, o


def nt_reset(ntree):
    ntree.nodes.clear()
    ntree.links.clear()
    return (ntree,) + io_nodes(ntree)


def nt_xform(ntree):
    io_xform(ntree)
    return nt_reset(ntree)


def vec_init(ntree: 'RBFDriverNodeTreeInput',
             onode: 'NodeGroupOutput',
             dtype: Union[int, str]) -> 'RBFDriverNodeVector':
    node = ntree.nodes.new('RBFDriverNodeVector')
    node.location = (120, 0)
    if isinstance(dtype, str):
        node.inputs[0].default_subtype = dtype
    else:
        node.inputs[0].default_size = dtype
    ntree.links.new(node.outputs[0], onode.inputs[0])
    return node


def var_init(ntree: 'RBFDriverNodeTreeInput', **attrs: Dict[str, Any]) -> 'RBFDriverNodeVariable':
    node = ntree.nodes.new('RBFDriverNodeVariable')
    for key, val in attrs.items():
        setattr(node, key, val)
    return node


def xyz_update(group: 'RBFDriverNodeGroupInput', dtype: str, ttype: str, **opt: Dict[str, Any]) -> None:
    ntree, inode, onode = nt_xform(group.node_tree)
    flags = (group.use_x, group.use_y, group.use_z)
    count = sum(flags)
    if count:
        vec = vec_init(ntree, onode, count if count != 3 else dtype)
        idx = 1
        for axis, flag in zip('XYZ', flags):
            if flag:
                var = var_init(ntree, name=axis, type='TRANSFORMS', transform_type=f'{ttype}_{axis}', **opt)
                ntree.links.new(inode.outputs[0], var.inputs[0])
                ntree.links.new(inode.outputs[1], var.inputs[1])
                ntree.links.new(var.outputs[0], vec.inputs[idx])
                idx += 1


def loc_update(group: 'RBFDriverNodeGroupInput') -> None:
    xyz_update(group, 'LOCATION', 'LOC')


def rot_update(group: 'RBFDriverNodeGroupInput') -> None:
    mode = group.rotation_mode
    if mode == 'EULER':
        xyz_update(group, 'EULER', 'ROT', rotation_mode=group.rotation_order)
    else:
        ntree, inode, onode = nt_xform(group.node_tree)
        links = ntree.links
        if mode == 'TWIST':
            key = group.rotation_axis
            vec = vec_init(ntree, onode, 1)
            var = var_init(ntree,
                           name=key,
                           type='TRANSFORMS',
                           transform_type=f'ROT_{key}',
                           rotation_mode=f'SWING_TWIST_{key}')
            links.new(inode.outputs[0], var.inputs[0])
            links.new(inode.outputs[1], var.inputs[1])
            links.new(var.outputs[0], vec.inputs[1])
        else:
            vec = vec_init(ntree, onode, 'QUATERNION')
            for i, axis in enumerate('WXYZ'):
                var = var_init(ntree,
                            name=axis,
                            type='TRANSFORMS',
                            transform_type=f'ROT_{axis}',
                            rotation_mode='QUATERNION')
                links.new(inode.outputs[0], var.inputs[0])
                links.new(inode.outputs[1], var.inputs[1])
                links.new(var.outputs[0], vec.inputs[i+1])


def scale_update(group: 'RBFDriverNodeGroupInput') -> None:
    xyz_update(group, 'SCALE', 'SCALE')


def type_update(group: 'RBFDriverNodeGroupInput', _) -> None:
    t = group.type
    if   t == 'LOCATION' : loc_update(group)
    elif t == 'ROTATION' : rot_update(group)
    elif t == 'SCALE'    : scale_update(group)

    if t != 'USER_DEF':
        nodes = group.node_tree.nodes
        layout_nodes_columns([
            [n for n in nodes if n.bl_idname == 'NodeGroupInput'],
            [n for n in nodes if n.bl_idname == 'RBFDriverNodeVariable'],
            [n for n in nodes if n.bl_idname == 'RBFDriverNodeVector'],
            [n for n in nodes if n.bl_idname == 'NodeGroupOutput']
            ], spacing=(80, 100))


class RBFDriverNodeGroupInput(RBFDriverNodeGroup, NodeCustomGroup):
    bl_idname = 'RBFDriverNodeGroupInput'
    bl_label = "Input"
    nt_name = "Input"
    nt_type = 'RBFDriverNodeTreeInput'

    TYPES = [
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
        update=type_update
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
        update=type_update
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
        update=type_update
        )

    type: EnumProperty(
        name="Type",
        items=TYPES,
        default='LOCATION',
        options=set(),
        update=type_update
        )

    use_x: BoolProperty(
        name="X",
        default=False,
        options=set(),
        update=type_update
        )

    use_y: BoolProperty(
        name="Y",
        default=False,
        options=set(),
        update=type_update
        )

    use_z: BoolProperty(
        name="Z",
        default=False,
        options=set(),
        update=type_update
        )

    def init(self, _) -> None:
        super().init(_)
        type_update(self, _)

    def draw_buttons(self, context: 'Context', layout: 'UILayout') -> None:
        row = layout.row(align=True)
        row.prop(self, "type", text="")
        super().draw_buttons(context, row, text="")
        if self.type in {'LOCATION', 'SCALE'}:
            row = layout.row(align=True)
            for axis in 'xyz':
                row.prop(self, f'use_{axis}', toggle=True)
        elif self.type == 'ROTATION':
            row = layout.row(align=True)
            row.prop(self, "rotation_mode", text="")
            mode = self.rotation_mode
            if mode == 'EULER':
                row = row.row(align=True)
                row.ui_units_x = 5
                row.prop(self, "rotation_order", text="")
                row = layout.row(align=True)
                for axis in 'xyz':
                    row.prop(self, f'use_{axis}', toggle=True)
            elif mode in {'SWING', 'TWIST'}:
                row = row.row(align=True)
                row.ui_units_x = 4
                row.prop(self, "rotation_axis", text="")
            