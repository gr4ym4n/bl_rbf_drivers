
from typing import TYPE_CHECKING, Optional
from bpy.types import PropertyGroup
from bpy.props import FloatProperty
import numpy as np
from .mixins import Matrix
if TYPE_CHECKING:
    from .input import RBFDriverInput


class RBFDriverInputDistanceMatrix(Matrix, PropertyGroup):

    @property
    def input(self) -> 'RBFDriverInput':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".pose_distance.")[0])

    norm: FloatProperty(
        name="Norm",
        get=lambda self: self.get("norm", 0.0),
        options=set()
        )

    def update(self, propagate: Optional[bool]=True) -> None:
        input = self.input
        params = np.array([tuple(v.data.values(v.data.is_normalized)) for v in input.variables], dtype=float).T
        matrix = np.empty((len(params), len(params)), dtype=float)

        distance = input.distance.function
        for a, row in zip(params, matrix):
            for i, b in enumerate(params):
                row[i] = distance(a, b)

        norm = np.linalg.norm(matrix)
        self["norm"] = norm
        if norm != 0.0:
            matrix /= norm

        self.__init__(matrix)
        if propagate:
            input.rbf_driver.distance.matrix.update()