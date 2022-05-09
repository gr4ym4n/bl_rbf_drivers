---
title: Drivers
menuTitle: Drivers
description: 'Familiarize yourself with the basic process and options when setting up an RBF driver'
position: 201
category: Manual
fullscreen: false
---

## Adding Drivers

Once you have [installed](/installation) the addon, the RBF Drivers panel will be available under the Object Properties panel. You can add an RBF driver to any object you wish, though [we usually recommend](/manual/faq#which-object-should-i-add-an-rbf-driver-to) adding it the object that contains the *driven* properties.

To add an RBF driver to an object, select the **Add** button in the RBF Drivers panel. If there aren't yet any RBF drivers for the object the button will be the only thing visible, otherwise it will be located next to the list of RBF drivers.

## Driver Types

There are a number of different types of RBF driver available depending on what object you are adding the RBF driver to. You can add [Generic](#generic) or [Generic (Symmetrical)](#generic-symmetrical) drivers to any object, whereas [Shape Keys](#shape-keys) and [Shape Keys (Symmetrical)](#shape-keys-symmetrical) drivers can only be added to Mesh, Lattice or Curve objects.

### Generic

Generic RBF drivers allow the most flexibility. There are no restrictions to the type of [Input](/manual/inputs) or [Output](manual/outputs) you can add to them.

### Generic (Symmetrical)

Selecting the [symmetrical](/manual/symmetry) version of a [generic](#generic) RBF driver will actually create 2 linked RBF drivers, one for each of the left and right sides. This is useful where you have a mirrored rig because you can set up the driver for one side and the addon will mirror your [inputs](/manual/inputs), [outputs](/manaul/outputs) and [poses](/manual/poses) to the other side as you make changes.

If you've already set up an RBF driver and you want to create a symmetrical, linked copy of it, you can use the **Duplicate Mirrored** action from the specials menu at the side of the Driver's list. The action will be available as long as the RBF driver is named according to [Blender's naming conventions for mirroring](https://docs.blender.org/manual/en/latest/animation/armatures/bones/editing/naming.html#naming-conventions) (e.g. "RBFDriver.L")

<alert type="warning">

There are some idiosyncracies to be aware of when working with symmetrical RBF drivers. It is recommended that you read through the manual page on [symmetry](/maual/symmetry).

</alert>

### Shape Keys

A common use case for RBF drivers is to drive shape keys based on pose bone transforms. You can do this with a [generic](#generic) RBF driver but setting up all the shape key targets can be a little tedious, so there is the option of adding a **Shape Keys** RBF driver. This option will only be available if the object you're adding the RBF driver to is compatible with shape keys (i.e. a Mesh, Lattice or Curve).

With a **Shape Keys** driver, you will no longer have the option of adding different types of [output](/manual/outputs), instead you'll see a list of the shape keys that have been defined for the object that you can select from.

You can convert a [**Shape Keys** driver](#shape-keys) to a [**Generic** driver](#generic) using the **Make Generic** action in the specials menu to the side of the list of drivers. You cannot convert a [**Shape Keys** driver](#shape-keys) to a [**Generic** driver](#generic).

### Shape Keys (Symmetrical)

The symmetrical version of the **Shape Keys** RBF driver works in much the same way as the [symmetrical generic](#generic-symmetrical) driver described above, so you actually get an RBF driver for both left and right sides and changes to one are mirrored to the other. This includes target shape keys, so you can use a symmetrical driver to quickly set up drivers for shape keys on both sides of the mesh, as long as you are adhering to the [normal naming conventions](https://docs.blender.org/manual/en/latest/animation/armatures/bones/editing/naming.html#naming-conventions) when naming your shape keys.

## Removing Drivers

To remove an RBF driver simply click the **-** button next to the list of drivers. The data properties related to the RBF driver and the drivers it is managing internally will be removed along with the RBF driver itself.
