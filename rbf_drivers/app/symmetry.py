

import re
from typing import Any, Match, Optional
from logging import getLogger
from .events import event_handler
from ..api.input_target import RBFDriverInputTarget
from ..api.input_variable import RBFDriverInputVariable
from ..api.input import RBFDriverInput
from ..lib.symmetry import symmetrical_target

log = getLogger("rbf_drivers")

def input_symmetry_target(input: RBFDriverInput) -> Optional[RBFDriverInput]:

    driver = input.rbf_driver
    if not driver.has_symmetry_target:
        log.warning(f'Symmetry target defined for component {input} but not for {driver}')
        return

    m_driver = driver.id_data.rbf_drivers.search(driver.symmetry_identifier)
    if m_driver is None:
        log.warning(f'Search failed for symmetry target of {driver}.')
        return

    return m_driver.inputs.search(input.symmetry_identifier)


def input_variable_symmetry_target(variable: RBFDriverInputVariable) -> Optional[RBFDriverInputVariable]:

    input = variable.input
    if not input.has_symmetry_target:
        log.warning((f'Symmetry target defined for sub-component {variable} but not for '
                     f'parent component {input}'))
        return

    m_input = input_symmetry_target(input)
    if m_input is None:
        log.warning(f'Search failed for symmetry target of {input}.')
        return

    return m_input.variables.search(variable.symmetry_identifier)


def input_target_symmetry_target(target: RBFDriverInputTarget) -> Optional[RBFDriverInputTarget]:

    variable = target.variable
    if not variable.has_symmetry_target:
        log.warning((f'Symmetry target defined for sub-component {target} but not for '
                     f'parent component {variable}'))
        return

    m_variable = input_variable_symmetry_target(variable)
    if m_variable is None:
        log.warning(f'Search failed for symmetry target of {variable}')
        return

    return m_variable.targets.search(target.symmetry_identifier)


def input_target_mirror_property(target: RBFDriverInputTarget, name: str, value: Any) -> None:

    variable = target.variable
    if not variable.has_symmetry_target:
        log.warning(f'Symmetry target defined for component {target} but not for {variable}')
        return

    input_ = variable.input
    if not input_.has_symmetry_target:
        log.warning(f'Symmetry target defined for component {variable} but not for {input}')
        return

    driver = input_.rbf_driver

    if not driver.has_symmetry_target:
        log.warning(f'Symmetry target defined for component {input} but not for {driver}')
        return

    if driver.symmetry_lock__internal__:
        return

    m_driver = driver.id_data.rbf_drivers.search(driver.symmetry_identifier)
    if m_driver is None:
        log.warning(f'Search failed for symmetry target of {driver}.')
        return

    m_input = driver.inputs.search(input.symmetry_identifier)
    if m_input is None:
        log.warning(f'Search failed for symmetry target of {input}.')
        return

    m_variable = m_input.variables.search(variable.symmetry_identifier)
    if m_variable is None:
        log.warning((f'Search failed for symmetry target of {variable}.'))
        return

    m_target = m_variable.targets.search(target.symmetry_identifier)
    if m_target is None:
        log.warning((f'Search failed for symmetry target of {target}.'))
        return

    log.info(f'Mirroring {variable} property {name}')
    m_driver.symmetry_lock__internal__ = True

    try:
        setattr(m_target, name, value)
    finally:
        m_driver.symmetry_lock__internal__ = False


@event_handler(RBFDriverInputTarget.BoneTargetUpdateEvent)
def on_input_target_bone_target_update(event: RBFDriverInputTarget.BoneTargetUpdateEvent) -> None:
    if event.target.has_symmetry_target:
        value = symmetrical_target(event.value) or event.value
        input_target_mirror_property(event.target, "bone_target", value)


@event_handler(RBFDriverInputTarget.DataPathUpdateEvent)
def on_input_target_data_path_update(event: RBFDriverInputTarget.DataPathUpdateEvent) -> None:
    if event.target.has_symmetry_target:
        def replace(match: Match):
            value = match.group()
            return symmetrical_target(value) or value
        value = re.findall(r'\["(.*?)"\]', replace, event.value)
        input_target_mirror_property(event.target, "data_path", value)


@event_handler(RBFDriverInputTarget.IDTypeUpdateEvent)
def on_input_target_id_type_update(event: RBFDriverInputTarget.IDTypeUpdateEvent) -> None:
    if event.target.has_symmetry_target:
        input_target_mirror_property(event.target, "id_type", event.value)


@event_handler(RBFDriverInputTarget.ObjectUpdateEvent)
def on_input_target_object_type(event: RBFDriverInputTarget.ObjectUpdateEvent) -> None:
    if event.target.has_symmetry_target:
        input_target_mirror_property(event.target, "object", event.value)


@event_handler(RBFDriverInputTarget.RotationModeUpdateEvent)
def on_input_target_object_type(event: RBFDriverInputTarget.RotationModeUpdateEvent) -> None:
    if event.target.has_symmetry_target:
        input_target_mirror_property(event.target, "rotation_mode", event.value)


@event_handler(RBFDriverInputTarget.TransformSpaceUpdateEvent)
def on_input_target_object_type(event: RBFDriverInputTarget.TransformSpaceUpdateEvent) -> None:
    if event.target.has_symmetry_target:
        input_target_mirror_property(event.target, "transform_space", event.value)


@event_handler(RBFDriverInputTarget.TransformSpaceUpdateEvent)
def on_input_target_object_type(event: RBFDriverInputTarget.TransformTypeUpdateEvent) -> None:
    if event.target.has_symmetry_target:
        input_target_mirror_property(event.target, "transform_type", event.value)


