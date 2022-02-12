
import uuid
import bpy

ID_TYPE_ITEMS = [
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
    ('KEY'        , "Key"     , "", 'SHAPEKEY_DATA',              17),
]

ID_TYPE_INDEX = {
    item[0]: item[4] for item in ID_TYPE_ITEMS
    }

LAYER_TYPE_ITEMS = [
    ('NONE'     , "Single Property" , "RNA property value"         , 'NONE', 0),
    ('LOCATION' , "Location"        , "Location transform channels", 'NONE', 1),
    ('ROTATION' , "Rotation"        , "Rotation transform channels", 'NONE', 2),
    ('SCALE'    , "Scale"           , "Scale transform channels"   , 'NONE', 3),
    ('BBONE'    , "BBone Properties", "BBone property values"      , 'NONE', 4),
    ('SHAPE_KEY', "Shape Key(s)"    , "Shape key values"           , 'NONE', 5),
    ]

LAYER_TYPE_INDEX = {
    item[0]: item[4] for item in LAYER_TYPE_ITEMS
    }

class Identifiable:

    def _get_identifier(pgroup: 'Identifiable') -> str:
        value = bpy.types.PropertyGroup.get(pgroup, "identifier")
        if not value:
            value = uuid.uuid4().hex
            bpy.types.PropertyGroup.__setitem__(pgroup, "identifier", value)
        return value

    identifier: bpy.props.StringProperty(
        name="Identifier",
        description="Unique data identifier",
        get=_get_identifier,
        options={'HIDDEN'}
        )
