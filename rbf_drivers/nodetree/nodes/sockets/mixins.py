
from typing import Optional, Sequence
from bpy.props import BoolProperty, StringProperty

class Expandable:

    show_expanded: BoolProperty(
        name="Expand",
        default=False,
        options=set()
        )

class Labeled:

    label: StringProperty(
        name="Label",
        default="",
        options=set()
        )

    def label_resolve(self, text: Optional[str]="") -> str:
        return self.label or text


class FloatArray:

    @property
    def value(self) -> Sequence[float]:
        raise NotImplementedError(f'{self.__class__.__name__}.value')

    @property
    def size(self) -> int:
        return len(self.value)
