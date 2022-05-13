---
title: Upgrading
menuTitle: Upgrading
description: 'Familiarize yourself with the basic process and options when setting up an RBF driver'
position: 207
category: Manual
fullscreen: true
---

If you have created RBF drivers using the addon before version 2.0, you can use the provided upgrade operation to import them for use in RBF Drivers 2.0+. The upgrade operation is not available in the RBF Drivers panel, but you can use the [operator search menu](https://docs.blender.org/manual/en/latest/interface/controls/templates/operator_search.html) to run it:

1. Open the operator search menu (by default this is achieved by tapping F3)
2. Type something like "upgrade rbf drivers" into the search field
3. Select the **Upgrade RBF Drivers** option

The operator will then search all the objects in the open Blender file for RBF drivers created with previous versions of the addon and offer you the option to upgrade all or some of them.

<alert type="warning">

The upgrade process does its best to map the settings of the legacy RBF drivers to settings for a new RBF driver, but due to major changes in version 2.0, a direct translation is not always possible. Known limitations of the upgrade process are detailed below.

* **Interpolation**  
  RBF Drivers v1 offered 4 interpolation types: *Linear*, *Gaussian*, *Multi-Quadratic Biharmonc* and *Inverse Multi-Quadratic Biharmonic* and further options for *Radius* and *Smoothing*. [RBF Drivers v2 has a much more flexible, predictable and performant interpolation mechanism](/manual/interpolation) based on curves, but it's not always practicable to map the interpolation settings between v1 and v2. If your original RBF driver used *Linear* or *Multi-quadratic* interpolation types with default settings for *Radius* and *Smoothing* there should be little or no difference with the upgraded driver, but in other cases there may be. It is advised that you familiarize yourself with the new interpolation settings in v2 and adjust them to your needs.
* **Rotation Inputs**  
  RBF Drivers v1 made several assumptions in how it handled rotation input data. Version 2 requires you to be more specific when setting up rotation inputs. In the vast majority of cases the upgrade operation should correctly map the rotation settings and data when upgrading, but if you have rotation inputs you are advised to verify things are working as they should after the updgrade.
* **Edge Cases**  
  There are so many ways to set up RBF drivers that there will undoubtedly be some edge-cases where the upgrade doesn't work as you might expect. If it fails for you, please [get in touch](/manual/support) as it may require some manual data manipulation or a change to the upgrade script.

</alert>