
from typing import Iterable, List, Optional, Sequence, Tuple, TYPE_CHECKING, Union
from bpy.types import PropertyGroup
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatVectorProperty,
    PointerProperty
    )
from ..app.events import dataclass, dispatch_event, Event
from .mixins import BPYPropCollectionInterface, Collection, Identifiable
if TYPE_CHECKING:
    from .poses import Pose


@dataclass
class CurvePointSettings:
    location: Tuple[float, float] = (0.0, 0.0)
    handle_type: str = 'AUTO'
    select: bool = False


@dataclass
class CurveSettings:
    points: Sequence[CurvePointSettings]
    extend: str = 'HORIZONTAL'


class CurvePointInterface:
    location: Tuple[float, float]
    handle_type: str
    select: bool


class CurveInterface:
    extend: str
    points: Sequence[CurvePointInterface]

#region

linear = CurveSettings([
    CurvePointSettings((0.0, 0.0), 'VECTOR'),
    CurvePointSettings((1.0, 1.0), 'VECTOR'),
    ])

sine_in = CurveSettings([
    CurvePointSettings((0.0, 0.0) , 'AUTO'),
    CurvePointSettings((0.1, 0.03), 'AUTO_CLAMPED'),
    CurvePointSettings((1.0, 1.0) , 'AUTO'),
    ])

sine_out = CurveSettings([
    CurvePointSettings((0.0, 0.0) , 'AUTO'),
    CurvePointSettings((0.9, 0.97), 'AUTO_CLAMPED'),
    CurvePointSettings((1.0, 1.0) , 'AUTO'),
    ])

sine_in_out = CurveSettings([
    CurvePointSettings((0.0, 0.0) , 'AUTO'),
    CurvePointSettings((0.1, 0.03), 'AUTO_CLAMPED'),
    CurvePointSettings((0.9, 0.97), 'AUTO_CLAMPED'),
    CurvePointSettings((1.0, 1.0) , 'AUTO'),
    ])

quad_in = CurveSettings([
    CurvePointSettings((0.0, 0.0)   , 'AUTO'),
    CurvePointSettings((0.15, 0.045), 'AUTO_CLAMPED'),
    CurvePointSettings((1.0, 1.0)   , 'AUTO'),
    ])

quad_out = CurveSettings([
    CurvePointSettings((0.0, 0.0)   , 'AUTO'),
    CurvePointSettings((0.85, 0.955), 'AUTO_CLAMPED'),
    CurvePointSettings((1.0, 1.0)   , 'AUTO'),
    ])

quad_in_out = CurveSettings([
    CurvePointSettings((0.0, 0.0)   , 'AUTO'),
    CurvePointSettings((0.15, 0.045), 'AUTO_CLAMPED'),
    CurvePointSettings((0.85, 0.955), 'AUTO_CLAMPED'),
    CurvePointSettings((1.0, 1.0)   , 'AUTO'),
    ])

cubic_in = CurveSettings([
    CurvePointSettings((0.0, 0.0) , 'AUTO'),
    CurvePointSettings((0.2, 0.03), 'AUTO_CLAMPED'),
    CurvePointSettings((1.0, 1.0) , 'AUTO'),
    ])

cubic_out = CurveSettings([
    CurvePointSettings((0.0, 0.0) , 'AUTO'),
    CurvePointSettings((0.8, 0.97), 'AUTO_CLAMPED'),
    CurvePointSettings((1.0, 1.0) , 'AUTO'),
    ])

cubic_in_out = CurveSettings([
    CurvePointSettings((0.0, 0.0) , 'AUTO'),
    CurvePointSettings((0.2, 0.03), 'AUTO_CLAMPED'),
    CurvePointSettings((0.8, 0.97), 'AUTO_CLAMPED'),
    CurvePointSettings((1.0, 1.0) , 'AUTO'),
    ])

quart_in = CurveSettings([
    CurvePointSettings((0.0, 0.0)  , 'AUTO'),
    CurvePointSettings((0.25, 0.03), 'AUTO_CLAMPED'),
    CurvePointSettings((1.0, 1.0)  , 'AUTO'),
    ])

quart_out = CurveSettings([
    CurvePointSettings((0.0, 0.0)  , 'AUTO'),
    CurvePointSettings((0.75, 0.97), 'AUTO_CLAMPED'),
    CurvePointSettings((1.0, 1.0)  , 'AUTO'),
    ])

quart_in_out = CurveSettings([
    CurvePointSettings((0.0, 0.0)  , 'AUTO'),
    CurvePointSettings((0.25, 0.03), 'AUTO_CLAMPED'),
    CurvePointSettings((0.75, 0.97), 'AUTO_CLAMPED'),
    CurvePointSettings((1.0, 1.0)  , 'AUTO'),
    ])

quint_in = CurveSettings([
    CurvePointSettings((0.0, 0.0)    , 'AUTO'),
    CurvePointSettings((0.275, 0.025), 'AUTO_CLAMPED'),
    CurvePointSettings((1.0, 1.0)    , 'AUTO'),
    ])

quint_out = CurveSettings([
    CurvePointSettings((0.0, 0.0)    , 'AUTO'),
    CurvePointSettings((0.725, 0.975), 'AUTO_CLAMPED'),
    CurvePointSettings((1.0, 1.0)    , 'AUTO'),
    ])

quint_in_out = CurveSettings([
    CurvePointSettings((0.0, 0.0)    , 'AUTO'),
    CurvePointSettings((0.275, 0.025), 'AUTO_CLAMPED'),
    CurvePointSettings((0.725, 0.975), 'AUTO_CLAMPED'),
    CurvePointSettings((1.0, 1.0)    , 'AUTO'),
    ])

POSE_INTERPOLATION_PRESETS = {
    'LINEAR': {
        'EASE_IN'    : linear,
        'EASE_OUT'   : linear,
        'EASE_IN_OUT': linear,
        },
    'SINE': {
        'EASE_IN'    : sine_in,
        'EASE_OUT'   : sine_out,
        'EASE_IN_OUT': sine_in_out,
        },
    'QUAD': {
        'EASE_IN'    : quad_in,
        'EASE_OUT'   : quad_out,
        'EASE_IN_OUT': quad_in_out,
        },
    'CUBIC': {
        'EASE_IN'    : cubic_in,
        'EASE_OUT'   : cubic_out,
        'EASE_IN_OUT': cubic_in_out,
        },
    'QUART': {
        'EASE_IN'    : quart_in,
        'EASE_OUT'   : quart_out,
        'EASE_IN_OUT': quart_in_out,
        },
    'QUINT': {
        'EASE_IN'    : quint_in,
        'EASE_OUT'   : quint_out,
        'EASE_IN_OUT': quint_in_out,
        },
    }

#endregion

#region PoseInterpolationPoint
#--------------------------------------------------------------------------------------------------

# TODO add icons
POSE_INTERPOLATION_POINT_HANDLE_TYPE_ITEMS = [
    ('AUTO'        , "Auto Handle"        , "", 'NONE', 0),
    ('AUTO_CLAMPED', "Auto Clamped Handle", "", 'NONE', 1),
    ('VECTOR'      , "Vector Handle"      , "", 'NONE', 2),
    ]

POSE_INTERPOLATION_POINT_HANDLE_TYPE_TABLE = {
    _item[0]: _item[4] for _item in POSE_INTERPOLATION_POINT_HANDLE_TYPE_ITEMS
    }


def pose_interpolation_point_handle_type_update_handler(point: 'PoseInterpolationPoint', _) -> None:
    dispatch_event(PoseInterpolationUpdateEvent(point.pose.interpolation))


def pose_interpolation_point_location_update_handler(point: 'PoseInterpolationPoint', _) -> None:
    point.pose.interpolation.update()


class PoseInterpolationPoint(PropertyGroup):

    handle_type: EnumProperty(
        name="Handle Type",
        description="Interpolation at this point: Bezier or vector",
        items=POSE_INTERPOLATION_POINT_HANDLE_TYPE_ITEMS,
        default='AUTO_CLAMPED',
        update=pose_interpolation_point_handle_type_update_handler,
        options=set(),
        )

    location: FloatVectorProperty(
        name="Location",
        description="X/Y coordinates of the pose interapolation point",
        size=2,
        subtype='XYZ',
        default=(0.0, 0.0),
        update=pose_interpolation_point_location_update_handler,
        options=set(),
        )

    @property
    def pose(self) -> 'Pose':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".interpolation")[0])

    select: BoolProperty(
        name="Select",
        description="Selection state of the pose interpolation point",
        default=False,
        options=set(),
        )

    def __init__(self, point: CurvePointInterface) -> None:
        self["handle_type"] = POSE_INTERPOLATION_POINT_HANDLE_TYPE_TABLE[point.handle_type]
        self["location"] = point.location
        self["select"] = point.select


#endregion

#region PoseInterpolationPoints
#--------------------------------------------------------------------------------------------------


def pose_interpolation_points_update_handler(points: 'PoseInterpolationPoints', _) -> None:
    points.pose.interpolation.update()


class PoseInterpolationPoints(Collection[PoseInterpolationPoint], PropertyGroup):
    """Collection of pose interplation points"""

    internal__: CollectionProperty(
        type=PoseInterpolationPoint,
        options={'HIDDEN'}
        )

    @property
    def pose(self) -> 'Pose':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".interpolation")[0])

    def __init__(self, data: Iterable[CurvePointInterface]) -> None:
        points: BPYPropCollectionInterface[PoseInterpolationPoint] = self.internal__
        points.clear()
        for item in data:
            points.add().__init__(item)

    def new(self, position: float, value: float) -> PoseInterpolationPoint:
        """Add a point"""

        if not isinstance(position, float):
            raise TypeError((f'{self.__class__.__name__}.new(position, value): '
                             f'Expected position to be a float, '
                             f'not {position.__class__.__name__}'))

        if not isinstance(value, float):
            raise TypeError((f'{self.__class__.__name__}.new(position, value): '
                             f'Expected value to be a float, '
                             f'not {value.__class__.__name__}'))

        for point in self:
            if point.location[0] == position and point.location[1] == value:
                return point

        point = self.internal__.add()
        point.__init__((position, value))

        interpolation = self.pose.interpolation
        if interpolation.type != 'CUSTOM':
            interpolation["type"] = POSE_INTERPOLATION_TYPE_TABLE['CUSTOM']
        interpolation.update()

        if point.location[0] != position or point.location[1] != value:
            for point in self:
                if point.location[0] == position and point.location[1] == value:
                    break

        return point

    def remove(self, point: PoseInterpolationPoint) -> None:
        """Remove a point"""

        if not isinstance(point, PoseInterpolationPoint):
            raise TypeError((f'{self.__class__.__name__}'
                             f'.remove(point): expected point to be '
                             f'{PoseInterpolationPoint.__name__}, not {point.__class__.__name__}'))

        index = next((i for i, p in enumerate(self) if p == point), -1)

        if index == -1:
            raise ValueError((f'{self.__class__.__name__}'
                              f'.remove(point): point not found'))

        if index == 0:
            raise ValueError(f'{self.__class__.__name__}'
                             f'.remove(point): Cannot remove first point')

        if index == len(self) - 1:
            raise ValueError(f'{self.__class__.__name__}'
                             f'.remove(point): Cannot remove last point')

        interpolation = self.pose.interpolation
        if interpolation.type != 'CUSTOM':
            interpolation["type"] = POSE_INTERPOLATION_TYPE_TABLE['CUSTOM']

        self.internal__.remove(index)
        interpolation.update()

#endregion

# TODO icons
POSE_INTERPOLATION_EXTEND_ITEMS = [
    ('HORIZONTAL'  , "Horizontal"  , "", 'NONE', 0),
    ('EXTRAPOLATED', "Extrapolated", "", 'NONE', 1),
    ]

POSE_INTERPOLATION_EXTEND_TABLE = {
    _item[0]: _item[4] for _item in POSE_INTERPOLATION_EXTEND_ITEMS
    }

POSE_INTERPOLATION_EASING_ITEMS = [
    ('EASE_IN'    , "In"      , "Ease in"        , 'IPO_EASE_IN'    , 0),
    ('EASE_OUT'   , "Out"     , "Ease out"       , 'IPO_EASE_OUT'   , 1),
    ('EASE_IN_OUT', "In & Out", "Ease in and out", 'IPO_EASE_IN_OUT', 2),
    ]

POSE_INTERPOLATION_EASING_TABLE = {
    _item[0]: _item[4] for _item in POSE_INTERPOLATION_EASING_ITEMS
    }

POSE_INTERPOLATION_TYPE_ITEMS = [
    ('LINEAR', "Linear"      , "Linear"          , 'IPO_LINEAR', 0),
    ('SINE'  , "Sinusoidal"  , "Sinusoidal"      , 'IPO_SINE'  , 1),
    ('QUAD'  , "Quadratic"   , "Quadratic"       , 'IPO_QUAD'  , 2),
    ('CUBIC' , "Cubic"       , "Cubic"           , 'IPO_CUBIC' , 3),
    ('QUART' , "Quartic"     , "Quartic"         , 'IPO_QUART' , 4),
    ('QUINT' , "Quintic"     , "Quintic"         , 'IPO_QUINT' , 5),
    None,
    ('CUSTOM', "Custom Curve", "Use custom curve", 'FCURVE'    , 6),
    ]

POSE_INTERPOLATION_TYPE_TABLE = {
    _item[0]: _item[4] for _item in POSE_INTERPOLATION_TYPE_ITEMS
    }


@dataclass(frozen=True)
class PoseInterpolationUpdateEvent(Event):
    interpolation: 'PoseInterpolation'


def pose_interpolation_type_update_handler(interpolation: 'PoseInterpolation', _) -> None:
    type = interpolation.type
    if type != 'CUSTOM':
        preset: CurveSettings = POSE_INTERPOLATION_PRESETS[interpolation.type][interpolation.easing]
        interpolation.__init__(points=preset.points)
    dispatch_event(PoseInterpolationUpdateEvent(interpolation))


def pose_interpolation_easing_update_handler(interpolation: 'PoseInterpolation', _) -> None:
    type = interpolation.type
    if type != 'CUSTOM':
        preset: CurveSettings = POSE_INTERPOLATION_PRESETS[interpolation.type][interpolation.easing]
        interpolation.__init__(points=preset.points)
    dispatch_event(PoseInterpolationUpdateEvent(interpolation))


def pose_interpolation_extend_update_handler(interpolation: 'PoseInterpolation', _) -> None:
    dispatch_event(PoseInterpolationUpdateEvent(interpolation))


def pose_interpolation_sync__internal__(interpolation: 'PoseInterpolation') -> bool:
    return interpolation.get("sync__internal__", False)


class PoseInterpolation(Identifiable, PropertyGroup):

    sync__internal__: BoolProperty(
        get=pose_interpolation_sync__internal__,
        options={'HIDDEN'}
        )

    easing: EnumProperty(
        name="Easing",
        items=POSE_INTERPOLATION_EASING_ITEMS,
        default='EASE_IN_OUT',
        options=set(),
        update=pose_interpolation_easing_update_handler
        )

    extend: EnumProperty(
        name="Extend",
        description="Extrapolate the curve or extend it horizontally",
        items=POSE_INTERPOLATION_EXTEND_ITEMS,
        default='HORIZONTAL',
        update=pose_interpolation_extend_update_handler,
        options=set(),
        )

    type: EnumProperty(
        name="Type",
        items=POSE_INTERPOLATION_TYPE_ITEMS,
        default='LINEAR',
        options=set(),
        update=pose_interpolation_type_update_handler,
        )

    points: PointerProperty(
        name="Points",
        description="",
        type=PoseInterpolationPoints,
        options=set()
        )

    @property
    def pose(self) -> 'Pose':
        path: str = self.path_from_id()
        return self.id_data.path_resolve(path.rpartition(".interpolation")[0])

    def __init__(self,
                 points: Optional[Sequence[CurvePointInterface]]=None,
                 extend: Optional[str]=None) -> None:
        self.points.__init__(points or linear.points)
        if extend is not None:
            self["extend"] = POSE_INTERPOLATION_EXTEND_TABLE[extend]

    def update(self) -> None:
        points = list(self.points)
        sorted_points = sorted(points, key=lambda point: point.location[0])

        if points != sorted_points:
            data = [
                CurvePointSettings(
                    location=tuple(point.location),
                    handle_type=point.handle_type,
                    select=point.select
                    ) for point in sorted_points]
            for point, item in zip(points, data):
                point.__init__(item)
        
        dispatch_event(PoseInterpolationUpdateEvent(self))
