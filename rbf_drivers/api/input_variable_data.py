
from typing import Iterator, List, Optional, Sequence, Union
from bpy.types import PropertyGroup
from bpy.props import BoolProperty, CollectionProperty, FloatProperty
import numpy as np
from .input_variable_data_sample import RBFDriverInputVariableDataSample
from ..app.events import dataclass, dispatch_event, Event


@dataclass(frozen=True)
class InputVariableDataUpdateEvent(Event):
    data: 'RBFDriverInputVariableData'


class RBFDriverInputVariableData(PropertyGroup):

    data__internal__: CollectionProperty(
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

    def __getitem__(self, key: Union[int, slice]) -> Union[RBFDriverInputVariableDataSample, List[RBFDriverInputVariableDataSample]]:
        return self.data__internal__[key]

    def __iter__(self) -> Iterator[RBFDriverInputVariableDataSample]:
        return iter(self.data__internal__)

    def __len__(self) -> int:
        return len(self.data__internal__)

    def __init__(self, values: Sequence[float], normalize: Optional[bool]=None) -> None:
        self["is_normalized"] = self.is_normalized if normalize is None else normalize

        data = self.data__internal__
        data.clear()

        for index, value in enumerate(values):
            data.add().__init__(index, value)

        self.update(propagate=False)

    def value(self, index: int, normalized: Optional[bool]=False) -> float:
        return self[index].value_normalized if normalized else self[index].value

    def values(self, normalized: Optional[bool]=False) -> Iterator[float]:
        if normalized:
            for item in self:
                yield item.value_normalized
        else:
            for item in self:
                yield item.value

    def update(self, propagate: Optional[bool]=True) -> None:

        if self.is_normalized:
            norm = np.linalg.norm(list(self.values(normalized=False)))

            if norm == 0.0:
                for sample in self.data__internal__:
                    sample.property_unset("value_normalized")
            else:
                for sample in self.data__internal__:
                    sample["value_normalized"] = sample.value / norm

        if propagate:
            dispatch_event(InputVariableDataUpdateEvent(self))
