
from functools import partial
from math import acos, asin, fabs, pi, sqrt
from typing import Callable, Sequence, TYPE_CHECKING
from logging import getLogger
from bpy.types import PropertyGroup
from bpy.props import EnumProperty, PointerProperty
from ..rbf_drivers.api.mixins import ArrayContainer
from .input_distance_matrix import RBFDriverInputDistanceMatrix
from ..rbf_drivers.app.utils import owner_resolve
if TYPE_CHECKING:
    from ..rbf_drivers.api.input import RBFDriverInput

log = getLogger("rbf_drivers")


INPUT_DISTANCE_METRIC_ITEMS = [
    ('EUCLIDEAN' , "Euclidean" , "Euclidean distance" ),
    ('ANGLE'     , "Angle"     , "Angle difference"   ),
    ('QUATERNION', "Quaternion", "Quaternion distance"),
    ('DIRECTION' , "Direction" , "Aim vector distance"),
    ]


def input_distance_metric(distance: 'RBFDriverInputDistance') -> int:
    input: 'RBFDriverInput' = owner_resolve(distance, ".")
    if input.type == 'ROTATION':
        mode = input.rotation_mode
        if mode == 'QUATERNION'     : return 2
        if mode.startswith('SWING') : return 3
        if mode.startswith('TWIST') : return 1
    return 0


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

    @property
    def function(self) -> Function:
        metric = self.metric
        if metric == 'QUATERNION' : return self.functions.quaternion
        if metric == 'DIRECTION'  : return partial(self.functions.direction, axis=self.input.rotation_mode[-1])
        if metric == 'ANGLE'      : return partial(self.functions.angle, axis=self.input.rotation_mode[-1])
        return self.functions.euclidean

    matrix: PointerProperty(
        name="Matrix",
        type=RBFDriverInputDistanceMatrix,
        options=set()
        )

    metric: EnumProperty(
        name="Metric",
        items=INPUT_DISTANCE_METRIC_ITEMS,
        get=input_distance_metric,
        options=set()
        )

    pose_radii: PointerProperty(
        name="Radii",
        type=ArrayContainer,
        options=set()
        )
