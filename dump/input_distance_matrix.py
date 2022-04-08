
from typing import Optional, TYPE_CHECKING
from bpy.types import PropertyGroup
import numpy as np
from ..rbf_drivers.api.mixins import Matrix
from ..rbf_drivers.api.input_variable import input_variable_is_enabled
from ..rbf_drivers.app.events import dataclass, dispatch_event, Event
from ..rbf_drivers.app.utils import owner_resolve
if TYPE_CHECKING:
    from ..rbf_drivers.api.input import RBFDriverInput


@dataclass(frozen=True)
class InputDistanceMatrixUpdateEvent(Event):
    matrix: 'RBFDriverInputDistanceMatrix'


class RBFDriverInputDistanceMatrix(Matrix, PropertyGroup):

    def update(self, propagate: Optional[bool]=True) -> None:
        input: 'RBFDriverInput' = owner_resolve(self, ".distance")

        if not input.is_valid:
            matrix = np.array([], dtype=float)
        else:
            active = filter(input_variable_is_enabled, input.variables)
            params = np.array([tuple(v.data.values(v.data.is_normalized)) for v in active], dtype=float).T
            matrix = np.empty((len(params), len(params)), dtype=float)

            distance = input.distance.function
            for a, row in zip(params, matrix):
                for i, b in enumerate(params):
                    row[i] = distance(a, b)

        self.__init__(matrix)
        if propagate:
            dispatch_event(InputDistanceMatrixUpdateEvent(self))
