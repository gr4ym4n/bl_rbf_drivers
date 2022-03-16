
from bpy.types import PropertyGroup

def owner_resolve(data: PropertyGroup, token: str) -> PropertyGroup:
    path: str = data.path_from_id()
    return data.id_data.path_resolve(path.rpartition(token)[0])
