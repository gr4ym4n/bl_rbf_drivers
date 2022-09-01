
from typing import TYPE_CHECKING
from .events import event_handler
from .utils import owner_resolve
from ..api.output import OUTPUT_ROTATION_MODE_TABLE
from ..api.outputs import OutputNewEvent
if TYPE_CHECKING:
    from ..api.output import Output


def output_init__location(output: 'Output', pose_count: int) -> None:
    for index, axis in enumerate("XYZ"):
        channel = output.channels.internal__.add()
        channel["name"] = axis
        channel["array_index"] = index
        channel["data_path"] = "location"
        channel["default_value"] = 0.0
        channel.data.__init__([0.0] * pose_count)


def output_init__rotation(output: 'Output', pose_count: int) -> None:
    output["rotation_mode"] = OUTPUT_ROTATION_MODE_TABLE['EULER']
    for index, axis in enumerate("WXYZ"):
        channel = output.channels.internal__.add()
        channel["name"] = axis
        if index > 0:
            channel["array_index"] = index - 1
        channel["data_path"] = "rotation_euler"
        channel["default_value"] = 0.0
        channel["is_enabled"] = False
        channel.data.__init__([channel.default_value] * pose_count)


def output_init__scale(output: 'Output', pose_count: int) -> None:
    for index, axis in enumerate("XYZ"):
        channel = output.channels.internal__.add()
        channel["name"] = axis
        channel["array_index"] = index
        channel["data_path"] = "scale"
        channel["default_value"] = 1.0
        channel.data.__init__([1.0] * pose_count)


def output_init__shape_key(output: 'Output', pose_count: int) -> None:
    channel = output.channels.internal__.add()
    channel["name"] = ""
    channel["data_path"] = 'key_blocks[""].value'
    channel["default_value"] = 0.0
    channel["is_enabled"] = True
    channel.data.__init__([0.0] * pose_count)


def output_init__single_prop(output: 'Output', pose_count: int) -> None:
    channel = output.channels.internal__.add()
    channel["name"] = ""
    channel["data_path"] = ""
    channel["default_value"] = 0.0
    channel["is_enabled"] = True
    channel.data.__init__([0.0] * pose_count)


OUTPUT_INIT_FUNCS = {
    'LOCATION'   : output_init__location,
    'ROTATION'   : output_init__rotation,
    'SCALE'      : output_init__scale,
    'SHAPE_KEY'  : output_init__shape_key,
    'SINGLE_PROP': output_init__single_prop,
    }


@event_handler(OutputNewEvent)
def on_output_new(event: OutputNewEvent) -> None:
    output = event.output
    OUTPUT_INIT_FUNCS[output.type](output, len(owner_resolve(output, ".outputs").poses))
