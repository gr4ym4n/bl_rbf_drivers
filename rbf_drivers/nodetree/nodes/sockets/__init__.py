

from .float import RBFDFloatSocket
from .quaternion import RBFDQuaternionSocket
from .target import RBFDTargetSocket
from .transform_matrix import RBFDTransformMatrixSocket
from .vector3 import RBFDVector3Socket

def classes():
    return [
        RBFDFloatSocket,
        RBFDQuaternionSocket,
        RBFDTargetSocket,
        RBFDTransformMatrixSocket,
        RBFDVector3Socket,
        ]


def register() -> None:
    from bpy.utils import register_class
    for cls in classes():
        register_class(cls)


def unregister() -> None:
    from bpy.utils import unregister_class
    for cls in reversed(classes()):
        unregister_class(cls)
