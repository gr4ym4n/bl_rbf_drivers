
from typing import Any, Dict, Optional, Tuple, Union, TYPE_CHECKING
from bpy.types import UILayout
from ..api.input import RBFDriverInput
from ..api.output import RBFDriverOutput
from ..ops.layer import RBFDRIVERS_OT_layer_remove
if TYPE_CHECKING:
    from bpy.types import Context, OperatorProperties, PropertyGroup
    from ..api.mixins import Targetable, Layer
    from ..api.property_target import RBFDriverPropertyTarget


class GUIUtils:

    @staticmethod
    def set_operator_properties(properties: 'OperatorProperties', settings: Dict[str, Any]) -> None:
        for key, value in settings.items():
            setattr(properties, key, value)

    @staticmethod
    def enum_icon(data: 'PropertyGroup', prop: str, item: Optional[str]="") -> int:
        return UILayout.enum_item_icon(data, prop, item or getattr(data, prop))

    @staticmethod
    def enum_name(data: 'PropertyGroup', prop: str, item: Optional[str]="") -> str:
        return UILayout.enum_item_name(data, prop, item or getattr(data, prop))

    def subpanel(self, align: Optional[bool]=False) -> 'UILayout':
        row = self.layout.row()
        row.separator()
        return row.column(align=align)

    @classmethod
    def draw_path(cls, layout: 'UILayout', target: 'Targetable', valid: Optional[bool]=True) -> None:
        row = layout.row()
        sub = row.row(align=True)
        sub.alignment = 'LEFT'
        sub.alert = not valid

        object = target.object

        if object is None:
            sub.label(icon='ERROR', text="Undefined")
            sub.label(icon='RIGHTARROW_THIN')
        else:
            sub.label(text=object.name, icon_value=cls.enum_icon(target, "id_type"))
            sub.label(icon='RIGHTARROW_THIN')
            if object and object.type == 'ARMATURE':
                name = target.bone_target
                if name:
                    icon = "ERROR" if name not in object.data.bones else "BONE_DATA"
                    sub.label(icon=icon, text=name)
                    sub.label(icon='RIGHTARROW_THIN')

        type = target.type
        if type == 'ROTATION':
            mode = target.rotation_mode
            text = f'{"Euler" if len(mode) < 5 else cls.enum_name(target, "rotation_mode")} Rotation'
        elif type == 'NONE':
            # TODO
            text = ""
        else:
            text = cls.enum_name(input, "type")

        sub.label(icon='RNA', text=text)
        row.row()


class GUILayerUtils(GUIUtils):

    @classmethod
    def draw_head(cls, layout: 'UILayout', layer: 'Layer') -> None:
        row = layout.row()
        row.scale_y = 1.25
        row.prop(layer, "ui_open",
                 text="",
                 icon=f'DISCLOSURE_TRI_{"DOWN" if layer.ui_open else "RIGHT"}',
                 emboss=False)

        sub = row.row(align=True)

        if layer.ui_label == 'PATH':
            subrow = sub.row(align=True)
            subrow.scale_y = 0.6
            cls.draw_path(subrow.box(), layer)
        else:
            sub.prop(layer, "name", text="")

        subrow = sub.row(align=True)
        subrow.scale_x = 1.1
        subrow.prop(layer, "ui_label", text="", icon_only=True)

        props = row.operator(RBFDRIVERS_OT_layer_remove.bl_idname, text="", icon='X', emboss=False)
        props.kind = 'INPUT' if isinstance(layer, RBFDriverInput) else 'OUTPUT'
        props.name = layer.name


def layout_split(layout: 'UILayout',
                 label: Optional[str]="",
                 align: Optional[bool]=False,
                 factor: Optional[float]=1/3,
                 decorate: Optional[bool]=True,
                 decorate_fill: Optional[bool]=True) -> Union['UILayout', Tuple['UILayout', ...]]:

    split = layout.row().split(factor=factor)
    col_a = split.column(align=align)
    col_a.alignment = 'RIGHT'

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


def transform_target_draw(layout: 'UILayout', context: 'Context', target: 'Targetable') -> None:
    object = target.object
    column = layout_split(layout, "Target", align=True)
    column.prop_search(target, "object", context.blend_data, "objects", text="", icon='OBJECT_DATA')
    if object is not None and object.type == 'ARMATURE':
        row = column.row(align=True)
        row.alert = bool(target.bone_target) and target.bone_target not in object.data.bones
        column.prop_search(target, "bone_target", object.data, "bones", text="", icon='BONE_DATA')


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
