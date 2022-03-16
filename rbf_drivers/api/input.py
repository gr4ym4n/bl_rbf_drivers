
from functools import partial
from typing import TYPE_CHECKING
import numpy as np
from bpy.types import Context, PropertyGroup
from bpy.props import EnumProperty, PointerProperty
from rbf_drivers.api.mixins import Symmetrical
from rbf_drivers.app.utils import owner_resolve
from ..app.events import event_handler
from .input_target import InputTargetBoneTargetUpdated, InputTargetObjectUpdated, InputTargetRotationModeUpdated, InputTargetTransformSpaceUpdated
from .input_variables import RBFDriverInputVariables
from .input_distance import RBFDriverInputDistance
from ..lib.transform_utils import ROTATION_MODE_ITEMS, TRANSFORM_SPACE_INDEX
from ..lib.rotation_utils import (noop,
                                  euler_to_quaternion,
                                  euler_to_swing_twist_x,
                                  euler_to_swing_twist_y,
                                  euler_to_swing_twist_z,
                                  quaternion_to_euler,
                                  quaternion_to_swing_twist_x,
                                  quaternion_to_swing_twist_y,
                                  quaternion_to_swing_twist_z,
                                  swing_twist_x_to_euler,
                                  swing_twist_y_to_euler,
                                  swing_twist_z_to_euler,
                                  swing_twist_x_to_quaternion,
                                  swing_twist_x_to_quaternion,
                                  swing_twist_y_to_quaternion,
                                  swing_twist_z_to_quaternion,
                                  swing_twist_x_to_swing_twist_y,
                                  swing_twist_x_to_swing_twist_z,
                                  swing_twist_y_to_swing_twist_x,
                                  swing_twist_y_to_swing_twist_z,
                                  swing_twist_z_to_swing_twist_x,
                                  swing_twist_z_to_swing_twist_y)

if TYPE_CHECKING:
    from .input_target import RBFDriverInputTarget
    from .input_variable import RBFDriverInputVariable
    from .driver import RBFDriver


def input_name_update_handler(input: 'RBFDriverInput', _: Context) -> None:
    names = [item.name for item in input.rbf_driver.inputs if item != input]
    index = 0
    value = input.name
    while value in names:
        index += 1
        value = f'{input.name}.{str(index).zfill(3)}'
    input["name"] = value


class RBFDriverInput(Symmetrical, PropertyGroup):

    ROTATION_MODES = ROTATION_MODE_ITEMS[0:-3] + [
        ('SWING_X', "X Swing", "Swing rotation to aim the X axis", 'NONE', 8 ),
        ('SWING_Y', "Y Swing", "Swing rotation to aim the Y axis", 'NONE', 9 ),
        ('SWING_Z', "Z Swing", "Swing rotation to aim the Z axis", 'NONE', 10),
        ('TWIST_X', "X Twist", "Twist around the X axis"         , 'NONE', 11),
        ('TWIST_Y', "Y Twist", "Twist around the Y axis"         , 'NONE', 12),
        ('TWIST_Z', "Z Twist", "Twist around the Z axis"         , 'NONE', 13),
        ]

    ROTATION_CONVERSION_LUT = {
        'AUTO': {
            'AUTO'      : noop,
            'XYZ'       : noop,
            'XZY'       : noop,
            'YXZ'       : noop,
            'YZX'       : noop,
            'ZXY'       : noop,
            'ZYX'       : noop,
            'SWING_X'   : euler_to_quaternion,
            'SWING_Y'   : euler_to_quaternion,
            'SWING_Z'   : euler_to_quaternion,
            'TWIST_X'   : partial(euler_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(euler_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(euler_to_swing_twist_z, quaternion=True),
            'QUATERNION': euler_to_quaternion,
            },
        'XYZ': {
            'AUTO'      : noop,
            'XYZ'       : noop,
            'XZY'       : noop,
            'YXZ'       : noop,
            'YZX'       : noop,
            'ZXY'       : noop,
            'ZYX'       : noop,
            'SWING_X'   : euler_to_quaternion,
            'SWING_Y'   : euler_to_quaternion,
            'SWING_Z'   : euler_to_quaternion,
            'TWIST_X'   : partial(euler_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(euler_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(euler_to_swing_twist_z, quaternion=True),
            'QUATERNION': euler_to_quaternion,
            },
        'XZY': {
            'AUTO'      : noop,
            'XYZ'       : noop,
            'XZY'       : noop,
            'YXZ'       : noop,
            'YZX'       : noop,
            'ZXY'       : noop,
            'ZYX'       : noop,
            'SWING_X'   : euler_to_quaternion,
            'SWING_Y'   : euler_to_quaternion,
            'SWING_Z'   : euler_to_quaternion,
            'TWIST_X'   : partial(euler_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(euler_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(euler_to_swing_twist_z, quaternion=True),
            'QUATERNION': euler_to_quaternion,
            },
        'YXZ': {
            'AUTO'      : noop,
            'XYZ'       : noop,
            'XZY'       : noop,
            'YXZ'       : noop,
            'YZX'       : noop,
            'ZXY'       : noop,
            'ZYX'       : noop,
            'SWING_X'   : euler_to_quaternion,
            'SWING_Y'   : euler_to_quaternion,
            'SWING_Z'   : euler_to_quaternion,
            'TWIST_X'   : partial(euler_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(euler_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(euler_to_swing_twist_z, quaternion=True),
            'QUATERNION': euler_to_quaternion,
            },
        'YZX': {
            'AUTO'      : noop,
            'XYZ'       : noop,
            'XZY'       : noop,
            'YXZ'       : noop,
            'YZX'       : noop,
            'ZXY'       : noop,
            'ZYX'       : noop,
            'SWING_X'   : euler_to_quaternion,
            'SWING_Y'   : euler_to_quaternion,
            'SWING_Z'   : euler_to_quaternion,
            'TWIST_X'   : partial(euler_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(euler_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(euler_to_swing_twist_z, quaternion=True),
            'QUATERNION': euler_to_quaternion,
            },
        'ZXY': {
            'AUTO'      : noop,
            'XYZ'       : noop,
            'XZY'       : noop,
            'YXZ'       : noop,
            'YZX'       : noop,
            'ZXY'       : noop,
            'ZYX'       : noop,
            'SWING_X'   : euler_to_quaternion,
            'SWING_Y'   : euler_to_quaternion,
            'SWING_Z'   : euler_to_quaternion,
            'TWIST_X'   : partial(euler_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(euler_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(euler_to_swing_twist_z, quaternion=True),
            'QUATERNION': euler_to_quaternion,
            },
        'ZYX': {
            'AUTO'      : noop,
            'XYZ'       : noop,
            'XZY'       : noop,
            'YXZ'       : noop,
            'YZX'       : noop,
            'ZXY'       : noop,
            'ZYX'       : noop,
            'SWING_X'   : euler_to_quaternion,
            'SWING_Y'   : euler_to_quaternion,
            'SWING_Z'   : euler_to_quaternion,
            'TWIST_X'   : partial(euler_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(euler_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(euler_to_swing_twist_z, quaternion=True),
            'QUATERNION': euler_to_quaternion,
            },
        'SWING_X': {
            'AUTO'      : quaternion_to_euler,
            'XYZ'       : quaternion_to_euler,
            'XZY'       : quaternion_to_euler,
            'YXZ'       : quaternion_to_euler,
            'YZX'       : quaternion_to_euler,
            'ZXY'       : quaternion_to_euler,
            'ZYX'       : quaternion_to_euler,
            'SWING_X'   : noop,
            'SWING_Y'   : noop,
            'SWING_Z'   : noop,
            'TWIST_X'   : partial(quaternion_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(quaternion_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(quaternion_to_swing_twist_z, quaternion=True),
            'QUATERNION': noop,
            },
        'SWING_Y': {
            'AUTO'      : quaternion_to_euler,
            'XYZ'       : quaternion_to_euler,
            'XZY'       : quaternion_to_euler,
            'YXZ'       : quaternion_to_euler,
            'YZX'       : quaternion_to_euler,
            'ZXY'       : quaternion_to_euler,
            'ZYX'       : quaternion_to_euler,
            'SWING_X'   : noop,
            'SWING_Y'   : noop,
            'SWING_Z'   : noop,
            'TWIST_X'   : partial(quaternion_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(quaternion_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(quaternion_to_swing_twist_z, quaternion=True),
            'QUATERNION': noop,
            },
        'SWING_Z': {
            'AUTO'      : quaternion_to_euler,
            'XYZ'       : quaternion_to_euler,
            'XZY'       : quaternion_to_euler,
            'YXZ'       : quaternion_to_euler,
            'YZX'       : quaternion_to_euler,
            'ZXY'       : quaternion_to_euler,
            'ZYX'       : quaternion_to_euler,
            'SWING_X'   : noop,
            'SWING_Y'   : noop,
            'SWING_Z'   : noop,
            'TWIST_X'   : partial(quaternion_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(quaternion_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(quaternion_to_swing_twist_z, quaternion=True),
            'QUATERNION': noop,
            },
        'TWIST_X': {
            'AUTO'      : swing_twist_x_to_euler,
            'XYZ'       : swing_twist_x_to_euler,
            'XZY'       : swing_twist_x_to_euler,
            'YXZ'       : swing_twist_x_to_euler,
            'YZX'       : swing_twist_x_to_euler,
            'ZXY'       : swing_twist_x_to_euler,
            'ZYX'       : swing_twist_x_to_euler,
            'SWING_X'   : swing_twist_x_to_quaternion,
            'SWING_Y'   : swing_twist_x_to_quaternion,
            'SWING_Z'   : swing_twist_x_to_quaternion,
            'TWIST_X'   : noop,
            'TWIST_Y'   : swing_twist_x_to_swing_twist_y,
            'TWIST_Z'   : swing_twist_x_to_swing_twist_z,
            'QUATERNION': swing_twist_x_to_quaternion,
            },
        'TWIST_Y': {
            'AUTO'      : swing_twist_y_to_euler,
            'XYZ'       : swing_twist_y_to_euler,
            'XZY'       : swing_twist_y_to_euler,
            'YXZ'       : swing_twist_y_to_euler,
            'YZX'       : swing_twist_y_to_euler,
            'ZXY'       : swing_twist_y_to_euler,
            'ZYX'       : swing_twist_y_to_euler,
            'SWING_X'   : swing_twist_y_to_quaternion,
            'SWING_Y'   : swing_twist_y_to_quaternion,
            'SWING_Z'   : swing_twist_y_to_quaternion,
            'TWIST_X'   : swing_twist_y_to_swing_twist_x,
            'TWIST_Y'   : noop,
            'TWIST_Z'   : swing_twist_y_to_swing_twist_z,
            'QUATERNION': swing_twist_y_to_quaternion,
            },
        'TWIST_Z': {
            'AUTO'      : swing_twist_z_to_euler,
            'XYZ'       : swing_twist_z_to_euler,
            'XZY'       : swing_twist_z_to_euler,
            'YXZ'       : swing_twist_z_to_euler,
            'YZX'       : swing_twist_z_to_euler,
            'ZXY'       : swing_twist_z_to_euler,
            'ZYX'       : swing_twist_z_to_euler,
            'SWING_X'   : swing_twist_z_to_quaternion,
            'SWING_Y'   : swing_twist_z_to_quaternion,
            'SWING_Z'   : swing_twist_z_to_quaternion,
            'TWIST_X'   : swing_twist_z_to_swing_twist_x,
            'TWIST_Y'   : swing_twist_z_to_swing_twist_y,
            'TWIST_Z'   : noop,
            'QUATERNION': swing_twist_z_to_quaternion,
            },
        'QUATERNION': {
            'AUTO'      : quaternion_to_euler,
            'XYZ'       : quaternion_to_euler,
            'XZY'       : quaternion_to_euler,
            'YXZ'       : quaternion_to_euler,
            'YZX'       : quaternion_to_euler,
            'ZXY'       : quaternion_to_euler,
            'ZYX'       : quaternion_to_euler,
            'SWING_X'   : noop,
            'SWING_Y'   : noop,
            'SWING_Z'   : noop,
            'TWIST_X'   : partial(quaternion_to_swing_twist_x, quaternion=True),
            'TWIST_Y'   : partial(quaternion_to_swing_twist_y, quaternion=True),
            'TWIST_Z'   : partial(quaternion_to_swing_twist_z, quaternion=True),
            'QUATERNION': noop,
            }
        }

    def rotation_mode_get(self) -> int:
        return self.get("rotation_mode", 0)

    def rotation_mode_set(self, value: int) -> None:
        cache = self._rotation_mode_get()
        if cache != value:
            self["rotation_mode"] = value
            if self.type == 'ROTATION':
                cache = self.ROTATION_MODES[cache][0]
                value = self.ROTATION_MODES[value][0]

                variables = self.variables

                if len(value) < 4:
                    variables[0]["enabled"] = False
                elif value.startswith('TWIST'):
                    axis = value[-1]
                    variables[0]["enabled"] = False
                    variables[1]["enabled"] = axis == 'X'
                    variables[2]["enabled"] = axis == 'Y'
                    variables[3]["enabled"] = axis == 'Z'
                else:
                    for variable in variables:
                        variable["enabled"] = True

                convert = self.ROTATION_CONVERSION_LUT[cache][value]

                matrix = np.array([
                    tuple(scalar.value for scalar in variable.data) for variable in self.variables
                    ], dtype=np.float)

                for vector, column in zip(matrix.T if len(cache) > 4 else matrix[1:].T,
                                          matrix.T if len(value) > 4 else matrix[1:].T):
                    column[:] = convert(vector)

                if len(value) < 5:
                    matrix[0] = 0.0

                for variable, data in zip(variables, matrix):
                    variable.data.__init__(data, value != 'QUATERNION')

                self.pose_distance.drivers.update()
                self.pose_distance.matrix.update()

    distance: PointerProperty(
        name="Pose Distance",
        type=RBFDriverInputDistance,
        options=set()
        )

    @property
    def rbf_driver(self) -> 'RBFDriver':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".inputs.")[0])

    rotation_mode: EnumProperty(
        name="Mode",
        description="Rotation mode",
        items=ROTATION_MODES,
        get=rotation_mode_get,
        set=rotation_mode_set,
        options=set(),
        )

    variables: PointerProperty(
        name="Variables",
        type=RBFDriverInputVariables,
        options=set()
        )

