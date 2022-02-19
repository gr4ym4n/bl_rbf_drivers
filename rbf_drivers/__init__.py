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

from . import posedata, input, pose, output, driver, ops, ui
from .lib import curve_mapping

curve_mapping.BLCMAP_OT_curve_copy.bl_idname = "rbf_driver.curve_copy"
curve_mapping.BLCMAP_OT_curve_paste.bl_idname = "rbf_driver.curve_paste"
curve_mapping.BLCMAP_OT_curve_edit.bl_idname = "rbf_driver.curve_edit"

def classes():
    return [
        curve_mapping.BLCMAP_CurvePointProperties,
        curve_mapping.BLCMAP_CurveProperties,
        curve_mapping.BLCMAP_CurvePoint,
        curve_mapping.BLCMAP_CurvePoints,
        curve_mapping.BLCMAP_Curve,
        curve_mapping.BLCMAP_OT_curve_copy,
        curve_mapping.BLCMAP_OT_curve_paste,
        curve_mapping.BLCMAP_OT_curve_edit,
        posedata.RBFDriverPoseDataScalar,
        posedata.RBFDriverPoseDataVector,
        posedata.RBFDriverActivePoseDataValue,
        input.RBFDriverInputTarget,
        input.RBFDriverInputTargets,
        input.RBFDriverInputVariable,
        input.RBFDriverInputVariables,
        input.RBFDriverInputActivePoseData,
        input.RBFDriverInput,
        input.RBFDriverInputs,
        pose.RBFDriverPoseFalloff,
        pose.RBFDriverPose,
        pose.RBFDriverPoses,
        output.RBFDriverOutputChannelRange,
        output.RBFDriverOutputChannel,
        output.RBFDriverOutputChannels,
        output.RBFDriverOutputActivePoseData,
        output.RBFDriverOutput,
        output.RBFDriverOutputs,
        driver.RBFDriverFalloff,
        driver.RBFDriver,
        driver.RBFDrivers,
        ops.ShapeKeyTarget,
        ops.RBFDRIVERS_OT_new,
        ops.RBFDRIVERS_OT_remove,
        ops.RBFDRIVERS_OT_move_up,
        ops.RBFDRIVERS_OT_move_down,
        ops.RBFDRIVERS_OT_input_add,
        ops.RBFDRIVERS_OT_input_remove,
        ops.RBFDRIVERS_OT_input_move_up,
        ops.RBFDRIVERS_OT_input_move_down,
        ops.RBFDRIVERS_OT_pose_add,
        ops.RBFDRIVERS_OT_pose_remove,
        ops.RBFDRIVERS_OT_pose_update,
        ops.RBFDRIVERS_OT_pose_move_up,
        ops.RBFDRIVERS_OT_pose_move_down,
        ops.RBFDRIVERS_OT_output_add,
        ops.RBFDRIVERS_OT_output_remove,
        ops.RBFDRIVERS_OT_output_move_up,
        ops.RBFDRIVERS_OT_output_move_down,
        ui.RBFDRIVERS_UL_drivers,
        ui.RBFDRIVERS_PT_drivers,
        ui.RBFDRIVERS_PT_interpolation,
        ui.RBFDRIVERS_UL_inputs,
        ui.RBFDRIVERS_PT_input_location_symmetry_settings,
        ui.RBFDRIVERS_PT_input_rotation_symmetry_settings,
        ui.RBFDRIVERS_PT_input_scale_symmetry_settings,
        ui.RBFDRIVERS_PT_input_bbone_curvein_symmetry_settings,
        ui.RBFDRIVERS_PT_input_bbone_curveout_symmetry_settings,
        ui.RBFDRIVERS_PT_input_bbone_roll_symmetry_settings,
        ui.RBFDRIVERS_PT_inputs,
        ui.RBFDRIVERS_UL_outputs,
        ui.RBFDRIVERS_PT_output_location_symmetry_settings,
        ui.RBFDRIVERS_PT_output_rotation_symmetry_settings,
        ui.RBFDRIVERS_PT_output_scale_symmetry_settings,
        ui.RBFDRIVERS_PT_output_bbone_curvein_symmetry_settings,
        ui.RBFDRIVERS_PT_output_bbone_curveout_symmetry_settings,
        ui.RBFDRIVERS_PT_output_bbone_roll_symmetry_settings,
        ui.RBFDRIVERS_PT_outputs,
        ui.RBFDRIVERS_UL_poses,
        ui.RBFDRIVERS_PT_poses,
        ui.RBFDRIVERS_PT_pose_interpolation,
        ui.RBFDRIVERS_PT_pose_input_values,
        ui.RBFDRIVERS_PT_pose_output_values,
        ]

def register():
    import bpy

    for cls in classes():
        bpy.utils.register_class(cls)

    bpy.types.Object.rbf_drivers = bpy.props.PointerProperty(
        name="RBF Drivers",
        description="Radial Basis Function Drivers",
        type=driver.RBFDrivers,
        options={'HIDDEN'}
        )

def unregister():
    import sys
    import bpy
    import operator

    try:
        del bpy.types.Object.rbf_drivers
    except: pass

    for cls in reversed(classes()):
        bpy.utils.unregister_class(cls)

    modules_ = sys.modules 
    modules_ = dict(sorted(modules_.items(), key=operator.itemgetter(0)))
   
    for name in modules_.keys():
        if name.startswith(__name__):
            del sys.modules[name]

