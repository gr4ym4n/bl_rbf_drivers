
from typing import Callable, Optional, Sequence, Set, Tuple, Union, TYPE_CHECKING
from math import acos, asin, fabs, isclose, pi, sqrt
from functools import partial
from string import ascii_letters
import numpy as np
from ..app.utils import (
    copyattrs,
    listattrs,
    DataFrame,
    idprop_array,
    idprop_update,
    idprop_drivers,
    idprop_variables
    )
from ..app.events import event_handler
from ..api.input_targets import (
    InputTargetBoneTargetUpdateEvent,
    InputTargetDataPathUpdateEvent,
    InputTargetIDTypeUpdateEvent,
    InputTargetObjectUpdateEvent,
    InputTargetRotationModeUpdateEvent,
    InputTargetTransformSpaceUpdateEvent,
    InputTargetTransformTypeUpdateEvent
    )
from ..api.input_variables import (
    InputVariableIsEnabledUpdateEvent,
    InputVariableNewEvent,
    InputVariableRemovedEvent,
    InputVariableTypeUpdateEvent
    )
from ..api.input import (
    InputBoneTargetUpdateEvent,
    InputDisposableEvent,
    InputObjectUpdateEvent,
    InputRotationAxisUpdateEvent,
    InputRotationModeUpdateEvent,
    InputTransformSpaceUpdateEvent
    )
from ..api.poses import PoseNewEvent, PoseRemovedEvent
from ..api.input_data import InputSampleUpdateEvent
from ..api.drivers import DriverDisposableEvent
if TYPE_CHECKING:
    from bpy.types import FCurve
    from ..api.input_targets import InputTargetPropertyUpdateEvent
    from ..api.input_variables import InputVariablesUpdateEvent, InputVariable
    from ..api.input import Input, InputPropertyUpdateEvent


class pose_data(DataFrame['Input']):

    def __init__(self, input: 'Input') -> None:
        data = [tuple(v.data.values()) for v in input.variables.enabled]
        data = idprop_array(data, f'input_{input.identifier}_data')
        norm = None
        if input.type == 'USER_DEF':
            norm = idprop_array([np.linalg.norm(r) or 1.0 for r in data], f'input_{input.identifier}_norm')
        self.data = data
        self.norm = norm
        idprop_update(input.id_data.data, data)

    def update(self, *args: Union[Tuple, Tuple[int, int, float]]) -> None:
        input: 'Input' = self.source
        if args:
            row, col, val = args
            data = self.data[row]
            norm = self.norm
            if norm:
                norm = norm[col]
                data["value"] = np.array(tuple(input.variables[col].data.values()), dtype=float)
                norm["value"] = np.linalg.norm(data["value"]) or 1.0
                data["value"] /= norm["value"]
                idprop_update(self.id, data)
                idprop_update(self.id, norm)
                distance_matrix(input).update()
            else:
                data = data[col]
                data["value"] = val
                idprop_update(self.id, data)
                distance_matrix(input).update(row)
        else:
            self.__init__(input)
            distance_matrix(input).update()


class distance_matrix(DataFrame['Input']):

    @staticmethod
    def _euclidean(a: Sequence[float], b: Sequence[float]) -> float:
        return sqrt(sum(pow(ai - bi, 2.0) for ai, bi in zip(a, b)))

    @staticmethod
    def _angle(a: Sequence[float], b: Sequence[float]) -> float:
        return fabs(a[0]-b[0])/pi

    @staticmethod
    def _quaternion(a: Sequence[float], b: Sequence[float]) -> float:
        return acos((2.0 * pow(min(max(sum(ai * bi for ai, bi in zip(a, b)), -1.0), 1.0), 2.0)) - 1.0) / pi

    @staticmethod
    def _direction(a: Sequence[float], b: Sequence[float], axis: str) -> float:
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

    def _function(self) -> Callable[[Sequence[float], Sequence[float]], float]:
        o = self.source
        t = o.type
        if t == 'ROTATION':
            m = o.rotation_mode
            if m == 'QUATERNION': return self._quaternion
            if m == 'SWING'     : return partial(self._direction, axis=o.rotation_axis)
            if m == 'TWIST'     : return self._angle
        return self._euclidean

    def __init__(self, input: 'Input') -> None:
        src = pose_data(input).data["value"]
        dfn = self._function()
        out = np.array([dfn(a, b) for a in src for b in src], dtype=float)
        self.data = out.reshape(src.shape[0], src.shape[0])

    def update(self, index: Optional[int]=None) -> None:
        input = self.input
        if index is None:
            self.__init__(input)
        else:
            src = pose_data(input).data["value"]
            out = self.data
            dfn = partial(self._function(), src[index])
            out[index] = out.T[index] = list(map(dfn, src))
        pose_radii(input).update()


class pose_radii(DataFrame['Input']):

    def __init__(self, input: 'Input') -> None:
        src = np.ma.masked_values(distance_matrix(input).data, 0.0, atol=0.001)
        out = np.empty(len(src), dtype=float)
        for i, row in enumerate(src):
            row = row.compressed()
            out[i] = 0.0 if len(row) else np.min(row)
        self.data = out

    def update(self) -> None:
        input = self.source

        src = distance_matrix(input).data
        out = self.data
        wgt = pose_weights(input)
        flg = {'FCURVE'}

        if len(src) != len(out):
            self.__init__(input)
            wgt.update(flags=flg)
        else:
            src = np.ma.masked_values(src, 0.0, atol=0.001)
            for i, (row, rad) in enumerate(zip(src, out)):
                row = row.compressed()
                val = 0.0 if len(row) == 0 else np.min(row)
                if not isclose(val, rad, abs_tol=0.001):
                    out[i] = val
                    wgt.update(i, flg)


class pose_weights(DataFrame['Input']):

    TARGET_PROPS = {
        'SINGLE_PROP' : ("id_type", "id", "data_path"),
        'TRANSFORMS' : ("id", "bone_target", "transform_type", "transform_space", "rotation_mode"),
        'DISTANCE' : ("id", "bone_target"),
        'ROTATION_DIFF' : ("id", "bone_target", "transform_space"),
    }

    @staticmethod    
    def _euclidean(tokens: Sequence[Tuple[str, str]]) -> None:
        return f'sqrt({"+".join("pow("+a+"-"+b+",2.0)" for a, b in tokens)})'

    @staticmethod
    def _quaternion(tokens: Sequence[Tuple[str, str]]) -> None:
        return f'acos((2.0*pow(clamp({"+".join(["*".join(x) for x in tokens])},-1.0,1.0),2.0))-1.0)/pi'

    @staticmethod
    def _swing(tokens: Sequence[Tuple[str, str]], axis: str) -> None:
        w, x, y, z = tokens
        if axis == 'X':
            a = str(1.0-2.0*(y*y+z*z))
            b = str(2.0*(x*y+w*z))
            c = str(2.0*(x*z-w*y))
            e = f'(asin((1.0-2.0*(y*y+z*z))*{a}+2.0*(x*y+w*z)*{b}+2.0*(x*z-w*y)*{c})-(pi/2.0))/pi'
        elif axis == 'Y':
            a = str(2.0*(x*y-w*z))
            b = str(1.0-2.0*(x*x+z*z))
            c = str(2.0*(y*z+w*x))
            e = f'(asin(2.0*(x*y-w*z)*{a}+(1.0-2.0*(x*x+z*z))*{b}+2.0*(y*z+w*x)*{c})--(pi/2.0))/pi'
        else:
            a = str(2.0*(x*z+w*y))
            b = str(2.0*(y*z-w*x))
            c = str(1.0-2.0*(x*x+y*y))
            e = f'(asin(2.0*(x*z+w*y)*{a}+2.0*(y*z-w*x)*{b}+(1.0-2.0*(x*x+y*y))*{c})--(pi/2.0))/pi'
        return e

    @staticmethod
    def _twist(tokens: Sequence[Tuple[str, str]]) -> None:
        return f'fabs({tokens[0][0]}-{str(tokens[0][1])})/pi'

    def _function(self) -> Callable[[Sequence[Tuple[str, str]]], str]:
        o = self.source
        if o.type == 'ROTATION':
            m = o.rotation_mode
            if m == 'SWING'     : partial(self._swing, axis=o.rotation_axis)
            if m == 'TWIST'     : self._twist
            if m == 'QUATERNION': self._quaternion
        self._euclidean

    def __init__(self, input: 'Input') -> None:
        data = [0.0] * len(pose_data(input).data)
        name = f'input_{input.identifier}_poseweights'
        data = idprop_array(data, name)
        self.data = data
        idprop_update(self.id, data)

    def update(self,
               *args: Union[Tuple, Tuple[int], Tuple[Set[str]], Tuple[int, Set[str]]]) -> None:
        input: 'Input' = self.source
        if len(pose_data(input).data) != len(self.data):
            self.__init__(input)
        if not args:
            index = None
            flags = {'DRIVER', 'FCURVE'}
        elif isinstance(args[0], set):
            index = None
            flags = args[0]
        else:
            index = args[0]
            flags = args[1] if len(args) > 1 else {'DRIVER', 'FCURVE'}
        if index is None:
            self._update_all(input, flags)
        else:
            self._update_one(input, index, flags)

    def _update_all(self, input: 'Input', flags: Set[str]) -> None:
        if 'FCURVE' in flags:
            self._update_all_fcurves(input)
        if 'DRIVER' in flags:
            self._update_all_drivers(input)

    def _update_one(self, input: 'Input', index: int, flags: Set[str]) -> None:
        fc = idprop_drivers(input.id_data.data, self.data[index], clear_vars='DRIVER' in flags)
        if 'FCURVE' in flags:
            self._update_fcurve(fc, pose_radii(input).data)
        if 'DRIVER' in flags:
            data = pose_data(input)
            vars = list(input.variables)
            func = self._function()
            self._update_driver(fc, data.data, data.norm, vars, func)

    @staticmethod
    def _update_fcurve(fcurve: 'FCurve', radii: np.ndarray) -> None:
        rad = radii[fcurve.array_index]["value"]
        pts = fcurve.keyframe_points
        num = len(pts)
        while num > 2:
            pts.remove(pts[-1])
            num -= 1
        while num < 2:
            pts.insert(float(num), 0.0)
            num += 1
        for pt in pts:
            pt.interpolation = 'BEZIER'
            pt.easing = 'AUTO'
            pt.handle_left_type = 'AUTO_CLAMPED'
            pt.handle_right_type = 'AUTO_CLAMPED'
        pts[0].co_ui = (0.0, 1.0)
        pts[1].co_ui = (rad, 0.0)

    def _update_all_fcurves(self, input: 'Input') -> None:
        radii = pose_radii(input).data
        for fc in idprop_drivers(input.id_data.data, self.data):
            self._update_fcurve(fc, radii)

    def _update_driver(self,
                       fcurve: 'FCurve',
                       data: np.ndarray,
                       norms: Optional[np.ndarray],
                       variables: Sequence['InputVariable'],
                       distance_function: Callable[[Sequence[Tuple[str, str]]], str]) -> None:
        ob = self.source.id_data
        dr = fcurve.driver
        ai = fcurve.array_index
        values = ascii_letters[:len(variables)]
        for src, key in zip(variables, ascii_letters):
            var = dr.variables.new()
            var.type = src.type
            var.name = key
            for a, b in zip(src.targets, var.targets):
                copyattrs(a, b, self.TARGET_PROPS[var.type])
        params = listattrs("name", idprop_variables(dr, ob, data[ai]))
        if norms:
            norms_ = listattrs("name", idprop_variables(dr, ob, norms))
            params = list(map("/".join, zip(params, norms_)))
        dr.expression = distance_function(tuple(zip(values, params)))

    def _update_all_drivers(self, input: 'Input') -> None:
        vars = list(input.variables)
        data = pose_data(input)
        norm = data.norm
        data = data.data
        func = self._function()
        for fc in idprop_drivers(input.id_data.data, self.data, 'SCRIPTED', clear_vars=True):
            self._update_driver(fc, data, norm, vars, func)


@event_handler(InputSampleUpdateEvent)
def on_input_sample_update(event: InputSampleUpdateEvent) -> None:
    sample = event.sample
    pose_data(sample.input).update(sample.index, sample.variable.index, event.value)


@event_handler(InputTargetBoneTargetUpdateEvent,
               InputTargetDataPathUpdateEvent,
               InputTargetIDTypeUpdateEvent,
               InputTargetObjectUpdateEvent,
               InputTargetRotationModeUpdateEvent,
               InputTargetTransformSpaceUpdateEvent,
               InputTargetTransformTypeUpdateEvent)
def on_input_target_property_update(event: 'InputTargetPropertyUpdateEvent') -> None:
    if event.target.variable.is_enabled:
        pose_weights(event.input).update({'DRIVER'})


@event_handler(InputBoneTargetUpdateEvent,
               InputObjectUpdateEvent,
               InputRotationAxisUpdateEvent,
               InputTransformSpaceUpdateEvent)
def on_input_variable_(event: 'InputPropertyUpdateEvent') -> None:
    pose_weights(event.input).update({'DRIVER'})


@event_handler(InputRotationModeUpdateEvent)
def on_input_rotation_mode_update(event: InputRotationModeUpdateEvent) -> None:
    pose_data(event.input).update()
    pose_weights(input).update({'DRIVER'})


@event_handler(InputVariableIsEnabledUpdateEvent)
def on_input_variable_is_enabled_update(event: InputVariableIsEnabledUpdateEvent) -> None:
    input = event.variable.input
    pose_data(input).update()
    pose_weights(input).update({'DRIVER'})


@event_handler(InputVariableTypeUpdateEvent)
def on_input_variable_type_update(event: InputVariableTypeUpdateEvent) -> None:
    if event.variable.is_enabled:
        pose_weights(event.variable.input).update({'DRIVER'})


@event_handler(InputVariableNewEvent, InputVariableRemovedEvent)
def on_input_variables_update(event: 'InputVariablesUpdateEvent') -> None:
    input = event.variables.input
    pose_data(input).update()
    pose_weights(input).update({'DRIVER'})


@event_handler(PoseNewEvent)
def on_pose_new(event: PoseNewEvent) -> None:
    index = event.pose.index
    for input in event.pose.driver.inputs:
        pose_data(input).update()
        pose_weights(input).update()


@event_handler(PoseRemovedEvent)
def on_pose_removed(event: PoseRemovedEvent) -> None:
    index = event.index
    for input in event.poses.driver.inputs:
        pose_data(input).update()
        pose_weights(input).update()


@event_handler(InputDisposableEvent)
def on_input_disposable(event: InputDisposableEvent) -> None:
    input = event.input
    for cls in (pose_data, distance_matrix, pose_radii, pose_weights):
        cls.delete(input)


@event_handler(DriverDisposableEvent)
def on_driver_disposable(event: DriverDisposableEvent) -> None:
    classes = (pose_data, distance_matrix, pose_radii, pose_weights)
    for input in event.driver.inputs:
        for cls in classes:
            cls.delete(input)
