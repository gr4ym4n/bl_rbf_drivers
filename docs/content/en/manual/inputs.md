---
title: Inputs
menuTitle: Inputs
description: 'Familiarize yourself with the basic process and options when setting up an RBF driver'
position: 203
category: Manual
fullscreen: false
---

## Adding Inputs

![Add Input](/bl_rbf_drivers/img/manual-inputs-add-input.jpg)

To add an input, click the **+** button next to the list of inputs. You can then select the type of input you want to add.

<alert type="info">

There is no limit imposed on the number of inputs you can add, but to avoid unnecessary performance costs it is best to use only the inputs you need. For example transform inputs ([Location](#location), [Rotation](#rotation) and [Scale](#scale)) will often produce the same results whether all channels are enabled or not, but if you're only interested in one or two channels it is better to only enable those channels.

</alert>

## Input Types

There are a number of different input types tailored to particular needs, as well as a [user-defined](#user-defined) type that is very flexible but can be more difficult to set up correctly. The available input types are detailed below.

### Location

The **Location** input type reads the translation values of an object or pose bone.

![Location Input](/bl_rbf_drivers/img/manual-inputs-location.jpg)

#### Target

You can select any object as the location input target. Selecting an armature object will reveal a second field where you can optionally select a pose bone target.

#### Channels

* **Transform Space**  
  By default the **Location** input will read values from the input target in its local coordinate space. This is usually what you will want, but you can also use transform or world spaces to suits various strategies.

  <alert type="info">

  The various coordinate spaces used within Blender can be the cause of some confusion. If you're not sure what they mean you can read up on them on the [Blender manual page](https://docs.blender.org/manual/en/latest/editors/3dview/controls/orientation.html). RBF drivers offer the same transform spaces as Blender's native drivers.

  </alert>

* **Axes**  
  Toggle which axis or axes of the target's location you want to use as input to the RBF Driver.

### Rotation

The **Rotation** input type reads the rotation values of an object or pose bone.

![Rotation Input](/bl_rbf_drivers/img/manual-inputs-rotation.jpg)

#### Target

You can select any object as the rotation input target. Selecting an armature object will reveal a second field where you can optionally select a pose bone target.

#### Channels

<table class="table-fixed">

<tr>
<td style="width:40%;"><img alt="Euler rotation input mode" src="/bl_rbf_drivers/img/manual-inputs-rotation-euler.jpg"></td>
<td style="width:50%;">

**Euler**  
Use the euler rotation values of the input target. You can additionally select the rotation order, coordinate space and which rotation channels to use.

</td>
</tr>

<tr>
<td><img alt="Quaternion rotation input mode" src="/bl_rbf_drivers/img/manual-inputs-rotation-quaternion.jpg"></td>
<td>

**Quaternion**  
Use the quaternion rotation values of the input target. You can also select the coordinate space to take the values from.

</td>
</tr>

<tr>
<td><img alt="Swing rotation input mode" src="/bl_rbf_drivers/img/manual-inputs-rotation-swing.jpg"></td>
<td>

**Swing**  
Decompose the input target rotation values and extract swing rotation values. You can select which axis of the input target the swing should be on and the coordinate space to take the values from.

</td>
</tr>

<tr>
<td><img alt="Twist rotation input mode" src="/bl_rbf_drivers/img/manual-inputs-rotation-twist.jpg"></td>
<td>

**Twist**  
Decompose the input target rotation values and extract the twist rotation angle around the given axis. Additional options are the selection of the axis of the input target the twist should be around and the coordinate space to take the values from.

</td>
</tr>

</table>

<alert type="info">

Swing/twist rotations can be particularly useful with RBF drivers. If you're not familiar with them you can read more about them in [the relevant blender manual page](https://docs.blender.org/manual/en/latest/animation/drivers/drivers_panel.html#rotation-channel-modes).

</alert>

<alert type="info">

The various coordinate spaces used within Blender can be the cause of some confusion. If you're not sure what they mean you can read up on them on the [Blender manual page](https://docs.blender.org/manual/en/latest/editors/3dview/controls/orientation.html). RBF drivers offer the same transform spaces as Blender's native drivers.

</alert>

### Scale

The **Scale** input type reads the scale values of an object or pose bone.

![Scale Input](/bl_rbf_drivers/img/manual-inputs-scale.jpg)

#### Target

You can select any object as the scale input target. Selecting an armature object will reveal a second field where you can optionally select a pose bone target.

* **Transform Space**  
  By default the **Scale** input will read values from the input target in its local coordinate space. This is usually what you will want, but you can also use transform or world spaces to suits various strategies.

  <alert type="info">

  The various coordinate spaces used within Blender can be the cause of some confusion. If you're not sure what they mean you can read up on them on the [Blender manual page](https://docs.blender.org/manual/en/latest/editors/3dview/controls/orientation.html). RBF drivers offer the same transform spaces as Blender's native drivers.

  </alert>

* **Axes**  
  Toggle which axis or axes of the target's scale you want to use as input to the RBF Driver.

### Rotational Difference

The **Rotational Difference** input type reads the angle between two objects of pose bones.

![Rotational Difference Input](/bl_rbf_drivers/img/manual-inputs-rotational-difference.jpg)

#### Targets

You can select any object as a rotational difference input target. Selecting an armature object will reveal a second field where you can optionally select a pose bone target.

### Distance

The **Distance** input type reads the distance between two objects or pose bones

![Distance Input](/bl_rbf_drivers/img/manual-inputs-distance.jpg)

#### Targets

You can select any object as a distance input target. Selecting an armature object will reveal a second field where you can optionally select a pose bone target.

<alert type="info">

The various coordinate spaces used within Blender can be the cause of some confusion. If you're not sure what they mean you can read up on them on the [Blender manual page](https://docs.blender.org/manual/en/latest/editors/3dview/controls/orientation.html). RBF drivers offer the same transform spaces as Blender's native drivers.

</alert>

### Shape Keys

The **Shape Keys** input type reads the values of one or more shape keys.

![Shape Keys Input](/bl_rbf_drivers/img/manual-inputs-shape-key.jpg)

### User-Defined

The **User-Defined** input type allows you to define what properties of Blender's data blocks to read, and how the RBF driver should treat those properties.

![User-Defined Input](/bl_rbf_drivers/img/manual-inputs-user-defined.jpg)

#### Type

For **User-Defined** inputs there are three sub-types available in the **Type** dropdown menu: **Float**, **Angle** and **Quaternion**. RBF Drivers will treat the input values differently depending on this setting. You should use whichever value best describes the input data type.

<alert type="info">

If you have selected **Quaternion** as the input data type, then as long as the variables  you have defined describe a quaternion value (i.e. there are 4 variables), then you will also have the option to **Extract Swing Rotation** around a given axis. This will behave in the same way as a **Swing** rotation input, but allows you to construct an arbitrary quaternion rotation yourself.

</alert>

#### Variables

If you have used Blender's native drivers then the variables section should be familiar to you as they offer almost exactly the same options.

<table class="table-fixed">

<tr>
<td style="width:40%;"><img alt="Single Property Input Variable" src="/bl_rbf_drivers/img/manual-inputs-variable-single-prop.jpg"></td>
<td style="width:50%;">

**Single Property**  
Retrieves the value of an RBF property, specified by a data-block reference and a path string.

</td>
</tr>

<tr>
<td><img alt="Transform Input Variable" src="/bl_rbf_drivers/img/manual-inputs-variable-transforms.jpg"></td>
<td>

**Transform Channel**  
Retrieves the value of a Transform channel from an object or bone.

</td>
</tr>

<tr>
<td><img alt="Rotational Diffference Input Variable" src="/bl_rbf_drivers/img/manual-inputs-variable-rotational-difference.jpg"></td>
<td>

**Rotational Difference**  
Provides the value of the rotational difference between two objects or bones, in radians.

</td>
</tr>

<tr>
<td><img alt="Distance Input Variable" src="/bl_rbf_drivers/img/manual-inputs-variable-distance.jpg"></td>
<td>

**Distance**  
Provides the value of the distance between two objects or bones.

</td>
</tr>

</table>

<alert type="info">

The number of variables you can add to a single input is limited to being 16. If you need more variables than that you can create another input and add the additional variables there. For the purposes of RBF Drivers there is no difference between 1 input with 8 variables, 2 inputs with 4 variables each, or 8 inputs that each have a single variable.

</alert>

## Decomposing Inputs

![Decompose input variables action](/bl_rbf_drivers/img/manual-inputs-decompose.jpg)

If you've set up an input of any type other than user-defined, then the **Decompose Input Variables** action will be available to you from the dropdown actions menu to the right of the inputs list. Invoking the action will convert the input to a [**User-Defined**](#user-defined) input and its channels to [input variables](#variables).

<alert type="warning">

While you can undo the process if you change your mind, you cannot later convert a **User-Defined** input to any other type of input, so use with care!

</alert>

## Removing Inputs

![Remove input button](/bl_rbf_drivers/img/manual-inputs-remove.jpg)

To remove an input, simply click on the **Remove Input** (**-**) button next to the list of inputs.
