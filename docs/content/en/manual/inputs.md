---
title: Inputs
menuTitle: Inputs
description: 'Familiarize yourself with the basic process and options when setting up an RBF driver'
position: 203
category: Manual
fullscreen: false
---

## Adding Inputs

![Add Input](/img/manual-inputs-add-input.jpg)

To add an input, click the **+** button next to the list of inputs. You can then select the type of input you want to add.

<alert type="info">

There is no limit imposed on the number of inputs you can add, but to avoid unnecessary performance costs it is best to use only the inputs you need. For example transform inputs ([Location](#location), [Rotation](#rotation) and [Scale](#scale)) will often produce the same results whether all channels are enabled or not, but if you're only interested in one or two channels it is better to only enable those channels.

</alert>

## Input Types

There are a number of different input types tailored to particular needs, as well as a [user-defined](#user-defined) type that is very flexible but can be more difficult to set up correctly. The available input types are detailed below.

### Location

The **Location** input type reads the translation values of an object or pose bone.

![Location Input](/img/manual-inputs-location.jpg)

#### Target

You can select any object as the location input target. Selecting an armature object will reveal a second field where you can optionally select a pose bone target.

#### Channels

By default the **Location** input will read values from the input target in its local coordinate space. This is usually what you will want, but you can also use transform or world spaces to suits various strategies.

<alert type="info">

The various coordinate spaces used within Blender can be the cause of some confusion. If you're not sure what they mean you can read up on them on the [Blender manual page](https://docs.blender.org/manual/en/latest/editors/3dview/controls/orientation.html). RBF drivers offer the same transform spaces as Blender's native drivers.

</alert>

The **Channels** settings allow you to select which transform channels you want to use as input to the RBF driver, and what transform space 

### Rotation

The **Rotation** input type reads the rotation values of an object or pose bone.

![Rotation Input](/img/manual-inputs-rotation.jpg)

#### Target

You can select any object as the rotation input target. Selecting an armature object will reveal a second field where you can optionally select a pose bone target.

#### Channels

The channel options allow you to select which rotation channels should be used as inputs to the RBF driver.

##### Rotation Modes

There are several rotation modes to choose from. The rotation mode does not need to match the rotation mode of the target.

###### Euler

Select **Euler** from the dropdown menu to use the euler rotation channels. With **Euler** selected you can also select the rotation order.

<alert type="warning">

Euler rotations are easy to understand but their use comes with some caveats. They are of course prone to [gimbal lock](https://en.wikipedia.org/wiki/Gimbal_lock) which can present issues during animation, but they can also present issues for the calculations that RBF drivers performs. If you're using more than two rotation axes as input to the RBF driver it is suggested that you use an alternative rotation mode.

</alert>

###### Quaternion

Select **Quaternion** from the dropdown menu to use the quaternion rotation channels of the input target. The **Use Logarithmic Map** checkbox 

<alert type="info">

RBF drivers will always use all rotation channels when **Quaternion** is selected as the components of a quaternion are not particularly descriptive in isolation. If for some reason you want to isolate one or more components of a quaternion rotation you can nevertheless achieve this using the [**User-Defined**](#user-defined) input type.

</alert>

###### Swing

If the **Swing** option is selected, the RBF driver will decompose the input target's rotation and use only the swing rotation values. This can be useful if you only want to take into account the direction an object or bone is pointing in.

By default the **Rotation** input will read values from the input target in its local coordinate space. This is usually what you will want, but you can also use transform or world spaces to suits various strategies.

<alert type="info">

The various coordinate spaces used within Blender can be the cause of some confusion. If you're not sure what they mean you can read up on them on the [Blender manual page](https://docs.blender.org/manual/en/latest/editors/3dview/controls/orientation.html). RBF drivers offer the same transform spaces as Blender's native drivers.

</alert>

### Scale

The **Scale** input type reads the scale values of an object or pose bone.

![Scale Input](/img/manual-inputs-scale.jpg)

#### Target

You can select any object as the scale input target. Selecting an armature object will reveal a second field where you can optionally select a pose bone target.

<alert type="info">

The various coordinate spaces used within Blender can be the cause of some confusion. If you're not sure what they mean you can read up on them on the [Blender manual page](https://docs.blender.org/manual/en/latest/editors/3dview/controls/orientation.html). RBF drivers offer the same transform spaces as Blender's native drivers.

</alert>

### Rotational Difference

The **Rotational Difference** input type reads the angle between two objects of pose bones.

![Rotational Difference Input](/img/manual-inputs-rotational-difference.jpg)

#### Targets

You can select any object as a rotational difference input target. Selecting an armature object will reveal a second field where you can optionally select a pose bone target.

### Distance

The **Distance** input type reads the distance between two objects or pose bones

![Distance Input](/img/manual-inputs-distance.jpg)

#### Targets

You can select any object as a distance input target. Selecting an armature object will reveal a second field where you can optionally select a pose bone target.

<alert type="info">

The various coordinate spaces used within Blender can be the cause of some confusion. If you're not sure what they mean you can read up on them on the [Blender manual page](https://docs.blender.org/manual/en/latest/editors/3dview/controls/orientation.html). RBF drivers offer the same transform spaces as Blender's native drivers.

</alert>

### Shape Keys

The **Shape Keys** input type reads the values of one or more shape keys.

![Shape Keys Input](/img/manual-inputs-shape-key.jpg)

### User-Defined

The **User-Defined** input type allows you to define what properties of Blender's data blocks to read, and how the RBF driver should treat those properties.

![User-Defined Input](/img/manual-inputs-user-defined.jpg)

## Decomposing Inputs

## Removing Inputs