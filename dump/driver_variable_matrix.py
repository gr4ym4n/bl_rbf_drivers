
from typing import Optional, TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import StringProperty
import numpy as np
from rbf_drivers.lib.curve_mapping import nodetree_node_ensure
from ..rbf_drivers.api.mixins import Matrix
from ..rbf_drivers.app.events import dataclass, dispatch_event, Event
from ..rbf_drivers.app.utils import owner_resolve
if TYPE_CHECKING:
    from ..rbf_drivers.api.pose_interpolation import RBFDriverPoseFalloff
    from ..rbf_drivers.api.driver import RBFDriver


@dataclass(frozen=True)
class DriverVariableMatrixUpdateEvent(Event):
    matrix: 'RBFDriverVariableMatrix'


def driver_variable_matrix_name(matrix: 'RBFDriverVariableMatrix') -> str:
    driver: 'RBFDriver' = owner_resolve(matrix, ".")
    return f'rbfn_dvmat_{driver.identifier}'


class RBFDriverVariableMatrix(Matrix, PropertyGroup):

    @property
    def data_path(self) -> str:
        return f'["{self.name}"]'

    name: StringProperty(
        name="Name",
        get=driver_variable_matrix_name,
        options=set()
    )

    def update(self, propagate: Optional[bool]=True) -> None:
        driver: 'RBFDriver' = owner_resolve(self, ".")
        dismat = driver.distance_matrix.to_array()

        if not dismat.size:
            varmat = np.array([], dtype=float)
        else:
            coef = 1.0 if driver.smoothing == 'LINEAR' else driver.radius

            for pose, d in zip(driver.poses, dismat):
                data = pose.falloff.curve
                node = nodetree_node_ensure(data.node_identifier, data)
                mapp = node.mapping
                cmap = mapp.curves[0]
                prad = pose.falloff.radius * coef
                d[:] = tuple(mapp.evaluate(cmap, pos) * prad for pos in d)

            idmat = np.identity(dismat.shape[0], dtype=float)

            if driver.smoothing == 'LINEAR':
                idmat *= driver.regularization

            try:
                varmat = np.linalg.solve(dismat, idmat)
            except np.linalg.LinAlgError:
                varmat = np.linalg.lstsq(dismat, idmat, rcond=None)[0]

        self.__init__(varmat)
        self.id_data.data[self.name] = list(varmat.flat)

        if propagate:
            dispatch_event(DriverVariableMatrixUpdateEvent(self))

