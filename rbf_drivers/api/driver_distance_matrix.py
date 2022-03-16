
from typing import TYPE_CHECKING, List, Optional
import numpy as np
from bpy.types import PropertyGroup
from .mixins import Matrix

if TYPE_CHECKING:
    from .pose_falloff import RBFDriverPoseFalloff
    from .pose_weight import RBFDriverPoseWeight
    from .pose import RBFDriverPose
    from .driver_variable_matrix import RBFDriverVariableMatrix
    from .driver import RBFDriver


def rbf_gaussian(data: np.ndarray, radius: float) -> np.ndarray:
    return np.exp(np.negative(np.power(data, 2.0) / 2.0 * radius * radius))


def rbf_quadratic(data: np.ndarray, radius: float) -> np.ndarray:
    return np.sqrt(np.power(data, 2.0) + pow(radius, 2.0))


class RBFDriverDistanceMatrix(Matrix, PropertyGroup):

    @property
    def rbf_driver(self) -> RBFDriver:
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])

    def update(self, propagate: Optional[bool]=True) -> None:
        rbf_driver = self.rbf_driver
        poses = rbf_driver.poses
        stack = [input.distance.matrix.to_array() for input in rbf_driver.inputs]
        count = len(stack)

        if count == 0:
            self.__init__([])
            return

        matrix = stack[0] if count == 1 else np.add.reduce(stack) / float(count)
        self.__init__(matrix)

        # Update pose radii
        matrix = matrix.view(np.ma.MaskedArray)
        matrix.mask = np.identity(len(matrix), dtype=bool)

        pose: 'RBFDriverPose'
        for pose, row in zip(poses, matrix):
            falloff: 'RBFDriverPoseFalloff' = pose.falloff
            if falloff.radius_is_auto_adjusted:
                row = row.compressed()
                falloff["radius"] = 1.0 if len(row) == 0 else np.min(row)





        # Apply RBF
        kernel = rbf_driver.smoothing
        if kernel != 'LINEAR':
            factor = rbf_driver.falloff.radius_factor
            rbf = rbf_gaussian if kernel == 'GAUSSIAN' else rbf_quadratic

            for pose, row in zip(poses, matrix):
                falloff: 'RBFDriverPoseFalloff' = pose.falloff
                radius = falloff.radius * factor * falloff.radius_factor
                row[:] = rbf(row, radius)

        self.__init__(matrix)

        

        if rbf_driver.use_linear_equation_solver:
            matrix: 'RBFDriverVariableMatrix' = rbf_driver.variable_matrix
            matrix.update()
        else:
            for pose in poses_updated:
                weight: 'RBFDriverPoseWeight' = pose.weight
                weight.update()


