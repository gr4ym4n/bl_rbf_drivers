
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, EnumProperty, PointerProperty
from .mixins import Symmetrical
from .inputs import RBFDriverInputs
from .poses import RBFDriverPoses
from .outputs import RBFDriverOutputs
from .driver_interpolation import RBFDriverInterpolation


DRIVER_TYPE_ITEMS = [
    ('NONE'      , "Generic"   , "", 'DRIVER'       , 0),
    ('SHAPE_KEYS', "Shape Keys", "", 'SHAPEKEY_DATA', 1),
    ]

DRIVER_TYPE_INDEX = {
    item[0]: item[4] for item in DRIVER_TYPE_ITEMS
    }

class RBFDriver(Symmetrical, PropertyGroup):

    interpolation: PointerProperty(
        name="Falloff",
        type=RBFDriverInterpolation,
        options=set()
        )

    inputs: PointerProperty(
        name="Inputs",
        type=RBFDriverInputs,
        options=set()
        )

    outputs: PointerProperty(
        name="Outputs",
        type=RBFDriverOutputs,
        options=set()
        )

    poses: PointerProperty(
        name="Poses",
        type=RBFDriverPoses,
        options=set()
        )

    symmetry_lock__internal__: BoolProperty(
        default=False,
        options={'HIDDEN'}
        )

    type: EnumProperty(
        name="Type",
        items=DRIVER_TYPE_ITEMS,
        get=lambda self: self.get("type", 0),
        options=set()
        )
