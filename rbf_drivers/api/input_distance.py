
from functools import partial
from math import acos, asin, fabs, pi, sqrt
from typing import Callable, Sequence, TYPE_CHECKING
from logging import getLogger
from bpy.types import PropertyGroup
from bpy.props import EnumProperty, PointerProperty
from .input_distance_matrix import RBFDriverInputDistanceMatrix
if TYPE_CHECKING:
    from .input import RBFDriverInput

log = getLogger("rbf_drivers")


class RBFDriverInputDistance(PropertyGroup):

    Function = Callable[[Sequence[float], Sequence[float]], float]

    class functions:

        @staticmethod
        def euclidean(a: Sequence[float], b: Sequence[float]) -> float:
            return sqrt(sum(pow(ai - bi, 2.0) for ai, bi in zip(a, b)))

        @staticmethod
        def angle(a: Sequence[float], b: Sequence[float], axis: str) -> float:
            index = 'WXYZ'.index(axis)
            return fabs(a[index], b[index])

        @staticmethod
        def quaternion(a: Sequence[float], b: Sequence[float]) -> float:
            return acos((2.0 * pow(min(max(sum(ai * bi for ai, bi in zip(a, b)), -1.0), 1.0), 2.0)) - 1.0) / pi

        @staticmethod
        def direction(a: Sequence[float], b: Sequence[float], axis: str) -> float:
            aw, ax, ay, az = a
            bw, bx, by, bz = b

            if axis == 'X':
                a = (1.0 - 2.0 * (ay * ay + az * az), 2.0 * (ax * ay + aw * az), 2.0 * (ax * az - aw * ay))
                b = (1.0 - 2.0 * (by * by + bz * bz), 2.0 * (bx * by + bw * bz), 2.0 * (bx * bz - bw * by))
            elif axis == 'Y':
                a = (2.0 * (ax * ay - aw * az), 1.0 - 2.0 * (ax * ax + az * az), 2.0 * (ay * az + aw * ax))
                b = (2.0 * (bx * by - bw * bz), 1.0 - 2.0 * (bx * bx + bz * bz), 2.0 * (by * bz + bw * bx))
            else:
                a = (2.0 * (ax * az + aw * ay), 2.0 * (ay * az - aw * ax), 1.0 - 2.0 * (ax * ax + ay * ay))
                b = (2.0 * (bx * bz + bw * by), 2.0 * (by * bz - bw * bx), 1.0 - 2.0 * (bx * bx + by * by))

            return (asin((sum(ai * bi for ai, bi in zip(a, b)))) - -(pi / 2.0)) / pi

    METRIC_ENUM_ITEMS = [
        ('EUCLIDEAN'),
        ('ANGLE'),
        ('QUATERNION'),
        ('DIRECTION'),
        ]

    @property
    def function(self) -> Function:
        metric = self.metric
        if metric == 'QUATERNION' : return self.functions.quaternion
        if metric == 'DIRECTION'  : return partial(self.functions.direction, axis=self.input.rotation_mode[-1])
        if metric == 'ANGLE'      : return partial(self.functions.angle, axis=self.input.rotation_mode[-1])
        return self.functions.euclidean

    @property
    def input(self) -> 'RBFDriverInput':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])

    matrix: PointerProperty(
        name="Matrix",
        type=RBFDriverInputDistanceMatrix,
        options=set()
        )

    @property
    def metric_enum_item_index(self) -> int:
        input = self.input
        if input.type == 'ROTATION':
            mode = input.rotation_mode
            if mode == 'QUATERNION'     : return 2
            if mode.startswith('SWING') : return 3
            if mode.startswith('TWIST') : return 1
        return 0

    metric: EnumProperty(
        name="Metric",
        items=METRIC_ENUM_ITEMS,
        get=metric_enum_item_index.getter,
        options=set()
        )
