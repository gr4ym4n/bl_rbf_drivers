
from difflib import Match
import re
from typing import TYPE_CHECKING
from logging import getLogger
from .utils import owner_resolve
from .events import event_handler
from ..lib.symmetry import symmetrical_target
from ..api.input_target import (InputTargetBoneTargetUpdateEvent,
                                InputTargetDataPathUpdateEvent,
                                InputTargetObjectUpdateEvent,
                                InputTargetRotationModeUpdateEvent,
                                InputTargetTransformSpaceUpdateEvent,
                                InputTargetTransformTypeUpdateEvent)
if TYPE_CHECKING:
    from ..api.input_target import RBFDriverInputTarget
    from ..api.input_variable import RBFDriverInputVariable
    from ..api.input import RBFDriverInput
    from ..api.driver import RBFDriver

log = getLogger("rbf_drivers")


class SymmetryError(Exception):
    pass


def resolve_input_target_mirror(target: 'RBFDriverInputTarget') -> 'RBFDriverInputTarget':

    variable: 'RBFDriverInputVariable' = owner_resolve(target, ".targets")
    if not variable.has_symmetry_target:
        raise SymmetryError(f'Symmetry target defined for {target} but not for {variable}')

    input: 'RBFDriverInput' = owner_resolve(variable, ".variables")
    if not input.has_symmetry_target:
        raise SymmetryError(f'Symmetry target defined for {variable} but not for {input}')

    driver: 'RBFDriver' = owner_resolve(input, ".variables")
    if not input.has_symmetry_target:
        raise SymmetryError(f'Symmetry target defined for {input} but not for {driver}')

    if driver.symmetry_lock__internal__:
        return None

    m_driver = driver.id_data.rbf_drivers.search(driver.symmetry_identifier)
    if m_driver is None:
        raise SymmetryError(f'Search failed for {driver} symmetry target')

    m_input = m_driver.inputs.search(input.symmetry_identifier)
    if m_input is None:
        raise SymmetryError(f'Search failed for {input} symmetry target')

    m_variable = m_input.variables.search(variable.symmetry_identifier)
    if m_variable is None:
        raise SymmetryError(f'Search failed for {variable} symmetry identifier')

    m_target = m_variable.targets.search(target.symmetry_identifier)
    if m_target is None:
        raise SymmetryError(f'Search failed for {target} symmetry identifier')

    return m_target


@event_handler(InputTargetBoneTargetUpdateEvent)
def on_input_target_bone_target_update(event: InputTargetBoneTargetUpdateEvent) -> None:
    if event.target.has_symmetry_target:
        try:
            mirror = resolve_input_target_mirror(event.target)
        except SymmetryError as error:
            log.error(error.message)
        else:
            if mirror:
                setattr(mirror, "bone_target", symmetrical_target(event.value) or event.value)


@event_handler(InputTargetDataPathUpdateEvent)
def on_input_target_data_path_update(event: InputTargetDataPathUpdateEvent) -> None:
    if event.target.has_symmetry_target:
        try:
            mirror = resolve_input_target_mirror(event.target)
        except SymmetryError as error:
            log.error(error.message)
        else:
            if mirror:
                def replace(match: Match):
                    value = match.group()
                    return symmetrical_target(value) or value
                setattr(mirror, "data_path", re.findall(r'\["(.*?)"\]', replace, event.value))


@event_handler(InputTargetObjectUpdateEvent)
def on_input_target_object_update(event: InputTargetObjectUpdateEvent) -> None:
    if event.target.has_symmetry_target:
        try:
            mirror = resolve_input_target_mirror(event.target)
        except SymmetryError as error:
            log.error(error.message)
        else:
            if mirror:
                value = event.value
                if value is not None:
                    name = symmetrical_target(value.name)
                    if name:
                        import bpy
                        if name in bpy.data.objects:
                            value = bpy.data.objects[name]
                setattr(mirror, "bone_target", value)


@event_handler(InputTargetRotationModeUpdateEvent)
def on_input_target_rotation_mode_update(event: InputTargetRotationModeUpdateEvent) -> None:
    if event.target.has_symmetry_target:
        try:
            mirror = resolve_input_target_mirror(event.target)
        except SymmetryError as error:
            log.error(error.message)
        else:
            if mirror:
                setattr(mirror, "rotation_mode", event.value)


@event_handler(InputTargetTransformSpaceUpdateEvent)
def on_input_target_transform_space_update(event: InputTargetTransformSpaceUpdateEvent) -> None:
    if event.target.has_symmetry_target:
        try:
            mirror = resolve_input_target_mirror(event.target)
        except SymmetryError as error:
            log.error(error.message)
        else:
            if mirror:
                setattr(mirror, "transform_space", event.value)


@event_handler(InputTargetTransformTypeUpdateEvent)
def on_input_target_transform_type_update(event: InputTargetTransformTypeUpdateEvent) -> None:
    if event.target.has_symmetry_target:
        try:
            mirror = resolve_input_target_mirror(event.target)
        except SymmetryError as error:
            log.error(error.message)
        else:
            if mirror:
                setattr(mirror, "transform_type", event.value)


