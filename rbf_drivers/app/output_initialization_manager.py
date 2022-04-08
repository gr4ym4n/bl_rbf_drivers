
from typing import Callable, TYPE_CHECKING

from rbf_drivers.app.utils import owner_resolve
from .events import event_handler
from ..api.outputs import OutputNewEvent
if TYPE_CHECKING:
    from ..api.output_channel_data import RBFDriverOutputChannelData
    from ..api.output import RBFDriverOutput


def output_channels_init__location(output: 'RBFDriverOutput', pose_count: int) -> None:
    '''
    Initializes a location output
    '''
    for index, axis in enumerate("XYZ"):
        channel = output.channels.collection__internal__.add()
        channel["name"] = axis
        channel["array_index"] = index
        channel["data_path"] = "location"
        channel["default_value"] = 0.0
        channel.data.__init__([0.0] * pose_count)


def output_channels_init__rotation(output: 'RBFDriverOutput', pose_count: int) -> None:
    '''
    Initializes a rotation output
    '''
    for index, axis in enumerate("WXYZ"):
        channel = output.channels.collection__internal__.add()
        channel["name"] = axis
        channel["array_index"] = index
        channel["data_path"] = "rotation_quaternion"
        channel["default_value"] = float(index == 0)
        channel.data.__init__([channel.default_value] * pose_count)


def output_channels_init__scale(output: 'RBFDriverOutput', pose_count: int) -> None:
    '''
    Initializes a scale output
    '''
    for index, axis in enumerate("XYZ"):
        channel = output.channels.collection__internal__.add()
        channel["name"] = axis
        channel["array_index"] = index
        channel["data_path"] = "scale"
        channel["default_value"] = 1.0
        channel.data.__init__([1.0] * pose_count)


def output_channels_init__bbone(output: 'RBFDriverOutput', pose_count: int) -> None:
    '''
    Initializes a bbone output
    '''
    for name, path, value, index in [
            ("curveinx" , "bbone_curveinx" , 0.0, None),
            ("curveinz" , "bbone_curveinz" , 0.0, None),
            ("curveoutx", "bbone_curveoutx", 0.0, None),
            ("curveoutz", "bbone_curveoutz", 0.0, None),
            ("easein"   , "bbone_easein"   , 0.0, None),
            ("easeout"  , "bbone_easeout"  , 0.0, None),
            ("rollin"   , "bbone_rollin"   , 0.0, None),
            ("rollout"  , "bbone_rollout"  , 0.0, None),
            ("scaleinx" , "bbone_scalein"  , 1.0, 0),
            ("scaleiny" , "bbone_scalein"  , 1.0, 1),
            ("scaleinz" , "bbone_scalein"  , 1.0, 2),
            ("scaleoutx", "bbone_scaleout" , 1.0, 0),
            ("scaleouty", "bbone_scaleout" , 1.0, 1),
            ("scaleoutz", "bbone_scaleout" , 1.0, 2),
        ]:
        channel = output.channels.collection__internal__.add()
        channel["name"] = name
        if index is not None:
            channel["array_index"] = index
        channel["data_path"] = f'pose.bones[""].bbone_{path}'
        channel["default_value"] = value
        channel.data.__init__([value] * pose_count)


def output_channels_init__shape_key(output: 'RBFDriverOutput', pose_count: int) -> None:
    '''
    Initializes a shape key output
    '''
    channel = output.channels.collection__internal__.add()
    channel["name"] = ""
    channel["data_path"] = 'key_blocks[""].value'
    channel["default_value"] = 0.0
    channel.data.__init__([0.0] * pose_count)


def output_channels_init__generic(output: 'RBFDriverOutput', pose_count: int) -> None:
    '''
    Initializes a generic output
    '''
    channel = output.channels.collection__internal__.add()
    channel["name"] = ""
    channel["data_path"] = ""
    channel["default_value"] = 0.0
    channel.data.__init__([0.0] * pose_count)


@event_handler(OutputNewEvent)
def on_output_new(event: OutputNewEvent) -> None:
    '''
    Initializes output channel data for each pose
    '''
    type: str = event.output.type
    init: Callable[['RBFDriverOutput', int], None]
    
    if   type == 'LOCATION'  : init = output_channels_init__location
    elif type == 'ROTATION'  : init = output_channels_init__rotation
    elif type == 'SCALE'     : init = output_channels_init__scale
    elif type == 'BBONE'     : init = output_channels_init__bbone
    elif type == 'SHAPE_KEY' : init = output_channels_init__shape_key
    else                     : init = output_channels_init__generic

    init(event.output, len(owner_resolve(event.output, ".outputs").poses))