
from typing import Any
from bpy.types import ID, NodeSocket, NodeSocketInterface, Object, UILayout
from bpy.props import EnumProperty, PointerProperty, StringProperty
from ..data import IDType, Target, TransformSpace, TransformType, RotationMode
from ..core import RBFDriverNodeSocket, RBFDriverNodeSocketInterface, cache


class RBFDriverNodeSocketIDTarget(RBFDriverNodeSocket, NodeSocket):
    bl_idname = 'RBFDriverNodeSocketID'
    bl_label = "ID"

    @cache
    def data(self) -> Target:
        id_ = self.object
        if id_ is not None and self.id_type != 'OBJECT':
            id_ = id_.data if id_.type == self.id_type else None
        return Target(id_type=IDType[self.id_type], id=id_)

    id_type: EnumProperty(
        name="Type",
        items=[
            ('OBJECT'     , "Object"  , "", 'OBJECT_DATA',                0),
            ('MESH'       , "Mesh"    , "", 'MESH_DATA',                  1),
            ('CURVE'      , "Curve"   , "", 'CURVE_DATA',                 2),
            ('SURFACE'    , "Surface" , "", 'SURFACE_DATA',               3),
            ('META'       , "Metaball", "", 'META_DATA',                  4),
            ('FONT'       , "Font"    , "", 'FONT_DATA',                  5),
            ('HAIR'       , "Hair"    , "", 'HAIR_DATA',                  6),
            ('POINTCLOUD' , "Point"   , "", 'POINTCLOUD_DATA',            7),
            ('VOLUME'     , "Volume"  , "", 'VOLUME_DATA',                8),
            ('GPENCIL'    , "GPencil" , "", 'OUTLINER_DATA_GREASEPENCIL', 9),
            ('ARMATURE'   , "Armature", "", 'ARMATURE_DATA',              10),
            ('LATTICE'    , "Lattice" , "", 'LATTICE_DATA',               11),
            ('EMPTY'      , "Empty"   , "", 'EMPTY_DATA',                 12),
            ('LIGHT'      , "Light"   , "", 'LIGHT_DATA',                 13),
            ('LIGHT_PROBE', "Light"   , "", 'OUTLINER_DATA_LIGHTPROBE',   14),
            ('CAMERA'     , "Camera"  , "", 'CAMERA_DATA',                15),
            ('SPEAKER'    , "Speaker" , "", 'OUTLINER_DATA_SPEAKER',      16),
            ],
        default='OBJECT',
        update=RBFDriverNodeSocket.value_update,
        options=set()
        )

    object: PointerProperty(
        name="ID",
        type=ID,
        poll=lambda self, obj: self.id_type in {'OBJECT', obj.type},
        update=RBFDriverNodeSocket.value_update,
        options=set()
        )

    def draw_value(self, _0, layout, _1, _2):
        row = layout.row(align=True)
        row.prop(self, "id_type", text="", icon_only=True)
        obj = self.object
        row = row.row(align=True)
        row.alert = obj is not None and self.id_type not in {'OBJECT', obj.type}
        row.prop(self, "object", text="", icon=UILayout.enum_item_icon(self, "id_type", self.id_type))


class RBFDriverNodeSocketTransformTarget(RBFDriverNodeSocket, NodeSocket):
    bl_idname = 'RBFDriverNodeSocketTransformTarget'
    bl_label = "Target"

    bone_target: StringProperty(
        name="Bone",
        default="",
        options=set(),
        update=RBFDriverNodeSocket.value_update
        )

    @cache
    def data(self) -> Target:
        return Target(id_type=IDType.OBJECT, id=self.object, bone_target=self.bone_target)

    object: PointerProperty(
        name="Object",
        type=Object,
        options=set(),
        update=RBFDriverNodeSocket.value_update
        )

    def draw_value(self, context, layout, *_) -> None:
        col = layout.column()
        obj = self.object
        col.prop_search(self, "object", context.blend_data, "objects", text="", icon='OBJECT_DATA')
        if obj is not None and obj.type == 'ARMATURE':
            row = col.row()
            val = self.bone_target
            row.alert = bool(val) and val not in obj.data.bones
            row.prop_search(self, "bone_target", obj.data, "bones", text="", icon='BONE_DATA')


class RBFDriverNodeSocketRotationMode(RBFDriverNodeSocket, NodeSocket):
    bl_idname = 'RBFDriverNodeSocketRotationMode'
    bl_label = "Mode"

    @cache
    def data(self) -> RotationMode:
        return RotationMode[self.value]

    value: EnumProperty(
        name="Rotation Mode",
        items=[
            ('AUTO'         , "Auto Euler"       , "Euler using the rotation order of the target"                                  ),
            ('XYZ'          , "XYZ Euler"        , "Euler using the XYZ rotation order"                                            ),
            ('XZY'          , "XZY Euler"        , "Euler using the XZY rotation order"                                            ),
            ('YXZ'          , "YXZ Euler"        , "Euler using the YXZ rotation order"                                            ),
            ('YZX'          , "YZX Euler"        , "Euler using the YZX rotation order"                                            ),
            ('ZXY'          , "ZXY Euler"        , "Euler using the ZXY rotation order"                                            ),
            ('ZYX'          , "ZYX Euler"        , "Euler using the ZYX rotation order"                                            ),
            ('QUATERNION'   , "Quaternion"       , "Quaternion rotation"                                                           ),
            ('SWING_TWIST_X', "Swing and X Twist", "Decompose into a swing rotation to aim the X axis, followed by twist around it"),
            ('SWING_TWIST_Y', "Swing and Y Twist", "Decompose into a swing rotation to aim the Y axis, followed by twist around it"),
            ('SWING_TWIST_Z', "Swing and Z Twist", "Decompose into a swing rotation to aim the Z axis, followed by twist around it"),
            ],
        default='AUTO',
        options=set(),
        update=RBFDriverNodeSocket.value_update
        )

    def draw_value(self, _, layout, *__) -> None:
        layout.prop(self, "value", text="")


class RBFDriverNodeSocketTransformSpace(RBFDriverNodeSocket, NodeSocket):
    bl_idname = 'RBFDriverNodeSocketTransformSpace'
    bl_label = "Space"

    @cache
    def data(self) -> TransformSpace:
        return TransformSpace[self.value]

    value: EnumProperty(
        name="Transform Space",
        items=[
            ('WORLD_SPACE'    , "World Space"    , "Transforms include effects of parenting/restpose and constraints"    ),
            ('TRANSFORM_SPACE', "Transform Space", "Transforms don't include parenting/restpose or constraints"          ),
            ('LOCAL_SPACE'    , "Local Space"    , "Transforms include effects of constraints but not parenting/restpose"),
            ],
        default='WORLD_SPACE',
        options=set(),
        update=RBFDriverNodeSocket.value_update
        )

    def draw_value(self, _, layout, *__) -> None:
        layout.prop(self, "value", text="")


class RBFDriverNodeSocketIDTargetInterface(RBFDriverNodeSocketInterface, NodeSocketInterface):
    bl_idname = 'RBFDriverNodeSocketIDTargetInterface'
    bl_socket_idname = RBFDriverNodeSocketIDTarget.bl_idname
    bl_label = RBFDriverNodeSocketIDTarget.bl_label


class RBFDriverNodeSocketTransformTargetInterface(RBFDriverNodeSocketInterface, NodeSocketInterface):
    bl_idname = 'RBFDriverNodeSocketTransformTargetInterface'
    bl_socket_idname = RBFDriverNodeSocketTransformTarget.bl_idname
    bl_label = RBFDriverNodeSocketTransformTarget.bl_label


class RBFDriverNodeSocketTransformSpaceInterface(RBFDriverNodeSocketInterface, NodeSocketInterface):
    bl_socket_idname = RBFDriverNodeSocketTransformSpace.bl_idname
    bl_idname = 'RBFDriverNodeSocketTransformSpaceInterface'
    bl_label = RBFDriverNodeSocketTransformSpace.bl_label


class RBFDriverNodeSocketRotationModeInterface(RBFDriverNodeSocketInterface, NodeSocketInterface):
    bl_idname = 'RBFDriverNodeSocketRotationModeInterface'
    bl_socket_idname = RBFDriverNodeSocketRotationMode.bl_idname
    bl_label = RBFDriverNodeSocketRotationMode.bl_label


CLASSES = [
    RBFDriverNodeSocketIDTarget,
    RBFDriverNodeSocketTransformTarget,
    RBFDriverNodeSocketRotationMode,
    RBFDriverNodeSocketTransformSpace,
    RBFDriverNodeSocketIDTargetInterface,
    RBFDriverNodeSocketTransformTargetInterface,
    RBFDriverNodeSocketTransformSpaceInterface,
    RBFDriverNodeSocketRotationModeInterface,
]