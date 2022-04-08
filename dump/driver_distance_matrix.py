
from typing import TYPE_CHECKING, Optional
import numpy as np
from bpy.types import PropertyGroup
from ..rbf_drivers.api.mixins import Matrix
from ..rbf_drivers.app.events import dataclass, dispatch_event, Event
from ..rbf_drivers.app.utils import owner_resolve
if TYPE_CHECKING:
    from ..rbf_drivers.api.driver import RBFDriver


@dataclass(frozen=True)
class DriverDistanceMatrixUpdateEvent(Event):
    matrix: 'RBFDriverDistanceMatrix'


def driver_distance_matrix_norm(matrix: 'RBFDriverDistanceMatrix') -> float:
    return matrix.get("norm", 0.0)


class RBFDriverDistanceMatrix(Matrix, PropertyGroup):

    def update(self, propagate: Optional[bool]=True) -> None:
        driver: 'RBFDriver' = owner_resolve(self, ".")

        stack = [input.distance.matrix.to_array() for input in driver.inputs if input.is_valid]
        count = len(stack)

        if count == 0:
            data = []
        else:
            data = stack[0] if count == 1 else np.add.reduce(stack) / float(count)

        self.__init__(data)
        if propagate:
            dispatch_event(DriverDistanceMatrixUpdateEvent(self))

