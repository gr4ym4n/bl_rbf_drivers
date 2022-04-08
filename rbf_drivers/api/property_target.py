
from typing import Optional
from bpy.types import ID, PropertyGroup
from bpy.props import IntProperty, StringProperty
from idprop.types import IDPropertyArray

class RBFDriverPropertyTarget(PropertyGroup):

    array_index: IntProperty(
        name="Index",
        min=0,
        get=lambda self: self.get("array_index", 0),
        options=set()
        )

    @property
    def is_array(self) -> bool:
        return self.is_property_set("array_index")

    name: StringProperty(
        name="Name",
        get=lambda self: self.get("name", ""),
        options=set()
        )

    @property
    def data_path(self) -> str:
        return f'["{self.name}"]'

    @property
    def id_type(self) -> str:
        return self.id_data.type

    @property
    def id(self) -> ID:
        return self.id_data.data

    @property
    def is_valid(self) -> bool:
        return isinstance(self.value, float)

    @property
    def value(self) -> Optional[float]:
        value = self.id.get(self.name, None)

        if self.is_array and isinstance(value, IDPropertyArray):
            index = self.array_index
            value = value[index] if index < len(value) else None

        if isinstance(value, float):
            return value
