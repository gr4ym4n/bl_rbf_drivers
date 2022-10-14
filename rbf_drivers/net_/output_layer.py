
from typing import TYPE_CHECKING
from numpy import finfo
from ..app.utils import driver_ensure, idprop_driver_ensure, idprop_remove
if TYPE_CHECKING:
    from ..api.outputs import Output


def output_magnitude_update(output: Output) -> None:
    fcurve = idprop_driver_ensure(output.magnitude, clear_variables=True)
    driver = fcurve.driver
    logsum = output.logarithmic_sum

    for axis, index in zip("xyz", range(1, 5)):
        variable = driver.variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = axis

        target = variable.targets[0]
        target.id_type = logsum.id_type
        target.id = logsum.id
        target.data_path = f'{logsum.data_path}[{index}]'

    driver.type = 'SCRIPTED'
    driver.expression = f'sqrt({"+".join("pow(" + v.name + ",2.0)" for v in driver.variables)})'


def output_magnitude_remove(output: 'Output') -> None:
    idprop_remove(output.magnitude, remove_drivers=True)


def output_sine_update(output: 'Output') -> None:
    fcurve = idprop_driver_ensure(output.sine, clear_variables=True)
    driver = fcurve.driver
    length = output.magnitude

    variable = driver.variables.new()
    variable.type = 'SINGLE_PROP'
    variable.name = "magnitude"

    target = variable.targets[0]
    target.id_type = length.id_type
    target.id = length.id
    target.data_path = length.data_path

    driver.type = 'SCRIPTED'
    driver.expression = f'sin(magnitude) / magnitude if magnitude != 0.0 else sin(magnitude)'


def output_sine_remove(output: 'Output') -> None:
    idprop_remove(output.sine, remove_drivers=True)


def output_exponent_update(output: 'Output') -> None:
    fcurve = idprop_driver_ensure(output.exponent, clear_variables=True)
    driver = fcurve.driver
    logsum = output.logarithmic_sum

    variable = driver.variables.new()
    variable.type = 'SINGLE_PROP'
    variable.name = "w"

    target = variable.targets[0]
    target.id_type = logsum.id_type
    target.id = logsum.id
    target.data_path = f'{logsum.data_path}[0]'

    driver.type = 'SCRIPTED'
    driver.expression = 'exp(w)'


def output_exponent_remove(output: 'Output') -> None:
    idprop_remove(output.exponent, remove_drivers=True)


def output_exponential_map_update(output: 'Output') -> None:
    for index in len(output.exponential_map):
        fcurve = idprop_driver_ensure(output.exponential_map, index=index, clear_drivers=True)
        driver = fcurve.driver
        driver.type = 'SCRIPTED'

        variable = driver.variables.new()
        variable.type = 'SINGLE_PROP'
        variable.name = "e"

        idprop = output.exponent
        target = variable.targets[0]
        target.id_type = idprop.id_type
        target.id = idprop.id
        target.data_path = idprop.data_path

        if index == 0:
            variable = driver.variables.new()
            variable.type = 'SINGLE_PROP'
            variable.name = "x"

            idprop = output.magnitude
            target = variable.targets[0]
            target.id_type = idprop.id_type
            target.id = idprop.id
            target.data_path = idprop.data_path

            driver.expression = f'e*cos(x) if x>{10 * finfo(float).resolution} else e'
        else:
            variable = driver.variables.new()
            variable.type = 'SINGLE_PROP'
            variable.name = "s"

            idprop = output.exponent
            target = variable.targets[0]
            target.id_type = idprop.id_type
            target.id = idprop.id
            target.data_path = idprop.data_path

            variable = driver.variables.new()
            variable.type = 'SINGLE_PROP'
            variable.name = "x"

            idprop = output.logarithmic_sum
            target = variable.targets[0]
            target.id_type = idprop.id_type
            target.id = idprop.id
            target.data_path = f'{idprop.data_path}[{index}]'

            driver.expression = f'e*s*x'


def output_exponential_map_remove(output: 'Output') -> None:
    idprop_remove(output.exponential_map, remove_drivers=True)


def output_quaternion_blend(output: 'Output') -> None:
    for channel in output.channels:
        fcurve = driver_ensure(channel.id, channel.data_path, channel.array_index)
        