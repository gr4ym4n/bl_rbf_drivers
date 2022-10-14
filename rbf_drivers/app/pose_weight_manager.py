
from typing import Iterable, Optional, Tuple, TYPE_CHECKING
from string import ascii_letters
from mathutils import Vector
from .events import event_handler
from ..api.pose_data_ import (
    pose_data_component_driver,
    pose_data_component_fcurve,
    pose_data_container_remove,
    pose_data_group_delete
    )
from ..api.pose_interpolation import PoseInterpolationPoint, PoseInterpolationUpdateEvent
from ..api.poses import PoseNewEvent, PoseRemovedEvent
from ..api.driver import RBFDriver
from ..api.drivers import DriverNewEvent, DriverDisposableEvent
if TYPE_CHECKING:
    from ..api.pose_interpolation import PoseInterpolation


def calculate_bezier_handles(p2: Vector,
                             ht: str,
                             h1: Vector,
                             h2: Vector,
                             prev:Optional[Vector]=None,
                             next:Optional[Vector]=None) -> None:
    pt = Vector((0.0, 0.0))

    if prev is None:
        p3 = next
        pt[0] = 2.0 * p2[0] - p3[0]
        pt[1] = 2.0 * p2[1] - p3[1]
        p1 = pt
    else:
        p1 = prev

    if next is None:
        p1 = prev
        pt[0] = 2.0 * p2[0] - p1[0]
        pt[1] = 2.0 * p2[1] - p1[1]
        p3 = pt
    else:
        p3 = next

    dvec_a = p2 - p1
    dvec_b = p3 - p2
    len_a = dvec_a.length
    len_b = dvec_b.length

    if len_a == 0.0:
        len_a = 1.0
    if len_b == 0.0:
        len_b = 1.0

    if ht in ('AUTO', 'AUTO_CLAMPED'):
        tvec = Vector((
            dvec_b[0] / len_b + dvec_a[0] / len_a,
            dvec_b[1] / len_b + dvec_a[1] / len_a))

        length = tvec.length * 2.5614
        if length != 0.0:
            ln = -(len_a / length)
            h1[0] = p2[0] + tvec[0] * ln
            h1[1] = p2[1] + tvec[1] * ln
            if ht == 'AUTO_CLAMPED' and prev is not None and next is not None:
                ydiff1 = prev[1] - p2[1]
                ydiff2 = next[1] - p2[1]
                if (ydiff1 <= 0.0 and ydiff2 <= 0.0) or (ydiff1 >= 0.0 and ydiff2 >= 0.0):
                    h1[1] = p2[1]
                else:
                    if ydiff1 <= 0.0:
                        if prev[1] > h1[1]:
                            h1[1] = prev[1]
                    else:
                        if prev[1] < h1[1]:
                            h1[1] = prev[1]

            ln = len_b / length
            h2[0] = p2[0] + tvec[0] * ln
            h2[1] = p2[1] + tvec[1] * ln
            if ht == 'AUTO_CLAMPED' and prev is not None and next is not None:
                ydiff1 = prev[1] - p2[1]
                ydiff2 = next[1] - p2[1]
                if (ydiff1 <= 0.0 and ydiff2 <= 0.0) or (ydiff1 >= 0.0 and ydiff2 >= 0.0):
                    h2[1] = p2[1]
                else:
                    if ydiff1 <= 0.0:
                        if next[1] < h2[1]:
                            h2[1] = next[1]
                    else:
                        if next[1] > h2[1]:
                            h2[1] = next[1]

    else: # ht == VECTOR
        h1[0] = p2[0] + dvec_a[0] * (-1.0/3.0)
        h1[1] = p2[1] + dvec_a[1] * (-1.0/3.0)
        h2[0] = p2[0] + dvec_b[0] * (1.0/3.0)
        h2[1] = p2[1] + dvec_b[1] * (1.0/3.0)


def calculate_bezier_points(points: Iterable[PoseInterpolationPoint],
                            x_range: Optional[Tuple[float, float]]=None,
                            y_range: Optional[Tuple[float, float]]=None,
                            extrapolate: Optional[bool]=True
                            ) -> Tuple[Tuple[Vector, Vector, Vector], ...]:
    data = [(
        pt.location.copy(),
        pt.handle_type,
        Vector((0.0, 0.0)),
        Vector((0.0, 0.0))
        ) for pt in points]

    if x_range:
        alpha, omega = x_range
        if alpha > omega:
            alpha, omega = omega, alpha
            for item in data:
                item[0][0] = 1.0 - item[0][0]
            data.reverse()
        delta = omega - alpha
        for item in data:
            item[0][0] = alpha + item[0][0] * delta

    if y_range:
        alpha, omega = y_range
        delta = omega - alpha
        for item in data:
            item[0][1] = alpha + item[0][1] * delta

    n = len(data) - 1
    for i, (pt, ht, h1, h2) in enumerate(data):
        calculate_bezier_handles(pt, ht, h1, h2,
                                 data[i-1][0] if i > 0 else None,
                                 data[i+1][0] if i < n else None)

    if len(data) > 2:
        ptA, htA, h1A, h2A = data[0]
        ptN, htN, h1N, h2N = data[-1]

        if htA == 'AUTO':
            hlen = (h2A - ptA).length
            hvec = data[1][2].copy()
            if hvec[0] < ptA[0]:
                hvec[0] = ptA[0]

            hvec -= ptA
            nlen = hvec.length
            if nlen > 0.00001:
                hvec *= hlen / nlen
                h2A[0] = hvec[0] + ptA[0]
                h2A[1] = hvec[1] + ptA[1]
                h1A[0] = ptA[0] - hvec[0]
                h1A[1] = ptA[1] - hvec[1]

        if htN == 'AUTO':
            hlen = (h1N - ptN).length
            hvec = data[-2][3].copy()
            if hvec[0] > ptN[0]:
                hvec[0] = ptN[0]

            hvec -= ptN
            nlen = hvec.length
            if nlen > 0.00001:
                hvec *= hlen / nlen
                h1N[0] = hvec[0] + ptN[0]
                h1N[1] = hvec[1] + ptN[1]
                h2N[0] = ptN[0] - hvec[0]
                h2N[1] = ptN[1] - hvec[1]

    if not extrapolate:
        pt = data[0]
        co = pt[0]
        hl = pt[2]
        hl[0] = 0.0
        hl[1] = co[1]

        pt = data[-1]
        co = pt[0]
        hr = pt[3]
        hr[0] = 1.0
        hr[1] = co[1]

    return tuple((item[0], item[2], item[3]) for item in data)


def input_avg_driver_update(rbfdriver: RBFDriver, index: int) -> None:
    driver = pose_data_component_driver(rbfdriver.parameters["input_pose_weights_avg"][index],
                                        ensure=True,
                                        clear_variables=True)
    variables = driver.variables
    for input_, name in enumerate(rbfdriver.inputs, ascii_letters):
        weight = input_.parameters["pose_weights"][index]
        variable = variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = name
        target = variable.targets[0]
        target.id_type = weight.id_type
        target.id = weight.id
        target.data_path = weight.value_path

    driver.type = 'SCRIPTED'
    if len(variables):
        driver.expression = f'i_*(({"+".join(variables.keys())})/{float(len(variables))})'
        
        variable = driver.variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = "i_"

        component = rbfdriver.parameters["pose_influences"][index]
        target = variable.targets[0]
        target.id_type = component.id_type
        target.id = component.id
        target.data_path = component.value_path
    else:
        driver.expression = "0.0"


def input_avg_fcurve_update(rbfdriver: RBFDriver,
                            interpolation: PoseInterpolation,
                            index: int) -> None:
    driven = rbfdriver.parameters["input_pose_weights_avg"][index]
    fcurve = pose_data_component_fcurve(driven, ensure=True)


    radius = interpolation.radius
    points = fcurve.keyframe_points
    bezier = calculate_bezier_points(interpolation.points,
                                     (0.5 - (radius * 0.5), 0.5 + (radius * 0.5)),
                                     extrapolate=interpolation.extend=='EXTRAPOLATED')
    length = len(points)
    target = len(bezier)

    while length > target:
        points.remove(points[-1])
        length -= 1

    for index, (co, hl, hr) in enumerate(bezier):
        if index < length:
            point = points[index]
        else:
            point = points.insert(co[0], co[1])
            length += 1

        point.interpolation = 'BEZIER'
        point.easing = 'AUTO'
        point.co = co
        point.handle_left_type = 'FREE'
        point.handle_right_type = 'FREE'
        point.handle_left = hl
        point.handle_right = hr


def input_sum_driver_update(rbfdriver: RBFDriver) -> None:
    driver = pose_data_component_driver(rbfdriver.parameters["input_pose_weights_sum"],
                                        ensure=True,
                                        clear_variables=True)
    driver.type = 'SUM'
    for component, name in zip(rbfdriver.parameters["input_pose_weights_avg"], ascii_letters):
        variable = driver.variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = name
        target = variable.targets[0]
        target.id_type = component.id_type
        target.id = component.id
        target.data_path = component.value_path


def pose_weight_driver_update(rbfdriver: RBFDriver, index: int) -> None:
    params = rbfdriver.parameters
    driver = pose_data_component_driver(params["pose_weights"][index],
                                        ensure=True,
                                        clear_variables=True)
    driver.type = 'SCRIPTED'
    driver.expression = "a/s"
    for component, name in ((params["input_pose_weights_avg"][index],
                             params["input_pose_weights_sum"]), "as"):
        variable = driver.variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = name
        target = variable.targets[0]
        target.id_type = component.id_type
        target.id = component.id
        target.data_path = component.value_path


@event_handler(DriverNewEvent)
def on_driver_new(event: DriverNewEvent) -> None:
    driver = event.driver
    params = driver.parameters.internal__
    for name in ("input_pose_weights_avg",
                 "input_pose_weights_sum",
                 "pose_weights",
                 "pose_influences"):
        container = params.add()
        container["name"] = name
        container["id_property_name"] = f'rbf_driver_{driver.identifier}_{name}'


@event_handler(DriverDisposableEvent)
def on_driver_disposable(event: DriverDisposableEvent) -> None:
    pose_data_group_delete(event.driver.parameters)


@event_handler(PoseNewEvent)
def on_pose_new(event: PoseNewEvent) -> None:
    driver = event.poses.driver
    params = driver.parameters
    params["input_pose_weights_avg"].internal__.add()
    params["pose_weights"].internal__.add()
    index = event.pose.index
    input_avg_driver_update(driver, index)
    input_sum_driver_update(driver)
    pose_weight_driver_update(driver, index)


@event_handler(PoseRemovedEvent)
def on_pose_removed(event: PoseRemovedEvent) -> None:
    driver = event.poses.driver
    params = driver.parameters
    for container in (params["input_pose_weights_avg"], params["pose_weights"]):
        pose_data_container_remove(container, event.index, remove_driver=True)
    input_sum_driver_update(driver)


@event_handler(PoseInterpolationUpdateEvent)
def on_pose_interpolation_update(event: PoseInterpolationUpdateEvent) -> None:
    pose = event.interpolation.pose
    input_avg_fcurve_update(pose.driver, event.interpolation, pose.index)
