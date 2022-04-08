
from typing import Any, Iterable, Iterator, List, Optional, Sequence, Tuple, Union
from uuid import uuid4
from bpy.types import ID, PropertyGroup
from bpy.props import CollectionProperty, FloatProperty, IntProperty, IntVectorProperty, StringProperty
from idprop.types import IDPropertyArray
import numpy as np

def identifier(pgroup: 'Identifiable') -> str:
    value = PropertyGroup.get(pgroup, "identifier")
    if not value:
        value = uuid4().hex
        PropertyGroup.__setitem__(pgroup, "identifier", value)
    return value


class Struct:

    def __str__(self) -> str:
        return (f'<{self.__class__.__name__} @ '
                f'{self.path_from_id().replace(".collection__internal__", "")}>')


class Identifiable(Struct):

    identifier: StringProperty(
        name="Identifier",
        description="Unique data identifier",
        get=identifier,
        options={'HIDDEN'}
        )

class Symmetrical(Identifiable):

    symmetry_identifier: StringProperty(
        name="Symmetry Identifier",
        get=lambda self: self.get("symmetry_identifier", ""),
        options=set(),
        )

    @property
    def has_symmetry_target(self) -> bool:
        return bool(self.symmetry_identifier)




class FloatContainer(Struct, PropertyGroup):

    index: IntProperty(
        name="Index",
        description="Index of the item within its data structure",
        get=lambda self: self.get("index", 0),
        options=set()
        )

    value: FloatProperty(
        name="Value",
        get=lambda self: self.get("value", 0.0),
        options=set()
        )

    def __init__(self, index: int, value: float) -> None:
        self["index"] = index
        self["value"] = value


class ArrayContainer(Struct, PropertyGroup):

    data__internal__: CollectionProperty(
        type=FloatContainer,
        options={'HIDDEN'}
        )

    def __len__(self) -> int:
        return len(self.data__internal__)

    def __iter__(self) -> Iterator[float]:
        for item in self.data__internal__:
            yield item.value

    def __getitem__(self, key: Union[int, slice]) -> Union[float, List[float]]:
        if isinstance(key, int):
            return self.data__internal__[key].value
        else:
            return [item.value for item in self.data__internal__[key]]

    def __init__(self, values: Sequence[float]) -> None:
        data = self.data__internal__
        data.clear()
        for index, value in enumerate(values):
            data.add().__init__(index, value)

    def item(self, index: int) -> FloatContainer:
        return self.data__internal__[index]

    def items(self) -> Iterator[FloatContainer]:
        return iter(self.data__internal__)

    def to_array(self) -> np.ndarray:
        data = self.data__internal__
        array = np.empty(len(data), dtype=float)
        data.foreach_get("value", array)
        return array


class MatrixVectorAccess:

    def __init__(self, data: 'Matrix', axis: int, index: int) -> None:
        self._data = data
        self._axis = axis
        self._index = index

    def __len__(self) -> int:
        return self._data.shape[int(not self._axis)]

    def __iter__(self) -> Iterator[float]:
        data = self._data.data__internal__
        for index in self.indices:
            yield data[index].value

    def __getitem__(self, key: Union[int, slice]) -> Union[float, List[float]]:
        data = self._data.data__internal__
        idxs = tuple(self.indices)
        if isinstance(key, int):
            return data[idxs[key]].value
        if isinstance(key, slice):
            return [data[index].value for index in idxs[key]]

    def __str__(self) -> str:
        return f'{str(self._data)}.{"columns" if self._axis else "rows"}[{self._index}]'

    @property
    def indices(self) -> Iterable[int]:
        shape = self._data.shape
        index = self._index
        if self._axis == 0:
            alpha = shape[1] * index
            delta = 1
            omega = alpha + shape[1]
        else:
            alpha = index
            delta = shape[1]
            omega = shape[0] * delta
        return range(alpha, omega, delta)

    def item(self, index: int) -> FloatContainer:
        return self._data.data__internal__[tuple(self.indices)[index]]

    def items(self) -> Iterator[FloatContainer]:
        data = self._data.data__internal__
        idxs = self.indices
        for index in idxs:
            yield data[index]

    def to_array(self) -> np.ndarray:
        return np.array(tuple(self), dtype=float)


class MatrixAccess:

    def __init__(self, data: 'Matrix', axis: int) -> None:
        self._data = data
        self._axis = axis

    def __len__(self) -> int:
        return self._data.shape[self._axis]

    def __iter__(self) -> Iterator[MatrixVectorAccess]:
        data = self._data
        axis = self._axis
        for index in range(len(self)):
            yield MatrixVectorAccess(data, axis, index)

    def __getitem__(self, key: Union[int, slice]) -> Union[MatrixVectorAccess, List[MatrixVectorAccess]]:
        if isinstance(key, int):
            if key >= len(self):
                raise IndexError()
            return MatrixVectorAccess(self._data, self._axis, key)
        if isinstance(key, slice):
            data = self._data
            axis = self._axis
            return [MatrixVectorAccess(data, axis, index) for index in range(len(self))]
        raise TypeError()

    def __str__(self) -> str:
        return f'{str(self._data)}.{"columns" if self._axis else "rows"}'

class Matrix(Struct):

    data__internal__: CollectionProperty(
        type=FloatContainer,
        options={'HIDDEN'}
        )

    shape: IntVectorProperty(
        name="Shape",
        size=2,
        get=lambda self: self.get("shape", (0, 0)),
        options=set()
        )

    @property
    def rows(self) -> MatrixAccess:
        return MatrixAccess(self, 0)

    @property
    def columns(self) -> MatrixAccess:
        return MatrixAccess(self, 1)

    @property
    def size(self) -> int:
        shape = self.shape
        return shape[0] * shape[1]

    def __len__(self) -> int:
        return self.shape[0]

    def __iter__(self) -> Iterator[MatrixAccess]:
        return iter(MatrixAccess(self, 0))

    def __getitem__(self, key: Union[int, slice]) -> Union[MatrixVectorAccess, List[MatrixVectorAccess]]:
        return self.rows[key]

    def __init__(self, data: Sequence[Sequence[float]]) -> None:
        scalars = self.data__internal__
        scalars.clear()
        if len(data) == 0:
            self["shape"] = (0, 0)
        else:
            data = np.asarray(data, dtype=float)
            self["shape"] = data.shape
            for index, value in enumerate(data.flat):
                scalars.add().__init__(index, value)

    def item(self, key: Union[int, Tuple[int, int]]) -> FloatContainer:

        if isinstance(key, int):
            return self.data__internal__[key]

        if isinstance(key, tuple):

            if len(key) != 2:
                raise ValueError((f'{self.__class__.__name__}.item(key): '
                                  f'Expected tuple key to be have length 2, not {len(key)}'))

            if not all([isinstance(item, int) for item in key]):
                raise ValueError((f'{self.__class__.__name__}.item(key): '
                                  f'Expected tuple key to be contains int values'))

            return self.data__internal__[key[0] * self.shape[1] + key[1]]
        
        raise TypeError((f'{self.__class__.__name__}.item(key): '
                         f'Expected key to be int or tuple, not {key.__class__.__name__}'))

    def items(self) -> Iterator[FloatContainer]:
        return iter(self.data__internal__)

    def to_array(self) -> np.ndarray:
        shape = self.shape
        array = np.empty(shape[0] * shape[1], dtype=float)
        self.data__internal__.foreach_get("value", array)
        array.shape = tuple(shape)
        return array
