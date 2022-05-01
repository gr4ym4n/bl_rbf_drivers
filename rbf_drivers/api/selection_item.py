
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, StringProperty

class RBFDriverSelectionItem(PropertyGroup):

    icon: StringProperty(
        name="Icon",
        default='',
        options=set()
        )

    selected: BoolProperty(
        name="Select",
        default=False,
        options=set()
        )
