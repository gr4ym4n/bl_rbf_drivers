
from typing import Iterator, List, Optional, Sequence, Union, TYPE_CHECKING
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, FloatProperty, PointerProperty
import numpy as np
from .input_variable_data_sample import RBFDriverInputVariableDataSample
if TYPE_CHECKING:
    from .input_variable import RBFDriverInputVariable

class RBFDriverInputVariableData(PropertyGroup):

    data__internal__: PointerProperty(
        type=RBFDriverInputVariableDataSample,
        options={'HIDDEN'}
        )

    norm: FloatProperty(
        name="Norm",
        get=lambda self: self.get("norm", 0.0) if self.is_normalized else np.linalg.norm(self.values()),
        options=set()
        )

    is_normalized: BoolProperty(
        name="Normalized",
        get=lambda self: self.get("is_normalized", False),
        options=set()
        )

    @property
    def variable(self) -> 'RBFDriverInputVariable':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".")[0])

    def __getitem__(self, key: Union[int, slice]) -> Union[RBFDriverInputVariableDataSample, List[RBFDriverInputVariableDataSample]]:
        return self.data__internal__[key]

    def __iter__(self) -> Iterator[RBFDriverInputVariableDataSample]:
        return iter(self.data__internal__)

    def __len__(self) -> int:
        return len(self.data__internal__)

    def __init__(self, data: Sequence[float], normalize: Optional[bool]=False) -> None:
        samples = self.data__internal__
        samples.clear()

        for index, value in enumerate(data):
            samples.add().__init__(index, value)

        if normalize:
            self["is_normalized"] = True
            norm = self["norm"] = np.linalg.norm(data)
            if norm != 0.0:
                for sample in self.data__internal__:
                    sample["value_normalized"] = sample.value / norm
        else:
            self["is_normalized"] = False
            self.property_unset("norm")

    def value(self, index: int, normalized: Optional[bool]=False) -> float:
        return self[index].value_normalized if normalized else self[index].value

    def values(self, normalized: Optional[bool]=False) -> Iterator[float]:
        if normalized:
            for item in self:
                yield item.value_normalized
        else:
            for item in self:
                yield item.value

    def update(self) -> None:
        if self.is_normalized:
            norm = np.linalg.norm(list(self.values(normalized=False)))
            self["norm"] = norm
            if norm == 0.0:
                for sample in self.data__internal__:
                    sample.property_unset("value_normalized")
            else:
                for sample in self.data__internal__:
                    sample["value_normalized"] = sample.value / norm

        pdist = self.variable.input.pose_distance
        pdist.matrix.update()
        pdist.drivers.update()