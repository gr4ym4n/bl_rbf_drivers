
from bpy.types import NodeCustomGroup
from bpy.props import EnumProperty
from .base import RBFDriverNodeGroup


class RBFDriverNodeGroupPoseGroup(RBFDriverNodeGroup, NodeCustomGroup):
    bl_idname = 'RBFDriverNodeGroupPoseGroup'
    bl_label = "Pose Group"
    bl_width_default = 240

    def _get_data_type(self):
        return self.get("data_type", 0)

    def _set_data_type(self, value: int):
        pass

    data_type: EnumProperty(
        items=[
            ('FLOAT', "Float", ""),
            ('ANGLE', "Angle", ""),
            ('ARRAY', "Array", ""),
            ('LOCATION', "Location", ""),
            ('EULER', "Euler", ""),
            ('QUATERNION', "Quaternion", ""),
            ('SCALE', "Scale", ""),
            ],
        get=_get_data_type,
        set=_set_data_type,
        options=set()
        )

    def build(self, *_):
        import bpy
        ntree = bpy.data.node_groups.new('RBFDriverPoseGroup', 'RBFDriverNodeTreePoseGroup')
        ntree.parent__internal__ = self.id_data
        ntree.inputs.new('RBFDriverNodeSocketVariableGroup', "Variables")
        self.node_tree = ntree

    def draw_buttons(self, _, layout):
        row = layout.row()
        

    def evaluate(self):
        pass