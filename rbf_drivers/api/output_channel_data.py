
from typing import Iterator, List, Sequence, Union
from bpy.types import PropertyGroup
from bpy.props import CollectionProperty
from .output_channel_data_sample import RBFDriverOutputChannelDataSample


class RBFDriverOutputChannelData(PropertyGroup):

    data__internal__: CollectionProperty(
        type=RBFDriverOutputChannelDataSample,
        options=set()
        )

    def __init__(self, values: Sequence[float]) -> None:
        data = self.data__internal__
        data.clear()

        for index, value in enumerate(values):
            data.add().__init__(index, value)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}'

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".collection__internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'

    def __getitem__(self, key: Union[int, slice]) -> Union[RBFDriverOutputChannelDataSample, List[RBFDriverOutputChannelDataSample]]:
        return self.data__internal__[key]

    def __iter__(self) -> Iterator[RBFDriverOutputChannelDataSample]:
        return iter(self.data__internal__)

    def __len__(self) -> int:
        return len(self.data__internal__)

    def value(self, index: int) -> float:
        return self[index].value

    def values(self) -> Iterator[float]:
        for item in self:
            yield item.value
