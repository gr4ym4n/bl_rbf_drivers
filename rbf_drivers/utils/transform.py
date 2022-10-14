
from math import acos, fabs, pi
from typing import TYPE_CHECKING, Optional, Tuple, Union
from bpy.types import Object, PoseBone
from mathutils import Matrix


def target(object: Optional[Object],
           bone_target: Optional['str']="") -> Optional[Union[Object, PoseBone]]:

    result = object

    if isinstance(result, Object) and result.type == 'ARMATURE' and bone_target:
        result = object.pose.bones.get(bone_target)

    return result


def matrix(owner: Optional[Union[Object, PoseBone]],
           space: Optional[str]='WORLD_SPACE') -> Matrix:

    if isinstance(owner, Object):
        if space == 'TRANSFORM_SPACE' : return owner.matrix_basis
        if space == 'LOCAL_SPACE'     : return owner.matrix_local
        if space == 'WORLD_SPACE'     : return owner.matrix_world

    elif isinstance(owner, PoseBone):
        if space == 'TRANSFORM_SPACE' : return owner.matrix_channel
        if space in {'WORLD_SPACE', 'LOCAL_SPACE'}:
            return owner.id_data.convert_space(pose_bone=owner,
                                               matrix=owner.matrix,
                                               from_space='POSE',
                                               to_space=space[:5])

    return Matrix.Identity(4)


def distance(a: Union[Object, PoseBone, Tuple[Union[Object, PoseBone], str]],
             b: Union[Object, PoseBone, Tuple[Union[Object, PoseBone], str]]) -> float:

    a = matrix(*a) if isinstance(a, tuple) else matrix(a)
    b = matrix(*b) if isinstance(b, tuple) else matrix(b)

    return (a.to_translation() - b.to_translation()).length


def rotational_difference(a: Union[Object, PoseBone], b: Union[Object, PoseBone]) -> float:
    # TODO check space for rotational difference driver
    a = matrix(a, 'TRANSFORM_SPACE').to_quaternion()
    b = matrix(b, 'TRANSFORM_SPACE').to_quaternion()
    angle = fabs(2.0 * acos((a.inverted() * b)[0]))

    return 2.0 * pi - angle if angle > pi else angle

