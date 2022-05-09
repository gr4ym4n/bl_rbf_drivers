---
title: Inputs
menuTitle: Inputs
description: 'Familiarize yourself with the basic process and options when setting up an RBF driver'
position: 203
category: Manual
fullscreen: false
---

## Adding Inputs

To add an input, click the **+** button next to the list of inputs. You can then select the type of input you want to add.

<alert type="info">

There is no limit imposed on the number of inputs you can add, but to avoid unnecessary performance costs it is best to use only the inputs you need. For example transform inputs ([Location](#location), [Rotation](#rotation) and [Scale](#scale)) will often produce the same results whether all channels are enabled or not, but if you're only interested in one or two channels it is better to only enable those channels.

</alert>

## Input Types

There are a number of different input types tailored to particular needs, as well as a [user-defined](#user-defined) type that is very flexible but can be more difficult to set up correctly.

### Location

The **Location** input type reads the translation values of an object or pose bone.

#### Target

You can select any object as the location input target. Selecting an armature object will reveal a second field where you can optionally select a pose bone target.

#### Channels

By default the **Location** input will read values from the input target in its local coordinate space. This is usually what you will want, but you can also use transform or world spaces to suits various strategies.

<alert type="info">

The various coordinate spaces used within Blender can be the cause of some confusion. If you're not sure what they mean you can read up on them on the [Blender manual page](https://docs.blender.org/manual/en/latest/editors/3dview/controls/orientation.html). RBF drivers offer the same transform spaces as Blender's native drivers.

</alert>

The **Channels** settings allow you to select which transform channels you want to use as input to the RBF driver, and what transform space 

### Rotation

<alert type="info">

The various coordinate spaces used within Blender can be the cause of some confusion. If you're not sure what they mean you can read up on them on the [Blender manual page](https://docs.blender.org/manual/en/latest/editors/3dview/controls/orientation.html). RBF drivers offer the same transform spaces as Blender's native drivers.

</alert>

### Scale

<alert type="info">

The various coordinate spaces used within Blender can be the cause of some confusion. If you're not sure what they mean you can read up on them on the [Blender manual page](https://docs.blender.org/manual/en/latest/editors/3dview/controls/orientation.html). RBF drivers offer the same transform spaces as Blender's native drivers.

</alert>

### Rotational Difference

### Distance

<alert type="info">

The various coordinate spaces used within Blender can be the cause of some confusion. If you're not sure what they mean you can read up on them on the [Blender manual page](https://docs.blender.org/manual/en/latest/editors/3dview/controls/orientation.html). RBF drivers offer the same transform spaces as Blender's native drivers.

</alert>

### Shape Keys

### User-Defined

## Decomposing Inputs

## Removing Inputs