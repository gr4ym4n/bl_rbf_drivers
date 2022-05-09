---
title: Upgrading
menuTitle: Upgrading
description: 'Familiarize yourself with the basic process and options when setting up an RBF driver'
position: 207
category: Manual
fullscreen: true
---

If you have created RBF drivers using the addon before version 2.0, you can use the provided upgrade operation to import them for use in RBF Drivers 2.0+. The upgrade operation is not available in the RBF Drivers panel, but you can use the [operator search menu](https://docs.blender.org/manual/en/latest/interface/controls/templates/operator_search.html) to run it:

1. Open the operator search menu (by default this is achieved by the F3 key)
2. Type something like "upgrade rbf drivers" into the search field
3. Select the **Upgrade RBF Drivers** option

The operator will then search all the objects in the open Blender file for RBF drivers created with previous versions of the addon and offer you the option to upgrade them.

<alert type="warning">

The upgrade process does its best to map the settings of the legacy RBF drivers to settings for a new RBF driver, but due to major improvements in version 2.0, a direct translation is not always possible. The new RBF driver may behave differently from the originaland you are advised to familiarize yourself with the current version of the addon as well as test and adjust the new RBF driver to your requirements.

</alert>