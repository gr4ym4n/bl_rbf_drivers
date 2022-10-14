
from itertools import repeat
from typing import TYPE_CHECKING, Any, Optional, Set, Tuple, Union
from bpy.types import Node, NodeCustomGroup, NodeSocket, NodeTree, Operator, UIList
from bpy.props import EnumProperty, FloatVectorProperty, IntProperty, StringProperty
from mathutils import Quaternion
from ..data import Input, InputMapping, VectorDataType
from ..core import RBFDriverNode, RBFDriverNodeGroup, RBFDriverNodeSubtree, RBFDriverNodeSocket, RBFDriverNodeSocketInterface, cache
from ..sockets.input import RBFDriverNodeSocketInput, RBFDriverNodeSocketInputMapping
from .matrix import RBFDriverNodeMatrix
if TYPE_CHECKING:
    from bpy.types import Context, UILayout
    from ..sockets.array import RBFDriverNodeSocketArray
    from .array import RBFDriverNodeArray


class RBFDriverPoseGroupAdd(Operator):
    bl_idname = 'rbfdriver.pose_group_add'
    bl_label = "Add"
    bl_options = {'INTERNAL'}

    node_name: StringProperty()

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        space = context.space_data
        if space is not None:
            tree = getattr(space, "node_tree", None)
            return tree is not None and tree.bl_idname.startswith('RBFDriverNodeTree')
        return False

    def execute(self, context: 'Context') -> Set[str]:
        group = context.space_data.node_tree.nodes.get(self.node_name)

        if group is None:
            self.report({'ERROR'}, f'Node "{self.node_name}" not found')
            return {'CANCELLED'}

        if not isinstance(group, RBFDriverNodePoseGroup):
            self.report({'ERROR'}, f'Node "{self.node_name}" is not a pose group node')
            return {'CANCELLED'}

        tree = group.node_tree
        
        if tree is None:
            self.report({'ERROR'}, "")
            return {'CANCELLED'}

        if not isinstance(tree, RBFDriverNodeTreePoseGroup):
            self.report({'ERROR'}, "")
            return {'CANCELLED'}

        poses = tree.nodes.get("Poses")

        if poses is None:
            self.report({'ERROR'}, "")
            return {'CANCELLED'}

        if not isinstance(poses, RBFDriverNodeMatrix):
            self.report({'ERROR'}, "")
            return {'CANCELLED'}

        node = tree.nodes.new('RBFDriverNodePose')
        node.name = "Pose"
        # TODO set up node according to input
        input_ = poses.inputs.new('RBFDriverNodeSocketArray', node.name)
        tree.links.new(node.outputs[0], input_)
        return {'FINISHED'}


class RBFDriverPoseList(UIList):
    bl_idname = 'RBFDRIVER_UL_poses'

    def draw_item(self, _0,
                  layout: 'UILayout', _1,
                  socket: 'RBFDriverNodeSocketArray', _2, _3, _4) -> None:
        layout.prop(socket, "name", text="", emboss=False, translate=False)


class RBFDriverNodeSocketPoseInput(RBFDriverNodeSocket, NodeSocket):
    bl_idname = 'RBFDriverNodeSocketPoseInput'
    bl_label = "Input"

    # TODO make sure input mapping adheres to max 32 items
    length: IntProperty(
        name="Length",
        min=0,
        max=32,
        options=set(),
        update=RBFDriverNodeSocket.value_update
        )

    type: EnumProperty(
        items=[
            ('ARRAY', "Array", ""),
            ('LOCATION', "Location", ""),
            ('EULER', "Euler", ""),
            ('QUATERNION', "Quaternion", ""),
            ('AXIS_ANGLE', "Axis/Angle", ""),
            ('SCALE', "Scale", ""),
            ('COLOR', "Color", ""),
            ],
        options=set(),
        update=RBFDriverNodeSocket.value_update
        )

    @cache
    def data(self) -> Optional[Union[Input, InputMapping]]:
        type_ = self.type
        if type_ == 'ARRAY':
            return InputMapping(tuple(repeat(Input(), self.length)))
        size = 3 + type_ == 'QUATERNION'
        return InputMapping(tuple(repeat(Input(), size), VectorDataType[type_]))

    def draw_value(self, context: 'Context', layout: 'UILayout', node: 'Node', text: str) -> None:
        row = layout.row(align=True)
        row.prop(self, "type", text="")
        if self.type == 'ARRAY':
            row = row.row(align=True)
            row.ui_units_x = 4
            row.prop(self, "length", text="")

    def validate(self, output: 'RBFDriverNodeSocket') -> None:
        return isinstance(output, (RBFDriverNodeSocketInput, RBFDriverNodeSocketInputMapping))


class RBFDriverNodePose(RBFDriverNode, Node):
    bl_idname = 'RBFDriverNodePose'
    bl_label = "Pose"

    length: IntProperty(
        name="Length",
        min=0,
        default=0,
        max=32,
        options=set(),
        )

    value: FloatVectorProperty(
        name="Value",
        size=32,
        options=set(),
        update=RBFDriverNode.value_update
        )

    def _get3(self) -> Tuple[float, float, float]:
        return tuple(self.value[:3])

    def _set3(self, value: Tuple[float, float, float]) -> None:
        self.value[:3] = value

    def _get4(self) -> Tuple[float, float, float, float]:
        return tuple(self.value[:4])

    def _set4(self, value: Tuple[float, float, float, float]) -> None:
        self.value[:4] = value

    value_axis_angle: FloatVectorProperty(
        name="Value",
        size=4,
        get=_get4,
        set=_set4,
        subtype='AXISANGLE',
        options=set()
        )

    value_location: FloatVectorProperty(
        name="Value",
        get=_get3,
        set=_set3,
        subtype='TRANSLATION',
        options=set()
        )

    value_quaternion: FloatVectorProperty(
        name="Value",
        size=4,
        get=_get4,
        set=_set4,
        subtype='QUATERNION',
        options=set()
        )

    value_scale: FloatVectorProperty(
        name="Value",
        get=_get3,
        set=_set3,
        subtype='XYZ',
        options=set()
        )

    value_color: FloatVectorProperty(
        name="Value",
        get=_get3,
        set=_set3,
        subtype='COLOR',
        options=set()
        )

    def input_update(self, socket: RBFDriverNodeSocketPoseInput) -> None:
        data = socket.data()
        if isinstance(data, Input):
            data = InputMapping((data,), VectorDataType.ARRAY)
        prev = self.type
        curr = socket.data().type.name
        if prev == curr:
            if prev == 'ARRAY':
                self.length = len(data.inputs)
            return
        if curr != 'ARRAY':
            self.length = 3 + (curr in {'QUATERNION', 'AXIS_ANGLE'})
        rot = {'EULER', 'QUATERNION', 'EULER'}
        if prev in rot and curr in rot:
            if prev == 'QUATERNION':
                q = self.quaternion
            if prev == 'AXIS_ANGLE':
                q = Quaternion(self.value[1:4], self.value[0])
            else:
                q = self.euler.to_quaternion()
            if curr == 'QUATERNION':
                self.quaternion = q
            elif curr == 'AXIS_ANGLE':
                axis, angle = q.to_axis_angle()
                self.axis_angle = (angle,) + tuple(axis)
            else:
                self.euler = q.to_euler()
        elif curr == 'COLOR':
            self.color = tuple(min(1., max(x, 0.)) for x in self.value[:3])

    type: EnumProperty(
        items=[
            ('ARRAY', "Array", ""),
            ('LOCATION', "Location", ""),
            ('EULER', "Euler", ""),
            ('QUATERNION', "Quaternion", ""),
            ('AXIS_ANGLE', "Axis/Angle", ""),
            ('SCALE', "Scale", ""),
            ('COLOR', "Color", ""),
            ],
        default='ARRAY',
        options={'HIDDEN'},
        )

    def init(self, _: 'Context') -> None:
        self.inputs.new('RBFDriverNodeSocketPoseInput', "Input")
        self.outputs.new('RBFDriverNodeSocketArray', "Pose")

    def data(self, _: 'RBFDriverNodeSocketArray') -> Tuple[float, ...]:
        type_ = self.type
        return tuple(self.value[:self.length] if type_ == 'ARRAY' else getattr(self, f'value_{type_.lower()}'))

    def draw_buttons(self, _: 'Context', layout: 'UILayout') -> None:
        type_ = self.type
        col = layout.column(align=True)
        if type_ == 'ARRAY':
            for index in range(self.length):
                col.prop(self, "value", index=index, text=str(index))
        else:
            col.prop(self, f'value_{self.type.lower()}', text="")   


class RBFDriverNodePoseGroup(RBFDriverNodeGroup, NodeCustomGroup):
    bl_idname = 'RBFDriverNodePoseGroup'
    bl_label = "Pose Group"
    bl_width_default = 240

    active_pose_index: IntProperty(
        min=0,
        default=0,
        options=set()
        )

    @property
    def active_pose(self) -> Optional['RBFDriverNodeArray']:
        tree = self.node_tree
        if tree:
            node = tree.nodes.get("Poses")
            if node:
                index = self.active_pose_index
                if index < len(node.inputs):
                    return next(iter(node.inputs[index].edge), None)

    def init(self, _: 'Context') -> None:
        import bpy
        tree = bpy.data.node_groups.new("RBFDriverPoseGroup", 'RBFDriverNodeTreePoseGroup')
        tree.owner = self.id_data
        self.node_tree = tree

        nodes = tree.nodes
        links = tree.links

        grp_i = nodes.new('NodeGroupInput')
        grp_o = nodes.new('NodeGroupOutput')

        poses = nodes.new('RBFDriverNodeMatrix')
        poses.length = 1
        poses.name = "Poses"

        # self.inputs.new('RBFDriverNodeSocketPoseInput', "Input")
        # self.outputs.new('RBFDriverNodeSocketMatrix', "Poses")

        pose = nodes.new('RBFDriverNodePose')
        pose.name = "Pose"

        links.new(grp_i.outputs[0], pose.inputs[0])
        links.new(pose.outputs[0], poses.inputs[0])
        links.new(poses.outputs[0], grp_o.inputs[0])

    def draw_buttons(self, _: 'Context', layout: 'UILayout') -> None:
        tree = self.node_tree
        if tree:
            node = tree.nodes.get("Poses")
            if node:
                row = layout.row()
                col = row.column()
                col.template_list('RBFDRIVER_UL_poses', self.name, node, "inputs", self, "active_pose_index")
                col = row.column(align=True)
                col.operator('rbfdriver.pose_group_add', text="", icon='ADD').node_name=self.name
                col.separator()
                col.operator('rbfdriver.group_edit', text="", icon='NODETREE').group_name=tree.name
                pose = self.active_pose
                if pose:
                    pass


class RBFDriverNodeTreePoseGroup(RBFDriverNodeSubtree, NodeTree):
    bl_idname = 'RBFDriverNodeTreePoseGroup'
    bl_label = "Pose Group"


CLASSES = [
    RBFDriverPoseGroupAdd,
    RBFDriverPoseList,
    RBFDriverNodeSocketPoseInput,
    RBFDriverNodePose,
    RBFDriverNodePoseGroup,
    RBFDriverNodeTreePoseGroup,
    ]
