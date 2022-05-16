
import datetime
from typing import TYPE_CHECKING
from bpy.types import AddonPreferences
from bpy.props import BoolProperty, EnumProperty, FloatProperty, StringProperty
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

    new_release_version: StringProperty(
        default="",
        options={'HIDDEN'}
        )

    new_release_url: StringProperty(
        default="",
        options={'HIDDEN'}
        )

    new_release_date: StringProperty(
        default="",
        options={'HIDDEN'}
        )

    new_release_path: StringProperty(
        default="",
        options={'HIDDEN'}
        )

    new_release_is_stable: BoolProperty(
        default=False,
        options={'HIDDEN'}
        )

    include_beta_versions: BoolProperty(
        name="Include Beta Versions",
        description="Download and install beta versions",
        default=False,
        options=set()
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

    update_error: StringProperty(
        default="",
        options={'HIDDEN'}
        )

    update_status: EnumProperty(
        items=[
            ('NONE', "", ""),
            ('ERROR', "Update Error", ""),
            ('CHECKING', "Checking for update", ""),
            ('NO_UPDATE', "No update available", ""),
            ('AVAILABLE', "Update available", ""),
            ('DOWNLOADING', "Downloading update", ""),
            ('READY', "Ready to install", ""),
            ],
        default='NONE',
        options={'HIDDEN'}
        )

    update_progress: FloatProperty(
        min=0.0,
        default=0.0,
        options={'HIDDEN'}
        )

    def draw(self, _: 'Context') -> None:

        split = self.layout.split(factor=0.15)
        labels = split.column()
        values = split.column()

        labels.label(text="License Key:")
        values.prop(self, "license_key", text="")

        if self.license_key:
            labels.separator(factor=0.5)
            values.separator(factor=0.5)

            status = self.update_status

            if status == 'CHECKING':
                progress = self.update_progress % 1

                if   progress < 0.25: icon = 'PROP_OFF'
                elif progress < 0.5 : icon = 'PROP_CON'
                elif progress < 0.75: icon = 'PROP_ON'
                else                : icon = 'PROP_CON'
            else:
                icon = 'URL'

            values.operator("rbf_driver.check_for_update",
                            icon=icon,
                            text="Check for update",
                            depress=(status == 'CHECKING'))

            labels.separator(factor=0.5)
            values.separator(factor=0.5)

            row = values.row()
            row.alignment = 'RIGHT'
            row.label(text="Include beta versions:")
            row.prop(self, "include_beta_versions", text="")

            row = values.row()
            row.alignment = 'RIGHT'
            row.label(text="Check at startup:")
            row.prop(self, "check_for_updates_on_startup", text="")

            labels.separator(factor=0.5)
            values.separator(factor=0.5)
            
            if status == 'ERROR':
                column = values.column(align=True)
                column.box().row().label(icon='ERROR', text="Update Failed")
                column.box().label(text=self.update_error)
                column.box().operator("rbf_driver.addon_reset_update_status", text="OK")

            elif status == 'NO_UPDATE':
                column = values.column(align=True)
                column.box().row().label(icon='PLUGIN', text="No Update Available")
                column.box().label(text="You currently have the latest compatible version installed")

            elif status in {'AVAILABLE', 'DOWNLOADING', 'READY', 'INSTALLING'}:
                column = values.column(align=True)

                row = column.box().row()
                row.label(icon='PLUGIN',
                          text="An update is available")

                split = column.box().row().split(factor=0.3)
                names = split.column()
                value = split.column()

                names.label(icon='BLANK1', text="Version:")
                value.label(text=self.new_release_version)

                rdate = self.new_release_date
                try:
                    date = datetime.date(int(rdate[:4]), int(rdate[4:6]), int(rdate[6:]))
                    text = date.strftime("%b %d %Y")
                except:
                    text = "Unknown"

                names.label(icon='BLANK1', text="Release Date:")
                value.label(text=text)

                names.label(icon='BLANK1', text="Stable:")
                value.label(text=f'{"Yes" if self.new_release_is_stable else "No"}')

                row = column.box().row()

                if status == 'AVAILABLE':
                    row.operator("rbf_driver.addon_download_update",
                                 icon='IMPORT',
                                 text="Download")

                elif status == 'DOWNLOADING':
                    prog = self.update_progress % 1
                    
                    if   prog < 0.25: icon = 'PROP_OFF'
                    elif prog < 0.5 : icon = 'PROP_CON'
                    elif prog < 0.75: icon = 'PROP_ON'
                    else            : icon = 'PROP_CON'

                    row.enabled = False
                    row.operator("rbf_driver.addon_download_update",
                                 icon=icon,
                                 text="Dowload",
                                 depress=True)

                else:# status == 'READY':
                    row.operator("rbf_driver.addon_install_update",
                                 icon='FILE_REFRESH',
                                 text="Update")
