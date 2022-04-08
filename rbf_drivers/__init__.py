'''
Copyright (C) 2021 James Snowden
james@metaphysic.al
Created by James Snowden
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

bl_info = {
    "name": "RBF Drivers",
    "description": "Radial basis function drivers.",
    "author": "James Snowden",
    "version": (2, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D",
    "wiki_url": "https://rbfdrivers.readthedocs.io/en/latest/",
    "category": "Animation",
    "warning": ""
}

from .lib.curve_mapping import (BLCMAP_CurvePointProperties,
                                BLCMAP_CurveProperties,
                                BLCMAP_CurvePoint,
                                BLCMAP_CurvePoints,
                                BLCMAP_Curve,
                                BLCMAP_OT_curve_copy,
                                BLCMAP_OT_curve_paste,
                                BLCMAP_OT_curve_edit,
                                BLCMAP_OT_node_ensure)

from .api.property_target import RBFDriverPropertyTarget
from .api.pose_data import RBFDriverPoseDatum, RBFDriverPoseDataPathItem, RBFDriverPoseDataGroup, RBFDriverPoseData
from .api.input_target import RBFDriverInputTarget
from .api.input_targets import RBFDriverInputTargets
from .api.input_variable_data_sample import RBFDriverInputVariableDataSample
from .api.input_variable_data import RBFDriverInputVariableData
from .api.input_variable import RBFDriverInputVariable
from .api.input_variables import RBFDriverInputVariables
from .api.input import RBFDriverInput
from .api.inputs import RBFDriverInputs
from .api.pose_interpolation import RBFDriverPoseInterpolation
from .api.pose import RBFDriverPose
from .api.poses import RBFDriverPoses
from .api.output_channel_data_sample import RBFDriverOutputChannelDataSample
from .api.output_channel_data import RBFDriverOutputChannelData
from .api.output_channel import RBFDriverOutputChannel
from .api.output_channels import RBFDriverOutputChannels
from .api.output import RBFDriverOutput
from .api.outputs import RBFDriverOutputs
from .api.driver_interpolation import RBFDriverInterpolation
from .api.driver import RBFDriver
from .api.drivers import RBFDrivers

from .ops.input import (RBFDRIVERS_OT_input_display_settings,
                        RBFDRIVERS_OT_input_add,
                        RBFDRIVERS_OT_input_remove,
                        RBFDRIVERS_OT_input_move)

from .ops.output import (RBFDRIVERS_OT_output_display_settings,
                         RBFDRIVERS_OT_output_add,
                         RBFDRIVERS_OT_output_remove,
                         RBFDRIVERS_OT_output_move_up,
                         RBFDRIVERS_OT_output_move_down)

from .ops.pose import (RBFDRIVERS_OT_pose_display_settings,
                       RBFDRIVERS_OT_pose_add,
                       RBFDRIVERS_OT_pose_remove,
                       RBFDRIVERS_OT_pose_update,
                       RBFDRIVERS_OT_pose_data_update,
                       RBFDRIVERS_OT_pose_move_up,
                       RBFDRIVERS_OT_pose_move_down)

from .ops.driver import (RBFDRIVERS_OT_new,
                         RBFDRIVERS_OT_remove,
                         RBFDRIVERS_OT_move_up,
                         RBFDRIVERS_OT_move_down)

from .gui.drivers import (RBFDRIVERS_UL_drivers,
                          RBFDRIVERS_PT_drivers)

from .gui.inputs import (RBFDRIVERS_PT_input_location_symmetry_settings,
                         RBFDRIVERS_PT_inputs)

from .gui.outputs import (RBFDRIVERS_PT_output_location_symmetry_settings,
                          RBFDRIVERS_PT_output_rotation_settings,
                          RBFDRIVERS_PT_outputs)

from .gui.poses import (RBFDRIVERS_MT_pose_context_menu,
                        RBFDRIVERS_UL_poses,
                        RBFDRIVERS_PT_poses,
                        RBFDRIVERS_PT_pose_input_values,
                        RBFDRIVERS_PT_pose_output_values)

from .app import (name_manager,
                  node_manager,
                  property_manager,
                  input_initialization_manager,
                  input_target_manager,
                  input_variable_data_manager,
                  input_pose_data_manager,
                  pose_initialization_manager,
                  pose_weight_driver_manager,
                  output_initialization_manager,
                  output_channel_manager,
                  output_channel_data_manager,
                  output_driver_manager,
                  output_pose_data_manager,
                  symmetry_manager)

def classes():
    return [
        # lib
        BLCMAP_CurvePointProperties,
        BLCMAP_CurveProperties,
        BLCMAP_CurvePoint,
        BLCMAP_CurvePoints,
        BLCMAP_Curve,
        BLCMAP_OT_curve_copy,
        BLCMAP_OT_curve_paste,
        BLCMAP_OT_curve_edit,
        BLCMAP_OT_node_ensure,
        # api
        RBFDriverPropertyTarget,
        RBFDriverPoseDatum,
        RBFDriverPoseDataPathItem,
        RBFDriverPoseDataGroup,
        RBFDriverPoseData,
        RBFDriverInputTarget,
        RBFDriverInputTargets,
        RBFDriverInputVariableDataSample,
        RBFDriverInputVariableData,
        RBFDriverInputVariable,
        RBFDriverInputVariables,
        RBFDriverInput,
        RBFDriverInputs,
        RBFDriverPoseInterpolation,
        RBFDriverPose,
        RBFDriverPoses,
        RBFDriverOutputChannelDataSample,
        RBFDriverOutputChannelData,
        RBFDriverOutputChannel,
        RBFDriverOutputChannels,
        RBFDriverOutput,
        RBFDriverOutputs,
        RBFDriverInterpolation,
        RBFDriver,
        RBFDrivers,
        # ops
        RBFDRIVERS_OT_input_display_settings,
        RBFDRIVERS_OT_input_add,
        RBFDRIVERS_OT_input_remove,
        RBFDRIVERS_OT_input_move,
        RBFDRIVERS_OT_output_display_settings,
        RBFDRIVERS_OT_output_add,
        RBFDRIVERS_OT_output_remove,
        RBFDRIVERS_OT_output_move_up,
        RBFDRIVERS_OT_output_move_down,
        RBFDRIVERS_OT_pose_display_settings,
        RBFDRIVERS_OT_pose_add,
        RBFDRIVERS_OT_pose_remove,
        RBFDRIVERS_OT_pose_update,
        RBFDRIVERS_OT_pose_data_update,
        RBFDRIVERS_OT_pose_move_up,
        RBFDRIVERS_OT_pose_move_down,
        RBFDRIVERS_OT_new,
        RBFDRIVERS_OT_remove,
        RBFDRIVERS_OT_move_up,
        RBFDRIVERS_OT_move_down,
        # gui
        RBFDRIVERS_UL_drivers,
        RBFDRIVERS_PT_drivers,
        RBFDRIVERS_PT_input_location_symmetry_settings,
        RBFDRIVERS_PT_inputs,
        RBFDRIVERS_PT_output_location_symmetry_settings,
        RBFDRIVERS_PT_output_rotation_settings,
        RBFDRIVERS_PT_outputs,
        # RBFDRIVERS_PT_interpolation,
        RBFDRIVERS_MT_pose_context_menu,
        RBFDRIVERS_UL_poses,
        RBFDRIVERS_PT_poses,
        RBFDRIVERS_PT_pose_input_values,
        RBFDRIVERS_PT_pose_output_values,
        ]

def register():
    from bpy.types import Object
    from bpy.props import PointerProperty
    from bpy.utils import register_class

    BLCMAP_OT_curve_copy.bl_idname = "rbf_driver.curve_copy"
    BLCMAP_OT_curve_paste.bl_idname = "rbf_driver.curve_paste"
    BLCMAP_OT_curve_edit.bl_idname = "rbf_driver.curve_edit"

    for cls in classes():
        register_class(cls)

    Object.rbf_drivers = PointerProperty(
        name="RBF Drivers",
        description="Radial Basis Function Drivers",
        type=RBFDrivers,
        options={'HIDDEN'}
        )

def unregister():
    import sys
    import operator
    from bpy.types import Object
    from bpy.utils import unregister_class

    try:
        del Object.rbf_drivers
    except: pass

    for cls in reversed(classes()):
        unregister_class(cls)

    modules_ = sys.modules 
    modules_ = dict(sorted(modules_.items(), key=operator.itemgetter(0)))
   
    for name in modules_.keys():
        if name.startswith(__name__):
            del sys.modules[name]

