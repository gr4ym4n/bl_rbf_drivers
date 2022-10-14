
from bpy.types import PropertyGroup
from bpy.props import PointerProperty
from .core import RBFDNodeReference, RBFDNodeReferences
from .inputs import (
    RBFDInputTool,
    RBFDInputTools,
    RBFDInputBuild,
    RBFDInputToolsList,
    RBFDInputToolsPanel
    )


class RBFDTools(PropertyGroup):

    inputs: PointerProperty(
        name="Inputs",
        type=RBFDInputTools,
        options=set()
        )


def classes():
    return [
        RBFDNodeReference,
        RBFDNodeReferences,
        RBFDInputTool,
        RBFDInputTools,
        RBFDInputBuild,
        RBFDInputToolsList,
        RBFDInputToolsPanel,
        RBFDTools,
        ]

def register() -> None:
    from bpy.utils import register_class
    for cls in classes():
        register_class(cls)


def unregister() -> None:
    from bpy.utils import unregister_class
    for cls in reversed(classes()):
        unregister_class(cls)
