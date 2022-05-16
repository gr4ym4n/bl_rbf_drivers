
import bpy
import addon_utils
import os
import shutil
import pathlib
import zipfile
import tempfile

PROPS = [
    ("check_for_updates_at_startup", False),
    ("include_beta_versions", False),
    ("license_key", ""),
    ("debug", False)]


def set_error(prefs, error, reenable=False, reinstall=None):
    print(error)
    prefs.update_status = 'ERROR'
    prefs.update_error = str(error)
    if reinstall:
        try:
            addon_utils.disable("rbf_drivers", default_set=True)
            shutil.rmtree(reinstall[0])
            addon_utils.modules_refresh()
            bpy.ops.preferences.addon_install(filepath=reinstall[1])
            bpy.ops.preferences.addon_enable(module="rbf_drivers")
        except Exception as error:
            def draw_func(self, _):
                layout = self.layout
                layout.separator()
                layout.label(icon='BLANK1', text="An unexpected error occurred. See console for  details")
                layout.label(icon='BLANK1', text=f"A backup of the addon was created at {reinstall[1]}")
                layout.label(icon='BLANK1', text="Please reinstall the addon manually.")
                layout.separator()
            bpy.context.window_manager.popup_menu(draw_func,
                                                  title="Reinstallation Failed",
                                                  icon='ERROR')
    elif reenable:
        try:
            addon_utils.enable("rbf_drivers")
        except: pass


def make_backup(path):
    srcpath = pathlib.Path(path).expanduser().resolve(strict=True)
    dirpath = tempfile.mkdtemp()
    zippath = os.path.join(dirpath, "rbf_drivers_backup.zip")

    with zipfile.ZipFile(zippath, "w", zipfile.ZIP_DEFLATED) as file:
        for item in srcpath.rglob("*.py"):
            file.write(item, item.relative_to(srcpath.parent))

    return zippath


def install_update():
    prefs = bpy.context.preferences.addons["rbf_drivers"].preferences
    props = {key: prefs.get(key, default) for key, default in PROPS}
    prefs = None

    path = ""
    for item in addon_utils.modules():
        if item.__name__ == "rbf_drivers" and os.path.exists(item.__file__):
            path = os.path.dirname(item.__file__)

    if not path:
        return set_error(prefs, "Failed to find addon directory")

    backup_path = ""
    try:
        backup_path = make_backup(path)
    except Exception as error:
        return set_error(prefs, error)

    try:
        addon_utils.disable("rbf_drivers", default_set=True)
    except Exception as error:
        return set_error(prefs, error, reenable=True)

    try:
        shutil.rmtree(path)
    except Exception as error:
        return set_error(prefs, error, reenable=True)

    try:
        addon_utils.modules_refresh()
    except Exception as error:
        return set_error(prefs, error, reinstall=(path, backup_path))

    try:
        bpy.ops.preferences.addon_install(filepath=r"FILEPATH")
    except Exception as error:
        return set_error(prefs, error, reinstall=(path, backup_path))

    try:
        bpy.ops.preferences.addon_enable(module="rbf_drivers")
    except Exception as error:
        return set_error(prefs, error, reinstall=(path, backup_path))
    else:
        prefs = bpy.context.preferences.addons["rbf_drivers"].preferences
        prefs["new_release_version"] = ""
        prefs["new_release_url"] = ""
        prefs["new_release_date"] = ""
        prefs["new_release_path"] = ""
        prefs["update_error"] = ""
        prefs["update_status"] = 0
        for key, value in props.items():
            prefs[key] = value

if __name__ == "__main__":
    bpy.app.timers.register(install_update, first_interval=1)
