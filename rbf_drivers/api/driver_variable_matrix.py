
from typing import Optional, TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import PointerProperty
import numpy as np
from .driver_variable_matrix_property import RBFDriverVariableMatrixProperty
from .mixins import Matrix
if TYPE_CHECKING:
    from .pose_weight_driver import RBFDriverPoseWeightDriver
    from .pose import RBFDriverPose
    from .driver import RBFDriver

class RBFDriverVariableMatrix(Matrix, PropertyGroup):

    id_property: PointerProperty(
        name="Property",
        type=RBFDriverVariableMatrixProperty,
        optinos=set()
        )

    @property
    def rbf_driver(self) -> 'RBFDriver':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])

    def update(self, propagate: Optional[bool]=True) -> None:
        distance_matrix = self.rbf_driver.distance_matrix.to_array()

        if len(distance_matrix) == 0:
            self.__init__([])
        else:
            identity_matrix = np.identity(distance_matrix.shape[0], dtype=float)
            try:
                solution = np.linalg.solve(distance_matrix, identity_matrix)
            except np.linalg.LinAlgError:
                solution = np.linalg.lstsq(distance_matrix, identity_matrix, rcond=None)[0]

            self.__init__(solution)

        idprop: RBFDriverVariableMatrixProperty = self.id_property
        idprop.update()

        if propagate:
            pose: RBFDriverPose
            for pose in self.rbf_driver.poses:
                driver: RBFDriverPoseWeightDriver = pose.weight.driver
                driver.update()
