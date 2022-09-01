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
    "location": "View3D > Properties > Object",
    "doc_url": "https://jamesvsnowden.github.io/bl_rbf_drivers/",
    "tracker_url": "https://github.com/jamesvsnowden/bl_rbf_drivers/issues",
    "category": "Animation",
    "warning": ""
}

def api_input_layer():
    from .api.input_targets import InputTarget, InputTargets
    from .api.input_data import InputSample, InputData
    from .api.input_variables import InputVariable, InputVariables
    from .api.input_distance_matrix import InputDistance, InputDistanceMatrix
    from .api.input_pose_radii import InputPoseRadius, InputPoseRadii
    



UPDATE_URL = ""

from .lib.curve_mapping import (BLCMAP_CurvePointProperties,
                                BLCMAP_CurveProperties,
                                BLCMAP_CurvePoint,
                                BLCMAP_CurvePoints,
                                BLCMAP_Curve,
                                BLCMAP_OT_curve_copy,
                                BLCMAP_OT_curve_paste,
                                BLCMAP_OT_node_ensure,
                                BCLMAP_OT_curve_point_remove,
                                BLCMAP_OT_handle_type_set)

from .api.selection_item import RBFDriverSelectionItem
from .api.property_target import RBFDriverPropertyTarget
from .api.input_targets import InputTarget
from .api.input_targets import InputTargets
from .api.input_sample import InputSample
from .api.input_data import InputData
from .api.input_variables import InputVariable
from .api.input_variables import InputVariables
from .api.inputs import Input
from .api.inputs import Inputs
from .api.pose_interpolation import RBFDriverPoseInterpolation
from .api.poses import Pose
from .api.poses import Poses
from .api.output_data import OutputSample
from .api.output_channel_data import OutputData
from .api.output_channels import OutputChannel
from .api.output_channels import RBFDriverOutputChannels
from .api.output import Output
from .api.outputs import RBFDriverOutputs
from .api.driver_interpolation import RBFDriverInterpolation
from .api.driver import RBFDriver
from .api.drivers import RBFDrivers
from .api.preferences import RBFDriverPreferences

from .app import (name_manager,
                  node_manager,
                  property_manager,
                  input_initialization_manager,
                  input_target_manager,
                  input_variable_data_manager,
                  pose_initialization_manager,
                  pose_weight_driver_manager,
                  output_initialization_manager,
                  output_channel_data_manager,
                  output_channel_driver_manager,
                  symmetry_manager)

from .ops.input import (RBFDRIVERS_OT_input_add,
                        RBFDRIVERS_OT_input_remove,
                        RBFDRIVERS_OT_input_decompose,
                        RBFDRIVERS_OT_input_move_up,
                        RBFDRIVERS_OT_input_move_down,
                        RBFDRIVERS_OT_input_variable_add,
                        RBFDRIVERS_OT_input_variable_remove)

from .ops.output import (RBFDRIVERS_OT_output_add,
                         RBFDRIVERS_OT_output_remove,
                         RBFDRIVERS_OT_output_move_up,
                         RBFDRIVERS_OT_output_move_down)

from .ops.pose import (RBFDRIVERS_OT_pose_add,
                       RBFDRIVERS_OT_pose_remove,
                       RBFDRIVERS_OT_pose_update,
                       RBFDRIVERS_OT_pose_move_up,
                       RBFDRIVERS_OT_pose_move_down)

from .ops.driver import (RBFDRIVERS_OT_new,
                         RBFDRIVERS_OT_remove,
                         RBFDRIVERS_OT_symmetrize,
                         RBFDRIVERS_OT_make_generic,
                         RBFDRIVERS_OT_move_up,
                         RBFDRIVERS_OT_move_down,
                         LegacyDriver,
                         RBFDRIVERS_OT_upgrade)

from .gui.generic import RBFDRIVERS_UL_selection_list
from .gui.drivers import (RBFDRIVERS_UL_drivers,
                          RBFDRIVERS_MT_driver_context_menu,
                          RBFDRIVERS_PT_drivers,
                          RBFDRIVERS_PT_interpolation)
from .gui.inputs import RBFDRIVERS_UL_inputs, RBFDRIVERS_MT_input_context_menu, RBFDRIVERS_PT_inputs
from .gui.outputs import RBFDRIVERS_UL_outputs, RBFDRIVERS_PT_outputs
from .gui.poses import RBFDRIVERS_MT_pose_context_menu, RBFDRIVERS_UL_poses, RBFDRIVERS_PT_poses

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
        BLCMAP_OT_node_ensure,
        BCLMAP_OT_curve_point_remove,
        BLCMAP_OT_handle_type_set,
        # api
        RBFDriverSelectionItem,
        RBFDriverPropertyTarget,
        InputTarget,
        InputTargets,
        InputSample,
        InputData,
        InputVariable,
        InputVariables,
        Input,
        Inputs,
        RBFDriverPoseInterpolation,
        Pose,
        Poses,
        OutputSample,
        OutputData,
        OutputChannel,
        RBFDriverOutputChannels,
        Output,
        RBFDriverOutputs,
        RBFDriverInterpolation,
        RBFDriver,
        RBFDrivers,
        RBFDriverPreferences,
        # ops
        RBFDRIVERS_OT_input_add,
        RBFDRIVERS_OT_input_remove,
        RBFDRIVERS_OT_input_decompose,
        RBFDRIVERS_OT_input_move_up,
        RBFDRIVERS_OT_input_move_down,
        RBFDRIVERS_OT_input_variable_add,
        RBFDRIVERS_OT_input_variable_remove,
        RBFDRIVERS_OT_output_add,
        RBFDRIVERS_OT_output_remove,
        RBFDRIVERS_OT_output_move_up,
        RBFDRIVERS_OT_output_move_down,
        RBFDRIVERS_OT_pose_add,
        RBFDRIVERS_OT_pose_remove,
        RBFDRIVERS_OT_pose_update,
        RBFDRIVERS_OT_pose_move_up,
        RBFDRIVERS_OT_pose_move_down,
        RBFDRIVERS_OT_new,
        RBFDRIVERS_OT_remove,
        RBFDRIVERS_OT_symmetrize,
        RBFDRIVERS_OT_make_generic,
        RBFDRIVERS_OT_move_up,
        RBFDRIVERS_OT_move_down,
        LegacyDriver,
        RBFDRIVERS_OT_upgrade,
        # gui
        RBFDRIVERS_UL_selection_list,
        RBFDRIVERS_UL_drivers,
        RBFDRIVERS_MT_driver_context_menu,
        RBFDRIVERS_PT_drivers,
        RBFDRIVERS_PT_interpolation,
        RBFDRIVERS_MT_input_context_menu,
        RBFDRIVERS_UL_inputs,
        RBFDRIVERS_PT_inputs,
        RBFDRIVERS_UL_outputs,
        RBFDRIVERS_PT_outputs,
        RBFDRIVERS_MT_pose_context_menu,
        RBFDRIVERS_UL_poses,
        RBFDRIVERS_PT_poses,
        ]

def register():
    from bpy.types import Object
    from bpy.props import PointerProperty
    from bpy.utils import register_class

    BLCMAP_OT_curve_copy.bl_idname = "rbf_driver.curve_copy"
    BLCMAP_OT_curve_paste.bl_idname = "rbf_driver.curve_paste"
    BLCMAP_OT_handle_type_set.bl_idname = "rbf_driver.handle_type_set"

    from .lib import update
    update.register("rbf_drivers", UPDATE_URL)

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

    from .lib import update
    update.unregister()

    modules_ = sys.modules 
    modules_ = dict(sorted(modules_.items(), key=operator.itemgetter(0)))
   
    for name in modules_.keys():
        if name.startswith(__name__):
            del sys.modules[name]

