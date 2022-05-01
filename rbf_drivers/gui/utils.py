
from typing import Any, Dict, Optional, Protocol, Tuple, Union, TYPE_CHECKING
from bpy.types import UILayout
if TYPE_CHECKING:
    from bpy.types import Context, Object, PropertyGroup
    from ..api.property_target import RBFDriverPropertyTarget


class TransformTargetProperties(Protocol):
    @property
    def bone_target(self) -> str: pass
    @property
    def object(self) -> Optional['Object']: pass


class GUIUtils:

    @staticmethod
    def split_layout(layout: 'UILayout',
                     label: Optional[str]="",
                     align: Optional[bool]=False,
                     alignment: Optional[str]='RIGHT',
                     factor: Optional[float]=0.2,
                     decorate: Optional[bool]=True,
                     decorate_fill: Optional[bool]=True) -> Union['UILayout', Tuple['UILayout', ...]]:

        split = layout.row().split(factor=factor)
        col_a = split.column(align=align)
        col_a.alignment = alignment

        if label:
            col_a.label(text=label)
    
        row = split.row()
        col_b = row.column(align=align)
    
        if decorate:
            col_c = row.column(align=align)
            if decorate_fill:
                col_c.label(icon='BLANK1')
            else:
                return (col_b, col_c) if label else (col_a, col_b, col_c)

        return col_b if label else (col_a, col_b)

    @staticmethod
    def enum_icon(data: 'PropertyGroup', prop: str, item: Optional[str]="") -> int:
        return UILayout.enum_item_icon(data, prop, item or getattr(data, prop))

    @staticmethod
    def enum_name(data: 'PropertyGroup', prop: str, item: Optional[str]="") -> str:
        return UILayout.enum_item_name(data, prop, item or getattr(data, prop))

    @staticmethod
    def subpanel(layout: 'UILayout', align: Optional[bool]=False) -> 'UILayout':
        row = layout.row()
        row.label(icon='BLANK1')
        return row.column(align=align)


class GUILayerUtils(GUIUtils):

    @classmethod
    def draw_transform_target(cls,
                              layout: 'UILayout',
                              context: 'Context',
                              props: TransformTargetProperties,
                              label: Optional[str]="Target",
                              **options: Dict[str, Any]) -> None:

        object = props.object
        column = cls.split_layout(layout, label, align=True, **options)
        column.prop_search(props, "object", context.blend_data, "objects", text="", icon='OBJECT_DATA')

        if object is not None and object.type == 'ARMATURE':
            row = column.row(align=True)
            row.alert = bool(props.bone_target) and props.bone_target not in object.data.bones
            row.prop_search(props, "bone_target", object.data, "bones", text="", icon='BONE_DATA')

def layout_split(layout: 'UILayout',
                 label: Optional[str]="",
                 align: Optional[bool]=False,
                 alignment: Optional[str]='RIGHT',
                 factor: Optional[float]=1/3,
                 decorate: Optional[bool]=True,
                 decorate_fill: Optional[bool]=True) -> Union['UILayout', Tuple['UILayout', ...]]:

    split = layout.row().split(factor=factor)
    col_a = split.column(align=align)
    col_a.alignment = alignment

    if label:
        col_a.label(text=label)
 
    row = split.row()
    col_b = row.column(align=align)
 
    if decorate:
        col_c = row.column(align=align)
        if decorate_fill:
            col_c.label(icon='BLANK1')
        else:
            return (col_b, col_c) if label else (col_a, col_b, col_c)

    return col_b if label else (col_a, col_b)


def pose_weight_render(layout: 'UILayout',
                       weight: 'RBFDriverPropertyTarget',
                       **options: Dict[str, Any]) -> None:

    if isinstance(weight.value, float):
        options["index"] = weight.array_index
        layout.prop(weight.id, weight.data_path, **options)
    else:
        # TODO add operator to reload pose weight driver
        layout.label(icon='ERROR', text="Weight")

def idprop_data_render(layout: 'UILayout',
                       target: 'RBFDriverPropertyTarget',
                       **options: Dict[str, Any]) -> None:
    if isinstance(target.value, float):
        layout.prop(target.id, target.data_path, **options)
    else:
        # TODO add operator to reload property
        layout.label(icon='ERROR', text="Missing Property")
