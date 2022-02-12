
from typing import Iterable, Iterator, List, Optional, Union
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty, FloatProperty

class RBFDriverPoseDataScalar(PropertyGroup):

    value: FloatProperty(
        name="Value",
        get=lambda self: self.get("value", 0.0),
        options=set()
        )

class RBFDriverPoseDataVector(PropertyGroup):

    data__internal__: CollectionProperty(
        type=RBFDriverPoseDataScalar,
        options={'HIDDEN'}
        )

    def __len__(self) -> int:
        return len(self.data__internal__)

    def __getitem__(self, key: Union[int, slice]) -> Union[RBFDriverPoseDataScalar, List[RBFDriverPoseDataScalar]]:
        return self.data__internal__[key]

    def __iter__(self) -> Iterator[RBFDriverPoseDataScalar]:
        return iter(self.data__internal__)

    def __init__(self, data: Optional[Iterable[float]]=None) -> None:
        scalars = self.data__internal__
        scalars.clear()
        if data is not None:
            for value in data:
                scalars.add()["value"] = value

    def values(self) -> Iterator[float]:
        for scalar in self:
            yield scalar.value
