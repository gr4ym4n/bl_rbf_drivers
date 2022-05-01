---
title: Getting Started
menuTitle: Getting Started
description: 'Familiarize yourself with the basic process of setting up an RBF driver'
position: 101
category: Tutorials
fullscreen: true
---

## Introduction

In this tutorial we'll be creating a very simple RBF driver that controls the location of one bone using the location of another bone. It won't be very useful in itself, but it will illustrate to workflow of creating RBF drivers. Once you're done, keep the blend file open or save it somewhere because we'll expand on it in the next couple of tutorials.

## Setting The Scene

For this example we're going to use bone transforms for both the input and output of the RBF driver. It is possible to use a huge variety of objects, data types and properties in RBF drivers, but using bone transforms keeps things simple for our purposes. Go ahead and open up a new Blender scene and follow the steps below.

1. Delete the default Camera, Cube and Light objects so we have a nice clean scene to work with.
2. Add an **Armature** object
3. Tab into **Edit** mode and rename the bone to *Input*.
4. Add a second bone (or duplicate the existing one), move it 1 unit along the X axis and rename it *Output*
5. Enter **Pose** mode (we'll need to be in **Pose** mode rather than **Object** mode to move the bones around later on).

You should now have a scene that looks something like the image below.

## Setting Up The RBF Driver

As long as you have the addon [installed](/installation), you should be able to find the RBF Drivers pane of the **Object Properties** panel. At the moment we haven't got any RBF drivers for this object so the only thing you will see is an **Add** button.

To add a new RBF driver click the **Add** button and select *Generic* from the popup menu (we'll explain what the other options are in later tutorials). The RBF Drivers pane will now show the list of drivers with the one we just added selected at the top, and its various settings (**Interpolation**, **Inputs**, etc.) below. For the moment we'll ignore the **Interpolation** and skip to **Inputs**.

## Adding The Input

Now click the **+** button next to the list of **Inputs** and select **Location** from the popup menu to add a location input. For the moment we're just going to use the *Input* bone's X location, so let's select that now:

In the **Input** settings select the armature that we added to the scene as the **Target** object (it's probably just called *Armature*) and then select the *Input* bone in the **Target** bone field. Finally, select the **X** axis. The **Input** settings should correspond to the image below.

## Adding the Output

The process will be much the same for the output. Click the **+** button next to the list of **Outputs** and select **Location** from the popup menu. Select the armature object as the **Target** but this time set the *Output* bone as the bone. Finally, select the **X** axis. The **Output** settings should now look like the image below.

## Adding Poses

If you scroll down in the **RBF Drivers** panel you'll see the **Poses** list. At the moment there's just one pose in the list: [the *Rest* pose](/manual/poses#the-rest-pose). This pose was added automatically when you created the RBF driver, and for our purposes you can leave it as it is. We're going to add a second pose to complete the RBF driver.

Make sure the armature is in **Pose** mode and select the *Input* bone in the viewport, then move it 1 unit along the X axis. Now select the *Output* bone, but this time move it 2 units along the X axis. Now go back to the **RBF Drivers** panel and click the **+** button next to the **Poses** list to record that as a new pose. That's it, our RBF driver is ready to go, but there's one more little step before we can see it in action.

## Seeing It In Action

Our RBF driver is going to be driving the *Output* bone's X location, but to create our poses we needed to move the *Output* bone around, so by default the output isn't active. If you go back to the **Output** list, you'll notice a little checkbox next to the output we created earlier. Go ahead and click the checkbox to activate the output driver.

Now select the *Input* bone in the viewport and move it along the X axis between 0 and 1. You should now see the *Output* bone moving between 0 and 2 along its X axis (if not go back and check the steps above). Let's take a look at what's going on here.

The RBF driver has 2 poses for our *Input* and *Output* bones. The first one (*Rest*) was created for you, and the second (*Pose*) we defined ourselves. As we move the *Input* bone between its *Rest* state and its *Pose* state, the RBF driver is calculating a weight to give each of those poses, and then driving the *Output* bone's location based on those weights and its own *Rest* and *Pose* state.

For the moment we just have a simple linear relationship between 2 values and 2 poses, but the power and flexibility of RBF drivers comes with the fact that we can have as many inputs, outputs and poses as we like and the RBF driver will go ahead and interpolate them all for us. We'll look at this in further tutorials, but before doing that, you may want to keep your blend file open and move on to the next tutorial to have a look at [pose interpolation](/tutorials/pose-interpolation).