
from math import acos, asin, fabs, pi, sqrt
from typing import TYPE_CHECKING, Sequence
if TYPE_CHECKING:
    from bpy.types import PropertyGroup


def resolve(data: 'PropertyGroup', separator: str) -> 'PropertyGroup':
    path: str = data.path_from_id()
    return data.id_data.path_resolve(path.rpartition(separator)[0])


def distance_euclidean(a: Sequence[float], b: Sequence[float]) -> float:
    return sqrt(sum(pow(ai - bi, 2.0) for ai, bi in zip(a, b)))


def distance_angle(a: Sequence[float], b: Sequence[float]) -> float:
    return fabs(a[0]-b[0])/pi


def distance_quaternion(a: Sequence[float], b: Sequence[float]) -> float:
    return acos((2.0 * pow(min(max(sum(ai * bi for ai, bi in zip(a, b)), -1.0), 1.0), 2.0)) - 1.0) / pi


def distance_direction(a: Sequence[float], b: Sequence[float], axis: str) -> float:
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