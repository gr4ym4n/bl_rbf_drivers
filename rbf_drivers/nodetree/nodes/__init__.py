
from .sample_quaternion import RBFDQuaternionSampleNode
from .target_transform_matrix import RBFDTargetTransformMatrixNode
from .target import RBFDTargetNode
from .transform_matrix_decompose import RBFDTransformMatrixDecomposeNode

def classes():
    return [
        RBFDQuaternionSampleNode,
        RBFDTargetTransformMatrixNode,
        RBFDTargetNode,
        RBFDTransformMatrixDecomposeNode,
        ]


def register() -> None:
    from bpy.utils import register_class
    for cls in classes():
        register_class(cls)


def unregister() -> None:
    from bpy.utils import unregister_class
    for cls in reversed(classes()):
        unregister_class(cls)
