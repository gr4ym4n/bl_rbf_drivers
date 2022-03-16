
from typing import TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import StringProperty
from .mixins import IDPropertyTarget
if TYPE_CHECKING:
    from .driver import RBFDriver

def driver_variable_matrix_property_name(prop: 'RBFDriverVariableMatrixProperty') -> str:
    return f'rbfn_pvmat_{prop.rbf_driver.identifier}'

class RBFDriverVariableMatrixProperty(IDPropertyTarget, PropertyGroup):

    name: StringProperty(
        name="Name",
        get=driver_variable_matrix_property_name,
        options=set()
        )

    @property
    def rbf_driver(self) -> 'RBFDriver':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".variable_matrix.")[0])

    def update(self) -> None:
        self.id[self.name] = list(self.rbf_driver.variable_matrix.to_array().flat)
