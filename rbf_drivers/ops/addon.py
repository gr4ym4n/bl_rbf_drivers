
from json import JSONDecodeError
from typing import Set, TYPE_CHECKING
import logging
from bpy.types import Operator
from bpy.props import StringProperty
if TYPE_CHECKING:
    from bpy.types import Context, Event

log = logging.getLogger()

class RBFDRIVERS_OT_check_for_update(Operator):
    bl_idname = "rbf_driver.check_for_update"
    bl_label = "Check for update"
    bl_description = "Check if an update is available"
    bl_options = {'INTERNAL', 'UNDO'}

    _timer = None
    _thread = None
    _result = None

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        return bool(context.preferences.addons["rbf_drivers"].preferences.license_key)

    def modal(self, context: 'Context', event: 'Event') -> Set[str]:

        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        result = self._result

        if result is None:
            return {'PASS_THROUGH'}

        self._thread.join()
        self._thread = None
        self._result = None
        self.cancel(context)

        if isinstance(result, Exception):
            log.error(str(result))

            def draw(self, _):
                column = self.layout.column()
                column.separator()
                column.label(text="An error occured while checking for updates.")
                column.label(text="See console for details.")
                column.separator()

            context.window_manager.popup_menu(draw, title="Update Check Failed", icon='ERROR')
            return {'CANCELLED'}

        url = result.get("url", "")

        if url and result.get("update", False):
            def draw(self, _):
                column = self.layout.column()
                column.separator()
                version = result.get("version", "")
                if version:
                    column.label(text=f'RBF Drivers {version} is available')
                column.operator(RBFDRIVERS_OT_update.bl_idname,
                                text="Download and Install",
                                depress=RBFDRIVERS_OT_update._running).url = url
                column.separator()
            context.window_manager.popup_menu(draw, title="Update Available", icon='PLUGIN')
        else:
            def draw(self, _):
                column = self.layout.column()
                column.separator()
                column.label(text="You currently have the latest version of RBF Drivers installed")
                column.separator()
            context.window_manager.popup_menu(draw, title="No Update Available", icon='PLUGIN')

        return {'FINISHED'}

    def execute(self, context: 'Context') -> Set[str]:
        import bpy, threading, urllib, addon_utils

        name = "RBF Drivers"
        info = next((m.bl_info for m in addon_utils.modules() if m.bl_info.get("name") == name), None)
        if not info:
            self.report({'ERROR'}, "Failed to read bl_info")
            return {'CANCELLED'}

        version = info.get("version")

        if version is None:
            self.report({'ERROR'}, "bl_info.version not found")
            return {'CANCELLED'}

        if (not isinstance(version, tuple)
            or len(version) != 3
            or not all(isinstance(value, int) for value in version)
            ):
            self.report({'ERROR'}, "bl_info version is not valid")
            return {'CANCELLED'}

        try:
            prefs = context.preferences.addons["rbf_drivers"].preferences
        except KeyError:
            self.report({'ERROR'}, "Failed to read preferences.")
            return {'CANCELLED'}

        params = {
            "product": "rbf_drivers",
            "license": prefs.license_key,
            "version": ".".join(map(str, version)),
            "blender": ".".join(map(str, bpy.app.version)),
            "beta": prefs.include_beta_versions
            }

        url = ""
        try:
            from ..app.config import update_url
        except:
            self.report({'ERROR'}, 'Unable to read update server URL')
            return {'CANCELLED'}
        else:
            url = f'{update_url}?{urllib.parse.urlencode(params)}'

        def send_request(self, url: str) -> None:
            import urllib, json
            try:
                with urllib.request.urlopen(url) as response:
                    if str(response.code) == "200":
                        self._result = json.loads(response.read())
                    else:
                        self._result = RuntimeError(str(response))
            except Exception as error:
                self._result = error

        self._timer = context.window_manager.event_timer_add(0.2, window=context.window)
        self._result = None
        self._thread = threading.Thread(target=send_request, args=(self, url))
        self._thread.start()

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context: 'Context') -> None:
        context.window_manager.event_timer_remove(self._timer)
        self._timer = None


class RBFDRIVERS_OT_update(Operator):
    bl_idname = "rbf_driver.addon_update"
    bl_label = "Update"
    bl_description = "Update to latest version"
    bl_options = {'INTERNAL', 'UNDO'}
    _thread = None
    _timer = None
    _error = None
    _filename = ""
    url: StringProperty()

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        return bool(context.preferences.addons["rbf_drivers"].preferences.license_key)

    def modal(self, context: 'Context', event: 'Event') -> Set[str]:
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        error = self._error
        if error is not None:
            log.error(str(error))
            self.cancel(context)
            def draw(self, _: 'Context') -> None:
                layout = self.layout
                layout.separator()
                layout.label(text="An error occured while dowloading the update.")
                layout.label(text="See console for details.")
                layout.separator()
            context.window_manager.popup_menu(draw, title="Update Failed", icon='ERROR')
            return {'CANCELLED'}

        filename = self._filename
        if filename:
            import bpy
            self.cancel(context)
            bpy.ops.preferences.addon_disable(module="rbf_drivers")
            bpy.ops.preferences.addon_remove(module="rbf_drivers")
            bpy.ops.preferences.addon_install(filepath=filename)
            bpy.ops.preferences.addon_enable(module="rbf_drivers")
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def execute(self, context: 'Context') -> Set[str]:
        import threading
        
        url = self.url
        if not url:
            self.report({'ERROR'}, "Required parameter URL not found")
            return {'CANCELLED'}

        def download_file(self, url: str) -> None:
            import urllib
            try:
                filename, _ = urllib.request.urlretrieve(url)
            except (urllib.error.URLError, urllib.error.HTTPError) as error:
                self._error = error
            else:
                self._filename = filename

        self._timer = context.window_manager.event_timer_add(0.2, window=context.window)
        self._error = None
        self._filename = ""
        self._thread = threading.Thread(target=download_file, args=(self, url))
        self._thread.start()

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context: 'Context') -> None:
        context.window_manager.event_timer_remove(self._timer)
        self._timer = None
