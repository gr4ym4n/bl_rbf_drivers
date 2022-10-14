
from typing import List, Optional, Tuple, TYPE_CHECKING, Union
import bpy
from .mixins import Labeled
if TYPE_CHECKING:
    from ..mixins import RBFDNode

ID_TYPE_ITEMS: List[Tuple[str, str, str, str, int]] = [
    ('OBJECT'     , "Object"  , "", 'OBJECT_DATA',                0),
    ('MESH'       , "Mesh"    , "", 'MESH_DATA',                  1),
    ('CURVE'      , "Curve"   , "", 'CURVE_DATA',                 2),
    ('SURFACE'    , "Surface" , "", 'SURFACE_DATA',               3),
    ('META'       , "Metaball", "", 'META_DATA',                  4),
    ('FONT'       , "Font"    , "", 'FONT_DATA',                  5),
    ('POINTCLOUD' , "Point"   , "", 'POINTCLOUD_DATA',            6),
    ('VOLUME'     , "Volume"  , "", 'VOLUME_DATA',                7),
    ('GPENCIL'    , "GPencil" , "", 'OUTLINER_DATA_GREASEPENCIL', 8),
    ('ARMATURE'   , "Armature", "", 'ARMATURE_DATA',              9),
    ('LATTICE'    , "Lattice" , "", 'LATTICE_DATA',               10),
    ('LIGHT'      , "Light"   , "", 'LIGHT_DATA',                 11),
    ('LIGHT_PROBE', "Light"   , "", 'OUTLINER_DATA_LIGHTPROBE',   12),
    ('CAMERA'     , "Camera"  , "", 'CAMERA_DATA',                13),
    ('SPEAKER'    , "Speaker" , "", 'OUTLINER_DATA_SPEAKER',      14),
    ('KEY'        , "Key"     , "", 'SHAPEKEY_DATA',              15),
    ]

ID_TYPE_TABLE = {
    _item[0]: _item[4] for _item in ID_TYPE_ITEMS
    }

ID_TYPE_ICONS = {
    _item[0]: _item[3] for _item in ID_TYPE_ITEMS
    }

ID_TYPE_FIELD = {
    'OBJECT'      : 'objects',
    'MESH'        : 'meshes',
    'CURVE'       : 'curves',
    'SURFACE'     : 'curves',
    'META'        : 'metaballs',
    'FONT'        : 'fonts',
    'POINTCLOUD'  : 'pointclouds',
    'VOLUME'      : 'volumes',
    'GPENCIL'     : 'grease_pencils',
    'ARMATURE'    : 'armatures',
    'LATTICE'     : 'lattices',
    'LIGHT'       : 'lights',
    'LIGHT_PROBE' : 'lightprobes',
    'CAMERA'      : 'cameras',
    'SPEAKER'     : 'speakers',
    'KEY'         : 'shape_keys',
}


def update_callback(socket: 'RBFDTargetSocket', _: Optional[bpy.types.Context]=None) -> None:
    node: 'RBFDNode' = socket.node
    if socket.is_output:
        for link in socket.links:
            input_ = link.to_socket
            if isinstance(input_, socket.__class__):
                input_["id_type"] = id_type_get(socket)
                input_["id"] = socket.id
                input_["bone_target"] = socket.bone_target
                node: 'RBFDNode' = link.to_node
                node.on_input_value_update(input_)


def id_type_get(socket: 'RBFDTargetSocket') -> int:
    return socket.get("id_type", ID_TYPE_TABLE['OBJECT'])


def id_type_set(socket: 'RBFDTargetSocket', value: int) -> None:
    if id_type_get(socket) != value:
        socket["id_type"] = value
        socket["id"] = None
        update_callback(socket)


class RBFDTargetSocket(Labeled, bpy.types.NodeSocket):
    bl_idname = 'RBFDTargetSocket'
    bl_label = "Target"

    bone_target: bpy.props.StringProperty(
        name="Bone",
        default="",
        options=set(),
        update=update_callback
        )

    id_type: bpy.props.EnumProperty(
        name="Type",
        items=ID_TYPE_ITEMS,
        get=id_type_get,
        set=id_type_set,
        )

    id: bpy.props.PointerProperty(
        name="ID",
        type=bpy.types.ID,
        options=set(),
        update=update_callback
        )

    def draw(self, context: bpy.types.Context, layout: bpy.types.UILayout, node: bpy.types.Node, text: str) -> None:
        if self.is_output:
            layout.label(text=text)

    def draw_color(self, context: bpy.types.Context, node: bpy.types.Node) -> Tuple[float, float, float, float]:
        return (1.0, 0.0, 0.0, 0.0)

    def resolve(self) -> Optional[Union[bpy.types.Object, bpy.types.PoseBone]]:
        res = self.id
        if (res is not None
                and isinstance(res, bpy.types.Object)
                and res.type == 'ARMATURE'
                and self.bone_target):
            res = res.pose.bones.get(self.bone_target)
        return res
