
from typing import TYPE_CHECKING, Callable, Dict, Optional, Sequence, Tuple, Union
from functools import partial
from bpy.types import NodeTree, PropertyGroup
from bpy.props import BoolProperty, EnumProperty, PointerProperty, StringProperty
from rbf_drivers.api.pose_data import POSE_DATA_CONTAINER_TYPE_SIZES
from .mixins import Symmetrical
from .pose_data_ import PoseDataFrame
from .input import InputRotationAxisUpdateEvent, InputRotationModeUpdateEvent
from .inputs import Inputs
from .poses import PoseNewEvent, Poses
from .outputs import RBFDriverOutputs
from ..app.events import dataclass, dispatch_event, event_handler, Event
from ..app.utils import (
    euler_to_quaternion,
    euler_to_swing_twist_x,
    euler_to_swing_twist_y,
    euler_to_swing_twist_z,
    quaternion_to_axis_angle,
    quaternion_to_euler,
    quaternion_to_swing_twist_x,
    quaternion_to_swing_twist_y,
    quaternion_to_swing_twist_z,
    swing_twist_x_to_euler,
    swing_twist_y_to_euler,
    swing_twist_z_to_euler,
    swing_twist_x_to_quaternion,
    swing_twist_y_to_quaternion,
    swing_twist_z_to_quaternion,
    swing_twist_x_to_swing_twist_y,
    swing_twist_x_to_swing_twist_z,
    swing_twist_y_to_swing_twist_x,
    swing_twist_y_to_swing_twist_z,
    swing_twist_z_to_swing_twist_x,
    swing_twist_z_to_swing_twist_y,
    transform_matrix,
    transform_target,
    )
if TYPE_CHECKING:
    from bpy.types import Context

ROTATION_CONVERSION_LUT: Dict[str, Dict[str, Optional[Callable]]] = {
    'EULER': {
        'EULER'     : None,
        'SWING'     : euler_to_quaternion,
        'TWIST_X'   : partial(euler_to_swing_twist_x, quaternion=True),
        'TWIST_Y'   : partial(euler_to_swing_twist_y, quaternion=True),
        'TWIST_Z'   : partial(euler_to_swing_twist_z, quaternion=True),
        'QUATERNION': euler_to_quaternion,
        },
    'SWING': {
        'EULER'     : quaternion_to_euler,
        'SWING'     : None,
        'TWIST_X'   : partial(quaternion_to_swing_twist_x, quaternion=True),
        'TWIST_Y'   : partial(quaternion_to_swing_twist_y, quaternion=True),
        'TWIST_Z'   : partial(quaternion_to_swing_twist_z, quaternion=True),
        'QUATERNION': None,
        },
    'TWIST_X': {
        'EULER'     : swing_twist_x_to_euler,
        'SWING'     : swing_twist_x_to_quaternion,
        'TWIST_X'   : None,
        'TWIST_Y'   : swing_twist_x_to_swing_twist_y,
        'TWIST_Z'   : swing_twist_x_to_swing_twist_z,
        'QUATERNION': swing_twist_x_to_quaternion,
        },
    'TWIST_Y': {
        'EULER'     : swing_twist_y_to_euler,
        'SWING'     : swing_twist_y_to_quaternion,
        'TWIST_X'   : swing_twist_y_to_swing_twist_x,
        'TWIST_Y'   : None,
        'TWIST_Z'   : swing_twist_y_to_swing_twist_z,
        'QUATERNION': swing_twist_y_to_quaternion,
        },
    'TWIST_Z': {
        'EULER'     : swing_twist_z_to_euler,
        'SWING'     : swing_twist_z_to_quaternion,
        'TWIST_X'   : swing_twist_z_to_swing_twist_x,
        'TWIST_Y'   : swing_twist_z_to_swing_twist_y,
        'TWIST_Z'   : None,
        'QUATERNION': swing_twist_z_to_quaternion,
        },
    'QUATERNION': {
        'EULER'     : quaternion_to_euler,
        'SWING'     : None,
        'TWIST_X'   : partial(quaternion_to_swing_twist_x, quaternion=True),
        'TWIST_Y'   : partial(quaternion_to_swing_twist_y, quaternion=True),
        'TWIST_Z'   : partial(quaternion_to_swing_twist_z, quaternion=True),
        'QUATERNION': None,
        }
    }

DRIVER_TYPE_ITEMS = [
    ('NONE'      , "Generic"   , "", 'DRIVER'       , 0),
    ('SHAPE_KEY' , "Shape Keys", "", 'SHAPEKEY_DATA', 1),
    ]

DRIVER_TYPE_INDEX = [
    item[0] for item in DRIVER_TYPE_ITEMS
    ]

DRIVER_TYPE_TABLE = {
    item[0]: item[4] for item in DRIVER_TYPE_ITEMS
    }

DRIVER_TYPE_ICONS = {
    item[0]: item[3] for item in DRIVER_TYPE_ITEMS
    }


@dataclass(frozen=True)
class DriverNameUpdateEvent(Event):
    driver: 'RBFDriver'
    value: str


def driver_name_update_handler(driver: 'RBFDriver', _: 'Context') -> None:
    dispatch_event(DriverNameUpdateEvent(driver, driver.name))


def driver_symmetry_lock(driver: 'RBFDriver') -> bool:
    return driver.get("symmetry_lock", False)


def driver_type(driver: 'RBFDriver') -> int:
    return driver.get("type", 0)


class RBFDriver(Symmetrical, PropertyGroup):
    '''Radial basis function driver'''

    nodetree_internal__: PointerProperty(
        type=NodeTree,
        options={'HIDDEN'}
        )

    data_frame: PointerProperty(
        name="Data",
        description="",
        type=PoseDataFrame,
        options=set()
        )

    @property
    def icon(self) -> str:
        """The RBF driver icon (read-only)"""
        return DRIVER_TYPE_ICONS[self.type]

    inputs: PointerProperty(
        name="Inputs",
        description="Collection of RBF driver inputs",
        type=Inputs,
        options=set()
        )

    outputs: PointerProperty(
        name="Outputs",
        description="Collection of RBF driver outputs",
        type=RBFDriverOutputs,
        options=set()
        )

    name: StringProperty(
        name="Name",
        description="Unique RBF driver name",
        options=set(),
        update=driver_name_update_handler,
        )

    poses: PointerProperty(
        name="Poses",
        description="Collection of RBF driver poses",
        type=Poses,
        options=set()
        )

    symmetry_lock: BoolProperty(
        name="Symmetry Lock",
        description="Prevents symmetry property changes from infinite regression (internal-use)",
        get=driver_symmetry_lock,
        options={'HIDDEN'}
        )

    type: EnumProperty(
        name="Type",
        description="The RBF driver type (read-only)",
        items=DRIVER_TYPE_ITEMS,
        get=driver_type,
        options=set()
        )

    def __init__(self, type: str, name: Optional[str]="", mirror: Optional['RBFDriver']=None) -> None:
        assert mirror is None or (isinstance(mirror, RBFDriver)
                                  and mirror.id_data == self.id_data
                                  and mirror != self)

        self["type"] = DRIVER_TYPE_TABLE[type]
        if name:
            self.name = name

        if mirror:
            self["symmetry_identifier"] = mirror.identifier
            mirror["symmetry_identifier"] = self.identifier

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(type="{self.type}", name="{self.name}")'

    def __str__(self) -> str:
        path: str = self.path_from_id()
        path = path.replace(".internal__", "")
        return f'{self.__class__.__name__} @ bpy.data.objects["{self.id_data.name}"].{path}'


def input_target(input_: 'Input') -> Optional[Union['ID', 'PoseBone']]:
    target = input_.object
    if target:
        if (input_.type in {'LOCATION', 'ROTATION', 'SCALE'}
                and target.type == 'ARMATURE'
                and input_.bone_target):
            target = target.pose.bones.get(input_.bone_target)
        elif input_.id_type != 'OBJECT':
            target = target.data if target.type == input_.id_type else target.data
    return 


def read_input(input_: 'Input') -> Tuple[str, Optional[Union[float, Sequence[float]]]]:
    type_ = input_.type
    dtype = 'FLOAT'
    value = None
    if type_ in {'LOCATION', 'ROTATION', 'SCALE'}:
        if type_ == 'LOCATION':
            dtype = 'TRANSLATION'
        elif type_ == 'ROTATION':
            pass
        else:
            dtype == 'QUATERNION'
        target = transform_target(input_, input_.bone_target)
        if target:
            matrix = transform_matrix(target, input_.transform_space)
            if type_ == 'LOCATION':
                dtype = 'TRANSLATION'
                value = matrix.to_translation()
            elif type_ == 'SCALE':
                dtype = type_
                value = matrix.to_scale()
            else:
                rmode = input_.rotation_mode
                dtype = 'QUATERNION'
                value = matrix.to_quaternion()
                if rmode == 'EULER':
                    dtype = rmode
                    value = value.to_euler(input_.rotation_order)
                elif rmode == 'AXIS_ANGLE':
                    dtype = rmode
                    value = value.to_axis_angle()

    return dtype, value



@event_handler(PoseNewEvent)
def on_pose_new(event: PoseNewEvent) -> None:
    pose = event.pose
    driver = pose.driver
    for input_ in driver.inputs:
        pose.inputs.internal__.add().__init__(*read_input(input_))
    for output in driver.outputs:
        pose.outputs.internal__.add().__init__(*read_output(output))


@event_handler(InputRotationModeUpdateEvent)
def on_input_rotation_mode_update(event: InputRotationModeUpdateEvent) -> None:
    input_ = event.input
    if input_.type == 'ROTATION':
        prevmode = event.previous_value
        currmode = event.value
        if prevmode == 'TWIST': prevmode = f'TWIST_{input_.rotation_axis}'
        if currmode == 'TWIST': currmode = f'TWIST_{input_.rotation_axis}'
        prevtype = prevmode
        currtype = currmode
        if prevtype in {'SWING', 'TWIST'}: prevtype = f'SWING_TWIST_{input_.rotation_axis}'
        if currtype in {'SWING', 'TWIST'}: currtype = f'SWING_TWIST_{input_.rotation_axis}'
        convert = ROTATION_CONVERSION_LUT[prevmode][currmode]
        if convert:
            size = POSE_DATA_CONTAINER_TYPE_SIZES[prevtype]
            for pose in event.input.driver.poses:
                data = pose.inputs.get(event.input)
                if data and len(data) == size:
                    data.__init__(currtype, convert(tuple(data)))


@event_handler(InputRotationAxisUpdateEvent)
def on_input_rotation_axis_update(event: InputRotationAxisUpdateEvent) -> None:
    input_ = event.input
    if input_.type == 'ROTATION':
        mode = input_.rotation_mode
        if mode in {'SWING', 'TWIST'}:
            prev = f'{mode}_{event.previous_value}'
            curr = f'{mode}_{event.value}'
            convert = ROTATION_CONVERSION_LUT[prev][curr]
            if convert:
                type_ = f'SWING_TWIST_{event.value}'
                for pose in input_.driver.poses:
                    data = pose.inputs.get(input_)
                    if data and len(data) == 4:
                        data.__init__(type_, convert(tuple(data)))