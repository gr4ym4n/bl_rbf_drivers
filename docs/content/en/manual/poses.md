---
title: Poses
menuTitle: Poses
description: 'Familiarize yourself with the basic process and options when setting up an RBF driver'
position: 205
category: Manual
fullscreen: true
---

## The Rest Pose

All RBF drivers need at least one pose to function. By default it's called the *Rest* pose and it's created automatically for you when you add a new RBF driver. You'll find it at the top of the **Poses** list. There's nothing inherently special about this pose and you can treat is just like any other, but it's important to note that its input and output values are set to sensible defaults that in some cases you will want to change.

## Adding Poses

## Removing Poses

## Updating Poses

## Influence

## Interpolation

By default, each pose will use the RBF driver's interpolation settings. It is however possible to override the interpolation on a per-pose basis.

To override the driver's interpolation for a pose, select that pose in the list of poses and check the **Override** option in the pose settings. You can then adjust the interpolation for that pose without affecting other poses.

## Radius

Each pose has a **radius**. The actual value of the radius is calculated by RBF drivers according to the distance to the nearest neighboring pose. The radii for each of the poses in our simple example is illustrated in the image below.

By changing the **radius** of a pose using the slider, you can adjust when and by how much the pose is activated during interpolation. In the animations below you can see the effect of increasing the radius of our first pose, and reducing the radius of our second pose.

## Editing Pose Values