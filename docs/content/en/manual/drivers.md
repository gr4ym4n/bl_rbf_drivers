---
title: Drivers
menuTitle: Drivers
description: 'Familiarize yourself with the basic process and options when setting up an RBF driver'
position: 201
category: Manual
fullscreen: false
---

Once you have [installed](/tutorials/installation) the addon, there should be an **RBF Drivers** section visible in the Object Properties panel.

## Adding Drivers

![adding rbf drivers](/img/manual-drivers-adding-drivers-01.jpg)

To add an RBF driver to an object, select the **Add** button in the RBF Drivers panel. If there aren't yet any RBF drivers for the object the button will be the only thing visible, otherwise it will be located next to the list of RBF drivers.

<alert type="info">

You can add an RBF driver to any object you wish, though [it is usually recommended](/manual/faq#which-object-should-i-add-an-rbf-driver-to) that you add it the object that contains the *driven* properties.

</alert>

## Driver Types

There are a number of different types of RBF driver available depending on what object you are adding the RBF driver to. You can add [Generic](#generic) or [Generic (Symmetrical)](#generic-symmetrical) drivers to *any* object, whereas [Shape Keys](#shape-keys) and [Shape Keys (Symmetrical)](#shape-keys-symmetrical) drivers can only be added to **Mesh**, **Lattice** or **Curve** objects, as only these objects can have shape keys.

![RBF driver types](/img/manual-drivers-driver-types-01.jpg)

### Generic

Generic RBF drivers allow the most flexibility. There are no restrictions to the type of [Input](/manual/inputs) or [Output](manual/outputs) you can add to them.

### Generic (Symmetrical)

Selecting the [symmetrical](/manual/symmetry) version of a [generic](#generic) RBF driver will actually create 2 linked RBF drivers, one for each of the left and right sides. This is useful where you have a mirrored rig because you can set up the driver for one side and the addon will mirror your [inputs](/manual/inputs), [outputs](/manual/outputs) and [poses](/manual/poses) to the other side as you make changes.

<alert type="info">

If you've already set up an RBF driver and you want to create a symmetrical, linked copy of it, you can use the [**duplicate mirrored**](#duplicate-mirrored) action from the [driver actions menu](#driver-actions-menu) at the side of the Driver's list. The action will be available as long as the RBF driver is named according to [Blender's naming conventions for mirroring](https://docs.blender.org/manual/en/latest/animation/armatures/bones/editing/naming.html#naming-conventions) (e.g. "RBFDriver.L")

</alert>

<alert type="warning">

There are some idiosyncracies to be aware of when working with symmetrical RBF drivers. It is recommended that you read through the manual page on [symmetry](/manual/symmetry).

</alert>

### Shape Keys

A common use case for RBF drivers is to drive shape keys based on pose bone transforms. You can do this with a [generic](#generic) RBF driver but setting up all the shape key targets can be a little tedious, so there is the option of adding a **Shape Keys** RBF driver. This option will only be available if the object you're adding the RBF driver to is compatible with shape keys (i.e. a Mesh, Lattice or Curve).

With a **Shape Keys** driver, you will no longer have the option of adding different types of [output](/manual/outputs), instead you'll see a list of the shape keys that have been defined for the object that you can select from.

<alert type="info">

You can convert a [**Shape Keys** driver](#shape-keys) to a [**Generic** driver](#generic) using the [**Make Generic**](#make-generic) action in the specials menu to the side of the list of drivers. You cannot convert a [**Shape Keys** driver](#shape-keys) to a [**Generic** driver](#generic).

</alert>

### Shape Keys (Symmetrical)

The symmetrical version of the **Shape Keys** RBF driver works in much the same way as the [symmetrical generic](#generic-symmetrical) driver described above, so you actually get an RBF driver for both left and right sides and changes to one are mirrored to the other. This includes target shape keys, so you can use a symmetrical driver to quickly set up drivers for shape keys on both sides of the mesh, as long as you are adhering to the [normal naming conventions](https://docs.blender.org/manual/en/latest/animation/armatures/bones/editing/naming.html#naming-conventions) when naming your shape keys.

## Driver Actions Menu

![driver actions menu](/img/manual-drivers-action-menu.jpg)

Additional actions for the currently selected RBF driver are available in the dropdown menu to the right of the list of drivers.

### Duplicate Mirrored

Selecting **Duplicate Mirrored** will create a copy of the currently selected driver with mirrored settings where appropriate. For example if the original driver has an input that targets a "Clavicle.L" bone, the *mirrored* driver will target "Clavicle.R". Settings between mirrored drivers remain synchronized (see the manual pages on [symmetry](/manual/symmetry) for more details).

<alert type="info">

The **Duplicate Mirrored** action will only be usable if the currently selected driver has a name that adheres to [Blender's naming conventions](https://docs.blender.org/manual/en/latest/animation/armatures/bones/editing/naming.html#naming-conventions).

</alert>

### Make Generic

Selecting **Make Generic** will convert a [Shape Keys driver](#shape-keys) into a [Generic driver](#generic).

<alert type="info">

The **Make Generic** action will only be usable if the currently selected is not a [Generic driver](#generic).

</alert>

<alert type="warning">

Though you can undo the action to reverse the changes, there is no action within RBF Drivers to convert a [Generic driver](#generic) to a [Shape Keys driver](#shape-keys).

</alert>

## Removing Drivers

![remove-driver](/img/manual-drivers-remove-driver.jpg)

To remove an RBF driver simply click the **-** button next to the list of drivers. The data properties related to the RBF driver and the drivers it is managing internally will be removed along with the RBF driver itself.
