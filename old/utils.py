
from typing import Dict, Tuple
from bpy.app import version

def bbone_property_tags() -> Dict[str, bool]:
    return {
        "bbone_curveinx": True,
        "bbone_curveinz": True,
        }

def bbone_property_name(key: str) -> str:
    if key == "bbone_curveinz":
        return f'bbone_curvein{"z" if version[0] >= 3 else "y"}'

    if key == "bbone_curveoutz":
        return f'bbone_curveout{"z" if version[0] >= 3 else "y"}'

    if key == "bbone_scaleinz":
        return key if version[0] >= 3 else "bbone_scaleiny"

    if key == "bbone_scaleoutz":
        return key if version[0] >= 3 else "bbone_scaleouty"

        

def bbone_property_names() -> Tuple[str]:
    v3 = version[0] >= 3
    v2 = not v3
    result = []
    result.append("bbone_curveinx")
    result.append("bbone_curveiny" if v2 else "bbone_curveinz")
    result.append("bbone_curveoutx")
    result.append("bbone_curveouty" if v2 else "bbone_curveoutz")
