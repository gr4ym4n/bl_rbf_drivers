
from dataclasses import dataclass, field, fields
from enum import IntFlag, auto
from math import ceil, floor, trunc
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple, Union, TYPE_CHECKING
if TYPE_CHECKING:
    from bpy.types import ID


class IDType(IntFlag):
    OBJECT = auto()
    MESH = auto()
    CURVE = auto()
    SURFACE = auto()
    META = auto()
    FONT = auto()
    HAIR = auto()
    POINTCLOUD = auto()
    VOLUME = auto()
    GPENCIL = auto()
    ARMATURE = auto()
    LATTICE = auto()
    EMPTY = auto()
    LIGHT = auto()
    LIGHT_PROBE = auto()
    CAMERA = auto()
    SPEAKER = auto()


class RotationMode(IntFlag):
    AUTO = auto()
    XYZ = auto()
    XZY = auto()
    YXZ = auto()
    YZX = auto()
    ZXY = auto()
    ZYX = auto()
    QUATERNION = auto()
    SWING_TWIST_X = auto()
    SWING_TWIST_Y = auto()
    SWING_TWIST_Z = auto()


class TransformSpace(IntFlag):
    WORLD_SPACE = auto()
    TRANSFORM_SPACE = auto()
    LOCAL_SPACE = auto()


class TransformType(IntFlag):
    LOC_X = auto()
    LOC_Y = auto()
    LOC_Z = auto()
    ROT_W = auto()
    ROT_X = auto()
    ROT_Y = auto()
    ROT_Z = auto()
    SCALE_X = auto()
    SCALE_Y = auto()
    SCALE_Z = auto()


class InputType(IntFlag):
    SINGLE_PROP = auto()
    TRANSFORMS = auto()
    LOC_DIFF = auto()
    ROTATION_DIFF = auto()


class ScalarDataType(IntFlag):
    FLOAT = auto()
    ANGLE = auto()
    PIXEL = auto()


class VectorDataType(IntFlag):
    ARRAY = auto()
    LOCATION = auto()
    EULER = auto()
    QUATERNION = auto()
    QUATERNION_AIM_X = auto()
    QUATERNION_AIM_Y = auto()
    QUATERNION_AIM_Z = auto()
    SCALE = auto()
    COLOR = auto()


@dataclass(frozen=True)
class Target:
    id_type: IDType = IDType.OBJECT
    id: Optional['ID'] = None
    bone_target: str = ""
    data_path: str = ""
    rotation_mode: RotationMode = RotationMode.AUTO
    transform_space: TransformSpace = TransformSpace.WORLD_SPACE
    transform_type: TransformType = TransformType.LOC_X

    def clone(self, **overrides: Dict[str, Any]) -> 'Target':
        return Target(**dict((f.name, overrides.get(f.name, getattr(self, f.name))) for f in fields(self)))


@dataclass(frozen=True)
class Input:
    type: InputType = InputType.SINGLE_PROP
    name: str = ""
    targets: Sequence[Target] = field(default_factory=lambda: (Target(),))

    def value(self) -> float:
        # TODO
        return 0.0


@dataclass(frozen=True)
class InputMapping:
    inputs: Sequence[Input] = field(default_factory=tuple)
    type: VectorDataType = VectorDataType.ARRAY


@dataclass(frozen=True)
class Scalar:
    value: float = 0.0
    input: Optional[Input] = None
    dtype: ScalarDataType = ScalarDataType.FLOAT

    def __bool__(self) -> bool:
        return bool(self.value)

    def __int__(self) -> int:
        return int(self.value)

    def __float__(self) -> float:
        return self.value

    def __pos__(self) -> 'Scalar':
        return Scalar(+self.value, dtype=self.dtype)

    def __neg__(self) -> 'Scalar':
        return Scalar(-self.value, dtype=self.dtype)

    def __abs__(self) -> 'Scalar':
        return Scalar(abs(self.value), dtype=self.dtype)

    def __round__(self, ndigits: int) -> 'Scalar':
        return Scalar(round(self.value, ndigits), dtype=self.dtype)

    def __floor__(self) -> 'Scalar':
        return Scalar(floor(self.value), dtype=self.dtype)

    def __ceil__(self) -> 'Scalar':
         return Scalar(ceil(self.value), dtype=self.dtype)

    def __trunc__(self) -> 'Scalar':
        return Scalar(trunc(self.value), dtype=self.dtype)

    def __add__(self, value: Union[float, 'Scalar']) -> 'Scalar':
        return Scalar(self.value + float(value), dtype=self.dtype)

    def __sub__(self, value: Union[float, 'Scalar']) -> 'Scalar':
        return Scalar(self.value - float(value), dtype=self.dtype)

    def __mul__(self, value: Union[float, 'Scalar']) -> 'Scalar':
        return Scalar(self.value * float(value), dtype=self.dtype)

    def __floordiv__(self, value: Union[float, 'Scalar']) -> 'Scalar':
        return Scalar(self.value / float(value), dtype=self.dtype)

    def __truediv__(self, value: Union[float, 'Scalar']) -> 'Scalar':
        return Scalar(self.value // value, dtype=self.dtype)

    def __mod__(self, value: Union[float, 'Scalar']) -> 'Scalar':
        return Scalar(self.value % float(value), dtype=self.dtype)

    def __divmod__(self, value: Union[float, 'Scalar']) -> 'Scalar':
        return Scalar(divmod(self.value, float(value)), dtype=self.dtype)


@dataclass(frozen=True)
class Vector:
    array: Sequence[Scalar] = field(default_factory=tuple)
    dtype: VectorDataType = VectorDataType.ARRAY

    def __len__(self) -> int:
        return len(self.array)

    def __iter__(self) -> Iterator[Scalar]:
        return iter(self.array)

    def __getitem__(self, key: Union[int, slice]) -> Union[Scalar, List[Scalar]]:
        return self.array[key]


@dataclass(frozen=True)
class Matrix:
    array: Sequence[Vector] = field(default_factory=tuple)
    dtype: VectorDataType = VectorDataType.ARRAY
    shape: Tuple[int, Optional[int]] = (0,)

    def __init__(self) -> None:
        pass
