
from typing import TYPE_CHECKING
from bpy.types import AddonPreferences
from bpy.props import BoolProperty, StringProperty
if TYPE_CHECKING:
    from bpy.types import Context

class RBFDriverPreferences(AddonPreferences):
    bl_idname = "rbf_drivers"

    check_for_updates_on_startup: BoolProperty(
        name="Check for updates on startup",
        description="",
        default=True,
        options=set(),
        )

    license_key: StringProperty(
        name="License Key",
        description="License key for use with auto-update",
        default="",
        options=set()
        )

    debug: BoolProperty(
        name="Debug",
        description="Keep debugging logs",
        default=False,
        options=set()
        )

    def draw(self, _: 'Context') -> None:
        layout = self.layout
        layout.prop(self, "license_key", text="License Key")
        layout.operator("rbf_driver.check_for_update", text="Check for update")
        row = layout.row()
        row.alignment = 'RIGHT'
        row.label(text="Check on startup:")
        row.prop(self, "check_for_updates_on_startup", text="")