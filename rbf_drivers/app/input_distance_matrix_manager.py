
from .events import event_handler
from ..api.input_variable_data_sample import InputVariableDataSampleUpdateEvent

@event_handler(InputVariableDataSampleUpdateEvent)
def on_input_variable_data_sample_update_event(event: InputVariableDataSampleUpdateEvent) -> None:
    pass