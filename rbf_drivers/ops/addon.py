
from typing import Set, TYPE_CHECKING
import logging
from bpy.types import Operator
from bpy.props import StringProperty
from ..app.utils import update_filepath_check, update_script_read, update_preferences
if TYPE_CHECKING:
    from bpy.types import Context, Event

log = logging.getLogger()


class RBFDRIVERS_OT_addon_reset_update_status(Operator):
    bl_idname = "rbf_driver.addon_reset_update_status"
    bl_label = "OK"
    bl_description = "Acknowledge"
    bl_options = {'INTERNAL', 'UNDO'}

    def execute(self, context: 'Context') -> Set[str]:
        prefs = context.preferences.addons["rbf_drivers"].preferences
        prefs.new_release_version = ""
        prefs.new_release_url = ""
        prefs.new_release_date = ""
        prefs.new_release_path = ""
        prefs.new_release_is_stable = False
        prefs.update_error = ""
        prefs.update_status = 'NONE'
        return {'FINISHED'}


class RBFDRIVERS_OT_addon_install_update(Operator):
    bl_idname = "rbf_driver.addon_install_update"
    bl_label = "Install"
    bl_description = "Install the update"
    bl_options = {'INTERNAL', 'UNDO'}

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        prefs = context.preferences.addons["rbf_drivers"].preferences
        return prefs.update_status == 'READY'

    def execute(self, context: 'Context') -> Set[str]:
        import bpy

        log.debug("Installing update.")

        # TODO Zip and cache current installation
        
        prefs = context.preferences.addons["rbf_drivers"].preferences
        filepath = prefs.new_release_path

        def cancel_with_error(error: Exception) -> Set[str]:
            prefs.update_status = 'ERROR'
            prefs.update_error = str(error)
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}

        log.debug(f'Checking update file path: "{filepath}"')

        error = update_filepath_check(filepath)
        if error:
            return cancel_with_error(error)
        else:
            log.info("Update file path checked OK.")

        log.debug("Creating update script.")

        text = bpy.data.texts.get("rbf_drivers_update_script")
        if text:
            text.clear()
        else:
            text = bpy.data.texts.new("rbf_drivers_update_script")

        try:
            data = update_script_read(filepath)
        except Exception as error:
            return cancel_with_error(error)
        else:
            text.write(data)

        log.debug("Running update script.")

        try:
            context = context.copy()
            context['edit_text'] = text
            bpy.ops.text.run_script(context)
        except Exception as error:
            return cancel_with_error(error)

        return {'FINISHED'}


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
        prefs = context.preferences.addons["rbf_drivers"].preferences
        return bool(prefs.license_key)

    def modal(self, context: 'Context', event: 'Event') -> Set[str]:

        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        prefs = context.preferences.addons["rbf_drivers"].preferences
        prefs.update_progress = self._timer.time_duration

        area = context.area
        if area:
            area.tag_redraw()

        result = self._result

        if result is None:
            return {'PASS_THROUGH'}

        self._thread.join()
        self._thread = None
        self._result = None
        self.cancel(context)

        if isinstance(result, Exception):
            update_preferences(prefs, 'ERROR', update_error=str(result))
            return {'CANCELLED'}

        url = result.get("url")

        if not isinstance(url, str) or not url:
            update_preferences(prefs, 'NO_UPDATE')
            return {'CANCELLED'}

        update_preferences(prefs, 'AVAILABLE',
                           new_release_url=url,
                           new_release_version=result.get("version"),
                           new_release_date=result.get("release_date"),
                           new_release_is_stable=(result.get("stable", False) in (True, 'true')))
        return {'FINISHED'}

    def execute(self, context: 'Context') -> Set[str]:
        import bpy, addon_utils, threading, urllib

        prefs = context.preferences.addons["rbf_drivers"].preferences

        def cancel_with_error(error):
            update_preferences(prefs, 'ERROR', str(error))
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}

        defn = next((m for m in addon_utils.modules() if m.__name__ == "rbf_drivers"), None)
        if not defn:
            return cancel_with_error("Unable to find module data file")

        bl_info = defn.bl_info
        version = bl_info.get("version")
        if version is None:
            return cancel_with_error("bl_info.version not found")

        if (not isinstance(version, (tuple, list))
            or len(version) != 3
            or not all(isinstance(value, int) for value in version)
            ):
            return cancel_with_error("bl_info version is not valid")

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
            return cancel_with_error('Unable to read update server URL')
        else:
            url = f'{update_url}?{urllib.parse.urlencode(params)}'

        log.debug((f'Checking if update is available. '
                   f'Current version is {params["version"]}'))

        def send_request(self, url: str) -> None:
            import json
            import urllib
            import urllib.request
            try:
                with urllib.request.urlopen(url) as response:
                    if str(response.code) == "200":
                        self._result = json.loads(response.read())
                    else:
                        self._result = RuntimeError(str(response))
            except Exception as error:
                self._result = error

        update_preferences(prefs, 'CHECKING', update_progress=0.0)

        area = context.area
        if area:
            area.tag_redraw()

        self._timer = context.window_manager.event_timer_add(0.2, window=context.window)
        self._result = None
        self._thread = threading.Thread(target=send_request, args=(self, url))
        self._thread.start()

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def cancel(self, context: 'Context') -> None:
        context.window_manager.event_timer_remove(self._timer)
        self._timer = None

        prefs = context.preferences.addons["rbf_drivers"].preferences
        prefs.update_progress = 0.0


class RBFDRIVERS_OT_addon_download_update(Operator):
    bl_idname = "rbf_driver.addon_download_update"
    bl_label = "Download"
    bl_description = "Download update"
    bl_options = {'INTERNAL', 'UNDO'}
    _thread = None
    _timer = None
    _error = None
    _filename = ""
    url: StringProperty()

    @classmethod
    def poll(cls, context: 'Context') -> bool:
        prefs = context.preferences.addons["rbf_drivers"].preferences
        return prefs.update_status == 'AVAILABLE'

    def modal(self, context: 'Context', event: 'Event') -> Set[str]:
        if event.type != 'TIMER':
            return {'PASS_THROUGH'}

        prefs = context.preferences.addons["rbf_drivers"].preferences
        prefs.update_progress = self._timer.time_duration

        area = context.area
        if area:
            area.tag_redraw()

        error = self._error
        if error is not None:
            self.cancel(context)
            update_preferences(prefs, 'ERROR', str(error))
            self.report({'ERROR'}, str(error))
            return {'CANCELLED'}

        path = self._filename
        if path:
            self.cancel(context)
            update_preferences(prefs, 'READY', new_release_path=path)
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def execute(self, context: 'Context') -> Set[str]:
        import threading

        prefs = context.preferences.addons["rbf_drivers"].preferences

        url = prefs.new_release_url
        if not url:
            message = "Required URL not found"
            update_preferences(prefs, 'ERROR', update_error=message)
            self.report({'ERROR'}, message)
            return {'CANCELLED'}

        log.debug(f'Requesting download for update')

        def download_file(self, url: str) -> None:
            import urllib
            try:
                filename, _ = urllib.request.urlretrieve(url)
            except (urllib.error.URLError, urllib.error.HTTPError) as error:
                self._error = error
            else:
                self._filename = filename

        update_preferences(prefs, 'DOWNLOADING', update_progress=0.0)

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

        prefs = context.preferences.addons["rbf_drivers"].preferences
        prefs.update_progress = 0.0
