
#region Imports
###################################################################################################

from typing import (Any,
                    Callable,
                    Dict,
                    Iterator,
                    List,
                    Optional,
                    Sequence,
                    Tuple,
                    Union,
                    TYPE_CHECKING)

from functools import partial
from math import acos, asin, fabs, pi, sqrt
from bpy.app import version

from bpy.types import (Driver,
                       ID,
                       Object,
                       PropertyGroup)

from bpy.props import (BoolProperty,
                       CollectionProperty,
                       EnumProperty,
                       FloatProperty,
                       IntProperty,
                       PointerProperty,
                       StringProperty)

import numpy as np
from rna_prop_ui import rna_idprop_ui_create
from .posedata import RBFDriverPoseDataVector
from .mixins import ID_TYPE_ITEMS, Identifiable
from .mixins import LAYER_TYPE_ITEMS
from .lib import rotation_utils
from .lib.driver_utils import (DriverVariableNameGenerator,
                               driver_ensure,
                               driver_remove,
                               driver_variables_clear
                               )
from .lib.transform_utils import (ROTATION_MODE_ITEMS,
                                  ROTATION_MODE_INDEX,
                                  TRANSFORM_SPACE_ITEMS,
                                  TRANSFORM_SPACE_INDEX,
                                  TRANSFORM_TYPE_INDEX,
                                  TRANSFORM_TYPE_ITEMS,
                                  transform_matrix,
                                  transform_matrix_element,
                                  transform_target,
                                  transform_target_distance,
                                  transform_target_rotational_difference
                                  )

if TYPE_CHECKING:
    from .driver import RBFDriver

#endregion Imports

#region Configuration
###################################################################################################

INFLUENCE_IDPROP_SETTINGS = {
    "default": 1.0,
    "min": 0.0,
    "max": 1.0,
    "soft_min": 0.0,
    "soft_max": 1.0,
    "description": "RBF driver input influence"
    }

BBONE_VARIABLES = [
    {"label": "Curve In X" , "path": "bbone_curveinx" , "valid": True},
    {"label": "Y"          , "path": "bbone_curveiny" , "valid": version[0] < 2},
    {"label": "Z"          , "path": "bbone_curveinz" , "valid": version[0] > 2},
    {"label": "Curve Out X", "path": "bbone_curveoutx", "valid": True},
    {"label": "Y"          , "path": "bbone_curveouty", "valid": version[0] < 2},
    {"label": "Z"          , "path": "bbone_curveoutz", "valid": version[0] > 2},
    {"label": "Ease In"    , "path": "bbone_easein"   , "valid": True},
    {"label": "Out"        , "path": "bbone_easeout"  , "valid": True},
    {"label": "Roll In"    , "path": "bbone_rollin"   , "valid": True},
    {"label": "Out"        , "path": "bbone_rollout"  , "valid": True},
    {"label": "Scale In X" , "path": "bbone_scaleinx"  if version[0] < 3 else "bbone_scalein[0]" , "valid": True},
    {"label": "Y"          , "path": "bbone_scaleiny"  if version[0] < 3 else "bbone_scalein[1]" , "valid": True},
    {"label": "Z"          , "path": "bbone_scaleinz"  if version[0] < 3 else "bbone_scalein[2]" , "valid": version[0] >= 3},
    {"label": "Scale Out X", "path": "bbone_scaleoutx" if version[0] < 3 else "bbone_scaleout[0]", "valid": True},
    {"label": "Y"          , "path": "bbone_scaleouty" if version[0] < 3 else "bbone_scaleout[1]", "valid": True},
    {"label": "Z"          , "path": "bbone_scaleoutz" if version[0] < 3 else "bbone_scaleout[2]", "valid": version[0] >= 3},
    ]

VARIABLE_TYPE_ITEMS = [
    ('SINGLE_PROP'  , "Single Property"      , "Use the value from some RNA property (Default).", 'NONE', 0),
    ('TRANSFORMS'   , "Transform Channel"    , "Final transformation value of object or bone."  , 'NONE', 1),
    ('ROTATION_DIFF', "Rotational Difference", "Use the angle between two bones."               , 'NONE', 2),
    ('LOC_DIFF'     , "Distance"             , "Distance between two bones or objects."         , 'NONE', 3),
    ]

VARIABLE_TYPE_INDEX = {
    item[0]: item[4] for item in VARIABLE_TYPE_ITEMS
    }

ROTATION_CONVERSION_LUT = {
    'AUTO': {
        'AUTO': rotation_utils.noop,
        'XYZ': rotation_utils.noop,
        'XZY': rotation_utils.noop,
        'YXZ': rotation_utils.noop,
        'YZX': rotation_utils.noop,
        'ZXY': rotation_utils.noop,
        'ZYX': rotation_utils.noop,
        'SWING_X': rotation_utils.euler_to_quaternion,
        'SWING_Y': rotation_utils.euler_to_quaternion,
        'SWING_Z': rotation_utils.euler_to_quaternion,
        'TWIST_X': partial(rotation_utils.euler_to_swing_twist_x, quaternion=True),
        'TWIST_Y': partial(rotation_utils.euler_to_swing_twist_y, quaternion=True),
        'TWIST_Z': partial(rotation_utils.euler_to_swing_twist_z, quaternion=True),
        'QUATERNION': rotation_utils.euler_to_quaternion,
        },
    'XYZ': {
        'AUTO': rotation_utils.noop,
        'XYZ': rotation_utils.noop,
        'XZY': rotation_utils.noop,
        'YXZ': rotation_utils.noop,
        'YZX': rotation_utils.noop,
        'ZXY': rotation_utils.noop,
        'ZYX': rotation_utils.noop,
        'SWING_X': rotation_utils.euler_to_quaternion,
        'SWING_Y': rotation_utils.euler_to_quaternion,
        'SWING_Z': rotation_utils.euler_to_quaternion,
        'TWIST_X': partial(rotation_utils.euler_to_swing_twist_x, quaternion=True),
        'TWIST_Y': partial(rotation_utils.euler_to_swing_twist_y, quaternion=True),
        'TWIST_Z': partial(rotation_utils.euler_to_swing_twist_z, quaternion=True),
        'QUATERNION': rotation_utils.euler_to_quaternion,
        },
    'XZY': {
        'AUTO': rotation_utils.noop,
        'XYZ': rotation_utils.noop,
        'XZY': rotation_utils.noop,
        'YXZ': rotation_utils.noop,
        'YZX': rotation_utils.noop,
        'ZXY': rotation_utils.noop,
        'ZYX': rotation_utils.noop,
        'SWING_X': rotation_utils.euler_to_quaternion,
        'SWING_Y': rotation_utils.euler_to_quaternion,
        'SWING_Z': rotation_utils.euler_to_quaternion,
        'TWIST_X': partial(rotation_utils.euler_to_swing_twist_x, quaternion=True),
        'TWIST_Y': partial(rotation_utils.euler_to_swing_twist_y, quaternion=True),
        'TWIST_Z': partial(rotation_utils.euler_to_swing_twist_z, quaternion=True),
        'QUATERNION': rotation_utils.euler_to_quaternion,
        },
    'YXZ': {
        'AUTO': rotation_utils.noop,
        'XYZ': rotation_utils.noop,
        'XZY': rotation_utils.noop,
        'YXZ': rotation_utils.noop,
        'YZX': rotation_utils.noop,
        'ZXY': rotation_utils.noop,
        'ZYX': rotation_utils.noop,
        'SWING_X': rotation_utils.euler_to_quaternion,
        'SWING_Y': rotation_utils.euler_to_quaternion,
        'SWING_Z': rotation_utils.euler_to_quaternion,
        'TWIST_X': partial(rotation_utils.euler_to_swing_twist_x, quaternion=True),
        'TWIST_Y': partial(rotation_utils.euler_to_swing_twist_y, quaternion=True),
        'TWIST_Z': partial(rotation_utils.euler_to_swing_twist_z, quaternion=True),
        'QUATERNION': rotation_utils.euler_to_quaternion,
        },
    'YZX': {
        'AUTO': rotation_utils.noop,
        'XYZ': rotation_utils.noop,
        'XZY': rotation_utils.noop,
        'YXZ': rotation_utils.noop,
        'YZX': rotation_utils.noop,
        'ZXY': rotation_utils.noop,
        'ZYX': rotation_utils.noop,
        'SWING_X': rotation_utils.euler_to_quaternion,
        'SWING_Y': rotation_utils.euler_to_quaternion,
        'SWING_Z': rotation_utils.euler_to_quaternion,
        'TWIST_X': partial(rotation_utils.euler_to_swing_twist_x, quaternion=True),
        'TWIST_Y': partial(rotation_utils.euler_to_swing_twist_y, quaternion=True),
        'TWIST_Z': partial(rotation_utils.euler_to_swing_twist_z, quaternion=True),
        'QUATERNION': rotation_utils.euler_to_quaternion,
        },
    'ZXY': {
        'AUTO': rotation_utils.noop,
        'XYZ': rotation_utils.noop,
        'XZY': rotation_utils.noop,
        'YXZ': rotation_utils.noop,
        'YZX': rotation_utils.noop,
        'ZXY': rotation_utils.noop,
        'ZYX': rotation_utils.noop,
        'SWING_X': rotation_utils.euler_to_quaternion,
        'SWING_Y': rotation_utils.euler_to_quaternion,
        'SWING_Z': rotation_utils.euler_to_quaternion,
        'TWIST_X': partial(rotation_utils.euler_to_swing_twist_x, quaternion=True),
        'TWIST_Y': partial(rotation_utils.euler_to_swing_twist_y, quaternion=True),
        'TWIST_Z': partial(rotation_utils.euler_to_swing_twist_z, quaternion=True),
        'QUATERNION': rotation_utils.euler_to_quaternion,
        },
    'ZYX': {
        'AUTO': rotation_utils.noop,
        'XYZ': rotation_utils.noop,
        'XZY': rotation_utils.noop,
        'YXZ': rotation_utils.noop,
        'YZX': rotation_utils.noop,
        'ZXY': rotation_utils.noop,
        'ZYX': rotation_utils.noop,
        'SWING_X': rotation_utils.euler_to_quaternion,
        'SWING_Y': rotation_utils.euler_to_quaternion,
        'SWING_Z': rotation_utils.euler_to_quaternion,
        'TWIST_X': partial(rotation_utils.euler_to_swing_twist_x, quaternion=True),
        'TWIST_Y': partial(rotation_utils.euler_to_swing_twist_y, quaternion=True),
        'TWIST_Z': partial(rotation_utils.euler_to_swing_twist_z, quaternion=True),
        'QUATERNION': rotation_utils.euler_to_quaternion,
        },
    'SWING_X': {
        'AUTO': rotation_utils.quaternion_to_euler,
        'XYZ': rotation_utils.quaternion_to_euler,
        'XZY': rotation_utils.quaternion_to_euler,
        'YXZ': rotation_utils.quaternion_to_euler,
        'YZX': rotation_utils.quaternion_to_euler,
        'ZXY': rotation_utils.quaternion_to_euler,
        'ZYX': rotation_utils.quaternion_to_euler,
        'SWING_X': rotation_utils.noop,
        'SWING_Y': rotation_utils.noop,
        'SWING_Z': rotation_utils.noop,
        'TWIST_X': partial(rotation_utils.quaternion_to_swing_twist_x, quaternion=True),
        'TWIST_Y': partial(rotation_utils.quaternion_to_swing_twist_y, quaternion=True),
        'TWIST_Z': partial(rotation_utils.quaternion_to_swing_twist_z, quaternion=True),
        'QUATERNION': rotation_utils.noop,
        },
    'SWING_Y': {
        'AUTO': rotation_utils.quaternion_to_euler,
        'XYZ': rotation_utils.quaternion_to_euler,
        'XZY': rotation_utils.quaternion_to_euler,
        'YXZ': rotation_utils.quaternion_to_euler,
        'YZX': rotation_utils.quaternion_to_euler,
        'ZXY': rotation_utils.quaternion_to_euler,
        'ZYX': rotation_utils.quaternion_to_euler,
        'SWING_X': rotation_utils.noop,
        'SWING_Y': rotation_utils.noop,
        'SWING_Z': rotation_utils.noop,
        'TWIST_X': partial(rotation_utils.quaternion_to_swing_twist_x, quaternion=True),
        'TWIST_Y': partial(rotation_utils.quaternion_to_swing_twist_y, quaternion=True),
        'TWIST_Z': partial(rotation_utils.quaternion_to_swing_twist_z, quaternion=True),
        'QUATERNION': rotation_utils.noop,
        },
    'SWING_Z': {
        'AUTO': rotation_utils.quaternion_to_euler,
        'XYZ': rotation_utils.quaternion_to_euler,
        'XZY': rotation_utils.quaternion_to_euler,
        'YXZ': rotation_utils.quaternion_to_euler,
        'YZX': rotation_utils.quaternion_to_euler,
        'ZXY': rotation_utils.quaternion_to_euler,
        'ZYX': rotation_utils.quaternion_to_euler,
        'SWING_X': rotation_utils.noop,
        'SWING_Y': rotation_utils.noop,
        'SWING_Z': rotation_utils.noop,
        'TWIST_X': partial(rotation_utils.quaternion_to_swing_twist_x, quaternion=True),
        'TWIST_Y': partial(rotation_utils.quaternion_to_swing_twist_y, quaternion=True),
        'TWIST_Z': partial(rotation_utils.quaternion_to_swing_twist_z, quaternion=True),
        'QUATERNION': rotation_utils.noop,
        },
    'TWIST_X': {
        'AUTO': rotation_utils.swing_twist_x_to_euler,
        'XYZ': rotation_utils.swing_twist_x_to_euler,
        'XZY': rotation_utils.swing_twist_x_to_euler,
        'YXZ': rotation_utils.swing_twist_x_to_euler,
        'YZX': rotation_utils.swing_twist_x_to_euler,
        'ZXY': rotation_utils.swing_twist_x_to_euler,
        'ZYX': rotation_utils.swing_twist_x_to_euler,
        'SWING_X': rotation_utils.swing_twist_x_to_quaternion,
        'SWING_Y': rotation_utils.swing_twist_x_to_quaternion,
        'SWING_Z': rotation_utils.swing_twist_x_to_quaternion,
        'TWIST_X': rotation_utils.noop,
        'TWIST_Y': rotation_utils.swing_twist_x_to_swing_twist_y,
        'TWIST_Z': rotation_utils.swing_twist_x_to_swing_twist_z,
        'QUATERNION': rotation_utils.swing_twist_x_to_quaternion,
        },
    'TWIST_Y': {
        'AUTO': rotation_utils.swing_twist_y_to_euler,
        'XYZ': rotation_utils.swing_twist_y_to_euler,
        'XZY': rotation_utils.swing_twist_y_to_euler,
        'YXZ': rotation_utils.swing_twist_y_to_euler,
        'YZX': rotation_utils.swing_twist_y_to_euler,
        'ZXY': rotation_utils.swing_twist_y_to_euler,
        'ZYX': rotation_utils.swing_twist_y_to_euler,
        'SWING_X': rotation_utils.swing_twist_y_to_quaternion,
        'SWING_Y': rotation_utils.swing_twist_y_to_quaternion,
        'SWING_Z': rotation_utils.swing_twist_y_to_quaternion,
        'TWIST_X': rotation_utils.swing_twist_y_to_swing_twist_x,
        'TWIST_Y': rotation_utils.noop,
        'TWIST_Z': rotation_utils.swing_twist_y_to_swing_twist_z,
        'QUATERNION': rotation_utils.swing_twist_y_to_quaternion,
        },
    'QUATERNION': {
        'AUTO': rotation_utils.quaternion_to_euler,
        'XYZ': rotation_utils.quaternion_to_euler,
        'XZY': rotation_utils.quaternion_to_euler,
        'YXZ': rotation_utils.quaternion_to_euler,
        'YZX': rotation_utils.quaternion_to_euler,
        'ZXY': rotation_utils.quaternion_to_euler,
        'ZYX': rotation_utils.quaternion_to_euler,
        'SWING_X': rotation_utils.noop,
        'SWING_Y': rotation_utils.noop,
        'SWING_Z': rotation_utils.noop,
        'TWIST_X': partial(rotation_utils.quaternion_to_swing_twist_x, quaternion=True),
        'TWIST_Y': partial(rotation_utils.quaternion_to_swing_twist_y, quaternion=True),
        'TWIST_Z': partial(rotation_utils.quaternion_to_swing_twist_z, quaternion=True),
        'QUATERNION': rotation_utils.noop,
        }
    }

INPUT_ROTATION_MODE_ITEMS = ROTATION_MODE_ITEMS[0:-3] + [
    ('SWING_X'   , "X Swing"   , "Swing rotation to aim the X axis"            , 'NONE', 8),
    ('SWING_Y'   , "Y Swing"   , "Swing rotation to aim the Y axis"            , 'NONE', 9),
    ('SWING_Z'   , "Z Swing"   , "Swing rotation to aim the Z axis"            , 'NONE', 10),
    ('TWIST_X'   , "X Twist"   , "Twist around the X axis"                     , 'NONE', 11),
    ('TWIST_Y'   , "Y Twist"   , "Twist around the Y axis"                     , 'NONE', 12),
    ('TWIST_Z'   , "Z Twist"   , "Twist around the Z axis"                     , 'NONE', 13),
    ]

INPUT_ROTATION_MODE_INDEX = {
    item[0]: item[4] for item in INPUT_ROTATION_MODE_ITEMS
    }

INPUT_VARIABLE_DEFINITIONS = {
    'NONE': [
        {
        "type": VARIABLE_TYPE_INDEX['SINGLE_PROP'],
        "name": "var",
        "targets": []
        }
    ],
    'LOCATION': [
        {
        "type": VARIABLE_TYPE_INDEX['TRANSFORMS'],
        "name": "x",
        "default": 0.0,
        "targets": [
            {
            "transform_type": TRANSFORM_TYPE_INDEX['LOC_X'],
            "transform_space": TRANSFORM_SPACE_INDEX['LOCAL_SPACE'],
            }]
        },{
        "type": VARIABLE_TYPE_INDEX['TRANSFORMS'],
        "name": "y",
        "default": 0.0,
        "targets": [
            {
            "transform_type": TRANSFORM_TYPE_INDEX['LOC_Y'],
            "transform_space": TRANSFORM_SPACE_INDEX['LOCAL_SPACE'],
            }]
        },{
        "type": VARIABLE_TYPE_INDEX['TRANSFORMS'],
        "name": "z",
        "default": 0.0,
        "targets": [
            {
            "transform_type": TRANSFORM_TYPE_INDEX['LOC_Z'],
            "transform_space": TRANSFORM_SPACE_INDEX['LOCAL_SPACE'],
            }]
        }],
    'ROTATION': [
        {
        "type": VARIABLE_TYPE_INDEX['TRANSFORMS'],
        "name": "w",
        "default": 1.0,
        "targets": [
            {
            "transform_type": TRANSFORM_TYPE_INDEX['ROT_W'],
            "transform_space": TRANSFORM_SPACE_INDEX['LOCAL_SPACE'],
            "rotation_mode": ROTATION_MODE_INDEX['QUATERNION'],
            }]
        },{
        "type": VARIABLE_TYPE_INDEX['TRANSFORMS'],
        "name": "x",
        "default": 0.0,
        "targets": [
            {
            "transform_type": TRANSFORM_TYPE_INDEX['ROT_X'],
            "transform_space": TRANSFORM_SPACE_INDEX['LOCAL_SPACE'],
            "rotation_mode": ROTATION_MODE_INDEX['QUATERNION'],
            }
        ]},{
        "type": VARIABLE_TYPE_INDEX['TRANSFORMS'],
        "name": "y",
        "default": 0.0,
        "targets": [
            {
            "transform_type": TRANSFORM_TYPE_INDEX['ROT_Y'],
            "transform_space": TRANSFORM_SPACE_INDEX['LOCAL_SPACE'],
            "rotation_mode": ROTATION_MODE_INDEX['QUATERNION'],
            }]
        },{
        "type": VARIABLE_TYPE_INDEX['TRANSFORMS'],
        "name": "z",
        "default": 0.0,
        "targets": [
            {
            "transform_type": TRANSFORM_TYPE_INDEX['ROT_Z'],
            "transform_space": TRANSFORM_SPACE_INDEX['LOCAL_SPACE'],
            "rotation_mode": ROTATION_MODE_INDEX['QUATERNION'],
            }]
        }],
    'SCALE': [
        {
        "type": VARIABLE_TYPE_INDEX['TRANSFORMS'],
        "name": "x",
        "default": 1.0,
        "targets": [
            {
            "transform_type": TRANSFORM_TYPE_INDEX['SCALE_X'],
            "transform_space": TRANSFORM_SPACE_INDEX['LOCAL_SPACE'],
            }]
        },{
        "type": VARIABLE_TYPE_INDEX['TRANSFORMS'],
        "name": "y",
        "default": 1.0,
        "targets": [
            {
            "transform_type": TRANSFORM_TYPE_INDEX['SCALE_Y'],
            "transform_space": TRANSFORM_SPACE_INDEX['LOCAL_SPACE'],
            }]
        },{
        "type": VARIABLE_TYPE_INDEX['TRANSFORMS'],
        "name": "z",
        "default": 1.0,
        "targets": [
            {
            "transform_type": TRANSFORM_TYPE_INDEX['SCALE_Z'],
            "transform_space": TRANSFORM_SPACE_INDEX['LOCAL_SPACE'],
            }]
        }],
    'BBONE': [
        {
        "type": VARIABLE_TYPE_INDEX['SINGLE_PROP'],
        "name": "curveinx",
        "default": 0.0,
        "targets": [
            {
            "data_path": "pose.bones[""].bbone_curveinx"
            }]
        },{
        "type": VARIABLE_TYPE_INDEX['SINGLE_PROP'],
        "name": "curveiny",
        "default": 0.0,
        "targets": [
            {
            "data_path": "pose.bones[""].bbone_curveiny"
            }]
        },{
        "type": VARIABLE_TYPE_INDEX['SINGLE_PROP'],
        "name": "curveinz",
        "default": 0.0,
        "targets": [
            {
            "data_path": "pose.bones[""].bbone_curveinz"
            }]
        },
        {
        "type": VARIABLE_TYPE_INDEX['SINGLE_PROP'],
        "name": "curveoutx",
        "default": 0.0,
        "targets": [
            {
            "data_path": "pose.bones[""].bbone_curveoutx"
            }]
        },
        {
        "type": VARIABLE_TYPE_INDEX['SINGLE_PROP'],
        "name": "curveouty",
        "default": 0.0,
        "targets": [
            {
            "data_path": "pose.bones[""].bbone_curveouty"
            }]
        },{
        "type": VARIABLE_TYPE_INDEX['SINGLE_PROP'],
        "name": "curveoutz",
        "default": 0.0,
        "targets": [
            {
            "data_path": "pose.bones[""].bbone_curveoutz"
            }]
        },{
        "type": VARIABLE_TYPE_INDEX['SINGLE_PROP'],
        "name": "easein",
        "default": 0.0,
        "targets": [
            {
            "data_path": "pose.bones[""].bbone_easein"
            }]
        },{
        "type": VARIABLE_TYPE_INDEX['SINGLE_PROP'],
        "name": "easeout",
        "default": 0.0,
        "targets": [
            {
            "data_path": "pose.bones[""].bbone_easeout"
            }]
        },{
        "type": VARIABLE_TYPE_INDEX['SINGLE_PROP'],
        "name": "rollin",
        "default": 0.0,
        "targets": [
            {
            "data_path": "pose.bones[""].bbone_rollin"
            }]
        },{
        "type": VARIABLE_TYPE_INDEX['SINGLE_PROP'],
        "name": "rollout",
        "default": 0.0,
        "targets": [
            {
            "data_path": "pose.bones[""].bbone_rollout"
            }]
        },{
        "type": VARIABLE_TYPE_INDEX['SINGLE_PROP'],
        "name": "scaleinx",
        "default": 0.0,
        "targets": [
            {
            "data_path": f'pose.bones[""].bbone_scalein{"x" if version[0] < 3 else "[0]"}'
            }]
        },{
        "type": VARIABLE_TYPE_INDEX['SINGLE_PROP'],
        "name": "scaleiny",
        "default": 0.0,
        "targets": [
            {
            "data_path": f'pose.bones[""].bbone_scalein{"y" if version[0] < 3 else "[1]"}'
            }]
        },{
        "type": VARIABLE_TYPE_INDEX['SINGLE_PROP'],
        "name": "scaleinz",
        "default": 0.0,
        "targets": [
            {
            "data_path": f'pose.bones[""].bbone_scalein{"z" if version[0] < 3 else "[1]"}'
            }]
        },{
        "type": VARIABLE_TYPE_INDEX['SINGLE_PROP'],
        "name": "scaleoutx",
        "default": 0.0,
        "targets": [
            {
            "data_path": f'pose.bones[""].bbone_scaleout{"x" if version[0] < 3 else "[0]"}'
            }]
        },{
        "type": VARIABLE_TYPE_INDEX['SINGLE_PROP'],
        "name": "scaleouty",
        "default": 0.0,
        "targets": [
            {
            "data_path": f'pose.bones[""].bbone_scaleout{"y" if version[0] < 3 else "[1]"}'
            }]
        },{
        "type": VARIABLE_TYPE_INDEX['SINGLE_PROP'],
        "name": "scaleoutz",
        "default": 0.0,
        "targets": [
            {
            "data_path": f'pose.bones[""].bbone_scaleout{"z" if version[0] < 3 else "[1]"}'
            }]
        }
    ],
    'SHAPE_KEY': [
        {
        "type": VARIABLE_TYPE_INDEX['SINGLE_PROP'],
        "name": "",
        "targets": [
            {
            "id_type": 'KEY',
            "data_path": 'key_blocks[""].value'
            }]
        }
    ]
    }

#endregion Configuration

#region Data Layer
###################################################################################################

#region Input Target
###################################################################################################

def input_target_bone_target_update_handler(target: 'RBFDriverInputTarget', _) -> None:
    input = target.input
    value = target.bone_target

    if input.type in ('LOCATION', 'ROTATION', 'SCALE'):
        for variable in input.variables:
            variable.targets[0]["bone_target"] = value
        input_pose_distance_driver_update_all(input, pose_count=input.pose_count)    

    elif input.type == 'BBONE':
        for variable, spec in zip(input.variables, BBONE_VARIABLES):
            variable.targets[0]["data_path"] = f'pose.bones["{value}"].{spec["path"]}'
        input_pose_distance_driver_update_all(input, pose_count=input.pose_count)


def input_target_data_path_get(target: 'RBFDriverInputTarget') -> str:
    return target.get("data_path", "")


def input_target_data_path_set(target: 'RBFDriverInputTarget', value: str) -> None:
    input = target.input
    if input.type in ('BBONE', 'SHAPE_KEY'):
        raise RuntimeError((f'{target.__class__.__name__}.data_path '
                            f'is not user-editable for inputs of type {input.type}'))
    elif input.type == 'NONE':
        input_pose_distance_driver_update_all(input, pose_count=input.pose_count)


def input_target_id_type_update_handler(target: 'RBFDriverInputTarget', _) -> None:
    input = target.input
    if input.type == 'NONE':
        input_pose_distance_driver_update_all(input, pose_count=input.pose_count)


def input_target_object_update_handler(target: 'RBFDriverInputTarget', _) -> None:
    input = target.input
    value = target.object

    if input.type in ('LOCATION', 'ROTATION', 'SCALE', 'BBONE', 'SHAPE_KEY'):
        for variable in input.variables:
            variable.targets[0]["object"] = value
        input_pose_distance_driver_update_all(input, pose_count=input.pose_count)


def input_target_rotation_mode_update_handler(target: 'RBFDriverInputTarget', _) -> None:
    input = target.input
    value = target.get("rotation_mode")

    if input.type == 'ROTATION':
        for variable in input.variables:
            variable.targets[0]["rotation_mode"] = value
        input_pose_distance_driver_update_all(input, pose_count=input.pose_count)


def input_target_transform_space_update_handler(target: 'RBFDriverInputTarget', _) -> None:
    input = target.input
    value = target.get("transform_space")

    if input.type in ('LOCATION', 'ROTATION', 'SCALE'):
        for variable in input.variables:
            variable.targets[0]["transform_space"] = value
        input_pose_distance_driver_update_all(input, pose_count=input.pose_count)


def input_target_transform_type_update_handler(target: 'RBFDriverInputTarget', _) -> None:
    input = target.input
    if input.type == 'NONE':
        input_pose_distance_driver_update_all(input, pose_count=input.pose_count)


class RBFDriverInputTarget(PropertyGroup):

    bone_target: StringProperty(
        name="Bone",
        description="The pose bone to target",
        options=set(),
        update=input_target_bone_target_update_handler
        )

    data_path: StringProperty(
        name="Path",
        description="The path to the target property",
        get=input_target_data_path_get,
        set=input_target_data_path_set,
        options=set(),
        )

    id_type: EnumProperty(
        name="Type",
        description="The type of ID to target",
        items=ID_TYPE_ITEMS,
        default='OBJECT',
        options=set(),
        update=input_target_id_type_update_handler
        )

    @property
    def id(self) -> Optional[ID]:
        """The target's ID data-block"""
        object = self.object
        if object is None or self.id_type == 'OBJECT': return object
        if object.type == self.id_type: return object.data

    @property
    def input(self) -> 'RBFDriverInput':
        """The input to which this input target belongs"""
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".variables.")[0])

    object: PointerProperty(
        name="Object",
        description="The target object",
        type=Object,
        poll=lambda self, object: self.id_type in (object.type, 'OBJECT'),
        options=set(),
        update=input_target_object_update_handler
        )

    rotation_mode: EnumProperty(
        name="Rotation",
        description="The rotation mode for the input target data",
        items=ROTATION_MODE_ITEMS,
        default=ROTATION_MODE_ITEMS[0][0],
        options=set(),
        update=input_target_rotation_mode_update_handler
        )

    transform_space: EnumProperty(
        name="Space",
        description="The space for transform channels",
        items=TRANSFORM_SPACE_ITEMS,
        default=TRANSFORM_SPACE_ITEMS[0][0],
        options=set(),
        update=input_target_transform_space_update_handler
        )

    transform_type: EnumProperty(
        name="Type",
        description="The transform channel to target",
        items=TRANSFORM_TYPE_ITEMS,
        default=TRANSFORM_TYPE_ITEMS[0][0],
        options=set(),
        update=input_target_transform_type_update_handler
        )

#endregion Input Target

#region Input Targets
###################################################################################################

class RBFDriverInputTargets(PropertyGroup):

    data__internal__: CollectionProperty(
        type=RBFDriverInputTarget,
        options={'HIDDEN'}
        )

    size__internal__: IntProperty(
        min=1,
        max=2,
        get=lambda self: self.get("size__internal__", 1),
        options={'HIDDEN'}
        )

    def __contains__(self, target: Any) -> bool:
        return any((item == target for item in self))

    def __len__(self) -> int:
        return self.size__internal__

    def __iter__(self) -> Iterator[RBFDriverInputTarget]:
        return iter(self.data__internal__[:self.size__internal__])

    def __getitem__(self, key: Union[int, slice]) -> Union[RBFDriverInputTarget, List[RBFDriverInputTarget]]:

        if isinstance(key, int):
            if 0 < key > self.size__internal__: raise IndexError(f'{self.size__internal__}')
            return self.data__internal__[key]

        if isinstance(key, slice):
            return self.data__internal__[key]

        raise TypeError((f'{self.__class__.__name__}[key]: '
                         f'Expected key to be int or slice, not {key.__class__.__name__}'))

#endregion Input Targets

#region Input Variable
###################################################################################################

def input_variable_name_update_handler(variable: 'RBFDriverInputVariable', _) -> None:
    input = variable.input
    if input.type == 'SHAPE_KEY':
        target: RBFDriverInputTarget = variable.targets[0]
        target["data_path"] = f'key_blocks["{variable.name}"].value'
        input_pose_distance_driver_update_all(input, pose_count=input.pose_count)


def input_variable_type_update_handler(variable: 'RBFDriverInputVariable', _) -> None:
    input = variable.input
    if input.type == 'SHAPE_KEY':
        variable["type"] = 0
        raise RuntimeError((f'{variable.__class__.__name__}.type '
                            f'is not user-editable for shape key inputs.'))


def input_variable_enabled_update_handler(variable: 'RBFDriverInputVariable', _) -> None:
    variable.input.update()


class RBFDriverInputVariable(PropertyGroup):

    data: PointerProperty(
        name="Data",
        description="The RBF pose data (internal-use)",
        type=RBFDriverPoseDataVector,
        options=set()
        )

    default: FloatProperty(
        name="Default",
        description="The default value for the variable",
        default=0.0,
        options=set(),
        )

    enabled: BoolProperty(
        name="Enabled",
        description="Include of exclude the variable from the RBF driver calculations",
        default=False,
        options=set(),
        update=input_variable_enabled_update_handler
        )

    @property
    def input(self) -> 'RBFDriverInput':
        """The input to which this input variable belongs"""
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".variables.")[0])

    name: StringProperty(
        name="Name",
        description="Variable name",
        options=set(),
        update=input_variable_name_update_handler
        )

    targets: PointerProperty(
        name="Targets",
        description="Input target definitions",
        type=RBFDriverInputTargets,
        options=set()
        )

    type: EnumProperty(
        name="Type",
        description="The variable type",
        items=VARIABLE_TYPE_ITEMS,
        default='SINGLE_PROP',
        options=set(),
        update=input_variable_type_update_handler
        )

    @property
    def value(self) -> float:
        """The current value of the variable"""
        type = self.type

        if type == 'TRANSFORMS':
            t = self.targets[0]
            m = transform_matrix(transform_target(t.object, t.bone_target), t.transform_space)
            return transform_matrix_element(m, t.transform_type, t.rotation_mode, driver=True)

        if type == 'LOC_DIFF':
            a = self.targets[0]
            b = self.targets[1]
            return transform_target_distance(transform_target(a.object, a.bone_target),
                                             transform_target(b.object, b.bone_target),
                                             a.transform_space,
                                             b.transform_space)

        if type == 'ROT_DIFF':
            a = self.targets[0]
            b = self.targets[1]
            return transform_target_rotational_difference(transform_target(a.object, a.bone_target),
                                                          transform_target(b.object, b.bone_target))

        if type == 'SINGLE_PROP':
            t = self.targets[0]
            o = t.id
            if o:
                try:
                    v = o.path_resolve(t.data_path)
                except ValueError:
                    pass
                else:
                    if isinstance(v, (float, int, bool)):
                        return float(v)

        return 0.0

#endregion Input Variable

#region Input Variables
###################################################################################################

class RBFDriverInputVariables(PropertyGroup):

    collection__internal__: CollectionProperty(
        type=RBFDriverInputVariable,
        options={'HIDDEN'}
        )

    def __contains__(self, name: str) -> bool:
        return any((var.name == name for var in self))

    def __len__(self) -> int:
        return len(self.collection__internal__)

    def __iter__(self) -> Iterator[RBFDriverInputVariable]:
        return iter(self.collection__internal__)

    def __getitem__(self, key: Union[str, int, slice]) -> Union[RBFDriverInputVariable, List[RBFDriverInputVariable]]:
        if isinstance(key, str):
            variable = next((var for var in self if var.name == key), None)
            if variable is None:
                raise KeyError(f'{self.__class__.__name__}[key]: "{key}" not found.')
            return variable

        if isinstance(key, int):
            if 0 > key >= len(self):
                raise IndexError((f'{self.__class__.__name__}[key]: '
                                  f'Index {key} out of range 0-{len(self)}.'))

            return self.collection__internal__[key]

        if isinstance(key, slice):
            return self.collection__internal__[key]

        raise TypeError((f'{self.__class__.__name__}[key]: '
                         f'Expected key to be str, int or slice, not {key.__class__.__name__}.'))

    def find(self, name: str) -> int:
        return next((i for i, var in enumerate(self) if var.name == name), -1)

    def get(self, name: str, default: Optional[object]=None) -> Any:
        return self.collection__internal__.get(name, default)

#endregion Input Variables

#region Input
###################################################################################################

def input_name_update_handler(input: 'RBFDriverInput', _) -> None:
    names = [input.name for input in input.id_data.path_resolve(input.path_from_id(".")[0])]
    value = input.name
    index = 0
    while value in names:
        index += 1
        value = f'{input.name}.{str(index).zfill(3)}'
    input["name"] = value


def input_rotation_mode_get(input: 'RBFDriverInput') -> int:
    return input.get("rotation_mode", 0)


def input_rotation_mode_set(input: 'RBFDriverInput', value: int) -> None:
    cache = input_rotation_mode_get(input)
    if cache == value:
        return

    input["rotation_mode"] = value
    if input.type != 'ROTATION':
        return

    prevmode = INPUT_ROTATION_MODE_INDEX[cache]
    currmode = INPUT_ROTATION_MODE_INDEX[value]
    convert = ROTATION_CONVERSION_LUT[prevmode][currmode]

    matrix = np.array([
        tuple(scalar.value for scalar in variable.data) for variable in input.variables
        ], dtype=np.float)

    for vector, column in zip(matrix.T if len(prevmode) > 4 else matrix[1:].T,
                              matrix.T if len(currmode) > 4 else matrix[1:].T):
        column[:] = convert(vector)

    if len(currmode) < 5:
        matrix[0] = 0.0

    for variable, data in zip(input.variables, matrix):
        variable.data.__init__(data)
    
    input.update()


class RBFDriverInput(Identifiable, PropertyGroup):

    @property
    def influence_property_name(self) -> str:
        return f'rbfi_infl_{self.identifier}'

    @property
    def influence_property_path(self) -> str:
        return f'["{self.influence_property_name}"]'

    name: StringProperty(
        name="Name",
        options=set(),
        update=input_name_update_handler
        )

    @property
    def pose_count(self) -> int:
        return len(self.rbf_driver.poses)

    @property
    def pose_distance_property_name(self) -> str:
        return f'rbfi_dist_{self.identifier}'

    @property
    def pose_distance_property_path(self) -> str:
        return f'["{self.pose_distance_property_name}"]'

    pose_radii: PointerProperty(
        name="Radii",
        type=RBFDriverPoseDataVector,
        options=set()
        )

    @property
    def rbf_driver(self) -> 'RBFDriver':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".inputs.")[0])

    variables: PointerProperty(
        name="Variables",
        type=RBFDriverInputVariables,
        options=set()
        )

    rotation_mode: EnumProperty(
        name="Mode",
        description="Rotation mode",
        items=ROTATION_MODE_ITEMS[0:-3] + [
            ('SWING_X'   , "X Swing"   , "Swing rotation to aim the X axis"            , 'NONE', 8),
            ('SWING_Y'   , "Y Swing"   , "Swing rotation to aim the Y axis"            , 'NONE', 9),
            ('SWING_Z'   , "Z Swing"   , "Swing rotation to aim the Z axis"            , 'NONE', 10),
            ('TWIST_X'   , "X Twist"   , "Twist around the X axis"                     , 'NONE', 11),
            ('TWIST_Y'   , "Y Twist"   , "Twist around the Y axis"                     , 'NONE', 12),
            ('TWIST_Z'   , "Z Twist"   , "Twist around the Z axis"                     , 'NONE', 13),
            ],
        get=input_rotation_mode_get,
        set=input_rotation_mode_set,
        options=set(),
        )

    type: EnumProperty(
        name="Type",
        items=LAYER_TYPE_ITEMS,
        get=lambda self: self.get("type", 0),
        options=set(),
        )

    def update(self) -> None:
        pose_count = self.pose_count
        input_pose_radii_update(self)
        input_pose_distance_idprop_update(self, pose_count)
        input_pose_distance_driver_update_all(self, pose_count)
        input_pose_distance_fcurve_update_all(self, pose_count)

#endregion Input

#region Inputs
###################################################################################################

class RBFDriverInputs(Identifiable, PropertyGroup):

    active_index: IntProperty(
        name="Index",
        description="Index of the active pose",
        min=0,
        default=0,
        options=set(),
        )

    @property
    def active(self) -> Optional[RBFDriverInput]:
        index = self.active_index
        return self[index] if index < len(self) else None

    collection__internal__: CollectionProperty(
        type=RBFDriverInput,
        options={'HIDDEN'}
        )

    @property
    def summed_influence_property_name(self) -> str:
        return f'rbfi_sinf_{self.identifier}'

    @property
    def summed_influence_property_path(self) -> str:
        return f'["{self.summed_influence_property_name}"]'

    def __len__(self) -> int:
        return len(self.collection__internal__)

    def __getitem__(self, key: Union[str, int, slice]) -> Union[RBFDriverInput, List[RBFDriverInput]]:
        return self.collection__internal__[key]

    def __contains__(self, name: str) -> bool:
        return name in self.collection__internal__

    def __iter__(self) -> Iterator[RBFDriverInput]:
        return iter(self.collection__internal__)

    def find(self, name: str) -> int:
        return self.collection__internal__.find(name)

    def get(self, name: str, default: Optional[object]=None) -> Any:
        return self.collection__internal__.get(name, default)

    def keys(self) -> List[str]:
        return self.collection__internal__.keys()

    def items(self) -> List[Tuple[str, RBFDriverInput]]:
        return self.collection__internal__.items()

    def values(self) -> List[RBFDriverInput]:
        return list(self)

#endregion Inputs
#endregion Data Layer

#region Service Layer
###################################################################################################

def input_pose_distance_metric_angle(a: Sequence[float], b: Sequence[float], axis: str) -> float:
    index = 'WXYZ'.index(axis)
    return fabs(a[index], b[index])


def input_pose_distance_metric_euclidean(a: Sequence[float], b: Sequence[float]) -> float:
    return sqrt(sum(pow(ai - bi, 2.0) for ai, bi in zip(a, b)))


def input_pose_distance_metric_quaternion(a: Sequence[float], b: Sequence[float]) -> float:
    return acos((2.0 * pow(min(max(sum(ai * bi for ai, bi in zip(a, b)), -1.0), 1.0), 2.0)) - 1.0) / pi


def input_pose_distance_metric_direction(a: Sequence[float], b: Sequence[float], axis: str) -> float:
    aw, ax, ay, az = a
    bw, bx, by, bz = b

    if axis == 'X':
        a = (1.0 - 2.0 * (ay * ay + az * az), 2.0 * (ax * ay + aw * az), 2.0 * (ax * az - aw * ay))
        b = (1.0 - 2.0 * (by * by + bz * bz), 2.0 * (bx * by + bw * bz), 2.0 * (bx * bz - bw * by))
    elif axis == 'Y':
        a = (2.0 * (ax * ay - aw * az), 1.0 - 2.0 * (ax * ax + az * az), 2.0 * (ay * az + aw * ax))
        b = (2.0 * (bx * by - bw * bz), 1.0 - 2.0 * (bx * bx + bz * bz), 2.0 * (by * bz + bw * bx))
    else:
        a = (2.0 * (ax * az + aw * ay), 2.0 * (ay * az - aw * ax), 1.0 - 2.0 * (ax * ax + ay * ay))
        b = (2.0 * (bx * bz + bw * by), 2.0 * (by * bz - bw * bx), 1.0 - 2.0 * (bx * bx + by * by))

    return (asin((sum(ai * bi for ai, bi in zip(a, b)))) - -(pi / 2.0)) / pi


def input_pose_distance_metric(input: RBFDriverInput) -> Callable[[Sequence[float], Sequence[float]], float]:
    if input.type == 'ROTATION':
        mode = input.rotation_mode
        if mode == 'QUATERNION': return input_pose_distance_metric_quaternion
        if mode.startswith('SWING'): return partial(input_pose_distance_metric_direction, axis=mode[-1])
        if mode.startswith('TWIST'): return partial(input_pose_distance_metric_angle, axis=mode[-1])
    return input_pose_distance_metric_euclidean


def input_pose_distance_matrix(input: RBFDriverInput) -> np.ndarray:
    metric = input_pose_distance_metric(input)
    params = np.array([tuple(var.data.values()) for var in input.variables], dtype=np.float).T
    matrix = np.empty((len(params), len(params)), dtype=np.float)
    for param, row in zip(params, matrix):
        for index, other in enumerate(params):
            row[index] = metric(param, other)
    return matrix


def input_pose_radii_update(input: RBFDriverInput) -> None:
    matrix = input_pose_distance_matrix(input).view(np.ma.MaskedArray)
    matrix.mask = np.identity(len(matrix), dtype=np.bool)
    matrix.fill_value = 0.0
    input.pose_radii.__init__(tuple(map(np.min, matrix)))


def input_pose_data_update(input: RBFDriverInput, pose_index: int) -> None:
    for variable in input.variables:
        variable.data[pose_index]["value"] = variable.value


def input_pose_distance_driver_update_xyz(driver: Driver,
                                  input: RBFDriverInput,
                                  pose_index: int,
                                  transform_type: str,
                                  **target_props: Dict[str, Any]) -> None:

    if len(input.variables) != 3:
        raise RuntimeError()

    params = []

    for axis, input_variable in zip('XYZ', input.variables):
        if input_variable.enabled:
            driver_variable = driver.variables.new()
            driver_variable.type = 'TRANSFORMS'
            driver_variable.name = axis.lower()

            input_target = input_variable.targets[0]
            driver_target = driver_variable.targets[0]

            driver_target.id = input_target.id
            driver_target.bone_target = input_target.bone_target
            driver_target.transform_type = f'{transform_type}_{axis}'
            driver_target.transform_space = input_target.transform_space

            for key, value in target_props.items():
                setattr(driver_target, key, value)

            params.append((driver_variable.name, str(input_variable.data[pose_index].value)))

    if params:
        driver.expression = f'sqrt({"+".join("pow("+a+"-"+b+",2.0)" for a, b in params)})'
    else:
        driver.expression = "0.0"


def input_pose_distance_driver_update_location(driver: Driver, input: RBFDriverInput, pose_index: int) -> None:
    return input_pose_distance_driver_update_xyz(driver, input, pose_index, 'LOC')


def input_pose_distance_driver_update_scale(driver: Driver, input: RBFDriverInput, pose_index: int) -> None:
    return input_pose_distance_driver_update_xyz(driver, input, pose_index, 'SCALE')


def input_pose_distance_driver_update_rotation_euler(driver: Driver, input: RBFDriverInput, pose_index: int, rotation_mode: str) -> None:
    return input_pose_distance_driver_update_xyz(driver, input, pose_index, 'ROT', rotation_mode=rotation_mode)


def input_pose_distance_driver_update_rotation_swing(driver: Driver, input: RBFDriverInput, pose_index: int) -> None:
    params = []

    for axis, input_variable in zip('WXYZ', input.variables):
        driver_variable = driver.variables.new()
        driver_variable.type = 'TRANSFORMS'
        driver_variable.name = axis.lower()

        input_target = input_variable.targets[0]
        driver_target = driver_variable.targets[0]

        driver_target.id = input_target.object
        driver_target.bone_target = input_target.bone_target
        driver_target.transform_type = f'ROT_{axis}'
        driver_target.rotation_mode = 'QUATERNION'
        driver_target.transform_space = input_target.transform_space

        params.append(input_variable.data[pose_index].value)

    if not params:
        driver.expression = "0.0"
    else:
        axis = input.rotation_mode[-1]
        w, x, y, z = params
        driver.type = 'SCRIPTED'

        if axis == 'X':
            a = str(1.0-2.0*(y*y+z*z))
            b = str(2.0*(x*y+w*z))
            c = str(2.0*(x*z-w*y))
            driver.expression = f'(asin((1.0-2.0*(y*y+z*z))*{a}+2.0*(x*y+w*z)*{b}+2.0*(x*z-w*y)*{c})-(pi/2.0))/pi'

        elif axis == 'Y':
            a = str(2.0*(x*y-w*z))
            b = str(1.0-2.0*(x*x+z*z))
            c = str(2.0*(y*z+w*x))
            driver.expression = f'(asin(2.0*(x*y-w*z)*{a}+(1.0-2.0*(x*x+z*z))*{b}+2.0*(y*z+w*x)*{c})--(pi/2.0))/pi'

        else:
            a = str(2.0*(x*z+w*y))
            b = str(2.0*(y*z-w*x))
            c = str(1.0-2.0*(x*x+y*y))
            driver.expression = f'(asin(2.0*(x*z+w*y)*{a}+2.0*(y*z-w*x)*{b}+(1.0-2.0*(x*x+y*y))*{c})--(pi/2.0))/pi'


def input_pose_distance_driver_update_rotation_twist(driver: Driver, input: RBFDriverInput, pose_index: int) -> None:
    axis = input.rotation_mode[-1]
    input_variable = input.varibles['WXYZ'.index(axis)]

    driver_variable = driver.variables.new()
    driver_variable.type = 'TRANSFORMS'
    driver_variable.name = axis.lower()

    input_target = input_variable.targets[0]

    driver_target = driver_variable.targets[0]
    driver_target.id = input_target.object
    driver_target.bone_target = input_target.bone_target
    driver_target.rotation_mode = f'SWING_TWIST_{axis}'
    driver_target.transform_type = f'ROT_{axis}'
    driver_target.transform_space = input_target.transform_space

    driver.type = 'SCRIPTED'
    driver.expression = f'fabs({driver_variable.name}-{str(input_variable.data[pose_index].value)})/pi'


def input_pose_distance_driver_update_rotation_quaternion(driver: Driver, input: RBFDriverInput, index: int) -> None:
    params = []
    for axis, input_variable in zip('WXYZ', input.variables):

        driver_variable = driver.variables.new()
        driver_variable.type = 'TRANSFORMS'
        driver_variable.name = axis.lower()

        input_target = input_variable.targets[0]

        driver_target = driver_variable.targets[0]
        driver_target.id = input_target.object
        driver_target.bone_target = input_target.bone_target
        driver_target.transform_type = f'ROT_{axis}'
        driver_target.rotation_mode = 'QUATERNION'
        driver_target.transform_space = input_target.transform_space

        params.append((driver_variable.name, str(input_variable.data[index].value)))

    driver.expression = f'acos((2.0*pow(clamp({"+".join(["*".join(x) for x in params])},-1.0,1.0),2.0))-1.0)/pi'


def input_pose_distance_driver_update_bbone(driver: Driver, input: RBFDriverInput, index: int) -> None:
    params = []
    varkeys = DriverVariableNameGenerator()

    for input_variable in input.variables:
        if input_variable.enabled:
            driver_variable = driver.variables.new()
            driver_variable.type = input_variable.type
            driver_variable.name = next(varkeys)

            for input_target, driver_target in zip(input_variable.targets, driver_variable.targets):
                driver_target.id = input_target.object
                driver_target.data_path = input_target.data_path

            data = [scalar.value for scalar in input_variable.data]
            norm = np.linalg.norm(data)
            params.append((driver_variable.name, str(data[index] / norm if norm != 0.0 else data[index]), str(norm)))

    if params:
        driver.expression = f'sqrt({"+".join("pow("+a+("" if n==0.0 else "/"+str(n))+"-"+b+",2.0)" for a, b, n in params)})'
    else:
        driver.expression = "0.0"


def input_pose_distance_driver_update_generic(driver: Driver, input: RBFDriverInput, index: int) -> None:
    params = []
    varkeys = DriverVariableNameGenerator()

    for input_variable in input.variables:
        driver_variable = driver.variables.new()
        driver_variable.type = input_variable.type
        driver_variable.name = next(varkeys)

        for input_target, driver_target in zip(input_variable.targets, driver_variable.targets):
            driver_target.id_type = input_target.id_type
            driver_target.id = input_target.id
            driver_target.bone_target = input_target.bone_target
            driver_target.rotation_mode = input_target.rotation_mode
            driver_target.transform_type = input_target.transform_type
            driver_target.transform_space = input_target.transform_space
            driver_target.data_path = input_target.data_path

        data = [scalar.value for scalar in input_variable.data]
        norm = np.linalg.norm(data)
        params.append((driver_variable.name, str(data[index] / norm if norm != 0.0 else data[index]), norm))

    if params:
        driver.expression = f'sqrt({"+".join("pow("+a+("" if n==0.0 else "/"+str(n))+"-"+b+",2.0)" for a, b, n in params)})'
    else:
        driver.expression = "0.0"


def input_pose_distance_idprop_update(input: RBFDriverInput, pose_count: int) -> None:
    input.id_data.data[input.pose_distance_property_name] = [0.0] * pose_count


def input_pose_distance_idprop_remove(input: RBFDriverInput) -> None:
    try:
        del input.id_data.data[input.pose_distance_property_name]
    except KeyError: pass


def input_pose_distance_idprop_update_all(inputs: RBFDriverInputs, pose_count: int) -> None:
    for input in inputs:
        input_pose_distance_idprop_update(input, pose_count)


def input_pose_distance_driver_update(input: RBFDriverInput, pose_index: int) -> None:
    fcurve = driver_ensure(input.id_data.data, input.pose_distance_property_path, pose_index)
    driver = fcurve.driver
    driver.type = 'SCRIPTED'
    driver_variables_clear(driver.variables)

    input_type = input.type

    if input_type == 'LOCATION':
        return input_pose_distance_driver_update_location(driver, input, pose_index)

    if input_type == 'ROTATION':
        rotation_mode = input.rotation_mode

        if len(rotation_mode) < 5:
            return input_pose_distance_driver_update_rotation_euler(driver, input, pose_index, rotation_mode=rotation_mode)
        if rotation_mode == 'QUATERNION':
            return input_pose_distance_driver_update_rotation_quaternion(driver, input, pose_index)
        if rotation_mode.startswith('SWING'):
            return input_pose_distance_driver_update_rotation_swing(driver, input, pose_index)
        if rotation_mode.startswith('TWIST'):
            return input_pose_distance_driver_update_rotation_twist(driver, input, pose_index)

    if input_type == 'SCALE':
        return input_pose_distance_driver_update_scale(driver, input, pose_index)

    if input_type == 'BBONE':
        return input_pose_distance_driver_update_bbone(driver, input, pose_index)

    return input_pose_distance_driver_update_generic(driver, input, pose_index)


def input_pose_distance_driver_update_all(input: RBFDriverInput, pose_count: int) -> None:
    for pose_index in range(pose_count):
        input_pose_distance_driver_update(input, pose_index)


def input_pose_distance_driver_remove(input: RBFDriverInput, pose_index: int) -> None:
    driver_remove(input.id_data.data, input.pose_distance_property_path, pose_index)


def input_pose_distance_driver_remove_all(input: RBFDriverInput) -> None:
    animdata = input.id_data.animation_data
    if animdata:
        data_path = input.pose_distance_property_path
        for fcurve in list(animdata.drivers):
            if fcurve.data_path == data_path:
                animdata.drivers.remove(fcurve)


def input_pose_distance_fcurve_update(input: RBFDriverInput, pose_index: int) -> None:
    fcurve = driver_ensure(input.id_data.data, input.pose_distance_property_path, pose_index)
    points = fcurve.keyframe_points

    while len(points) > 2:
        points.remove(points[-2])

    distance = input.pose_radii[pose_index].value

    for point, (co, hl, hr) in zip(points, (
        ((0., 1.), (-.25, 1.), (distance*.25, .75)),
        ((distance, 0.), (distance*.75, .25), (distance*1.25, 0.))
        )):
        point.interpolation = 'BEZIER'
        point.co = co
        point.handle_left_type = 'FREE'
        point.handle_right_type = 'FREE'
        point.handle_left = hl
        point.handle_right = hr


def input_pose_distance_fcurve_update_all(input: RBFDriverInput, pose_count: int) -> None:
    for pose_index in range(pose_count):
        input_pose_distance_fcurve_update(input, pose_index)


def input_influence_idprop_create(input: RBFDriverInput) -> None:
    rna_idprop_ui_create(input.id_data.data,
                         input.influence_property_name,
                         **INFLUENCE_IDPROP_SETTINGS)


def input_influence_idprop_ensure(input: RBFDriverInput) -> None:
    if not isinstance(input.id_data.data.get(input.influence_property_name), float):
        input_influence_idprop_create(input)


def input_influence_idprop_remove(input: RBFDriverInput) -> None:
    try:
        del input.id_data.data[input.influence_property_name]
    except KeyError: pass


def input_influence_idprop_remove_all(inputs: RBFDriverInputs) -> None:
    for input in inputs:
        input_influence_idprop_remove(input)


def input_influence_sum_idprop_ensure(inputs: RBFDriverInputs) -> None:
    inputs.id_data.data[inputs.summed_influence_property_name] = 0.0


def input_influence_sum_idprop_remove(inputs: RBFDriverInputs) -> None:
    try:
        del inputs.id_data.data[inputs.summed_influence_property_name]
    except KeyError: pass


def input_influence_sum_driver_update(inputs: RBFDriverInputs) -> None:
    fcurve = driver_ensure(inputs.id_data.data, inputs.summed_influence_property_path)
    driver = fcurve.driver
    driver.type = 'SUM'
    driver_variables_clear(driver.variables)

    for index, input in enumerate(inputs):
        variable = driver.variables.new()
        variable.name = f'var_{str(index).zfill(3)}'
        variable.type = 'SINGLE_PROP'

        target = variable.targets[0]
        target.id_type = inputs.id_data.type
        target.id = inputs.id_data.data
        target.data_path = input.influence_property_path


def input_influence_sum_driver_remove(inputs: RBFDriverInputs) -> None:
    driver_remove(inputs.id_data.data, inputs.summed_influence_property_path)

#endregion Service Layer