---
title: Pose Interpolation
menuTitle: Pose Interpolation
description: 'Changing RBF driver interpolation settings'
position: 104
category: Tutorials
fullscreen: true
---

## Introduction

In the [previous tutorial](/tutorials/getting-started) we set up a very simple RBF driver that moves an *Output* bone based on the location of an *Input* bone. Before we start handling some more advanced setups, we're going to use that setup to illustrate some of the [interpolation](/manual/interpolation) options available in **RBF Drivers**.

<alert type="warning">

This tutorial follows on directly from [**Getting Started**](/tutorials/getting-started). If you haven't done so already, you'll probably want to go back and complete that first. If you want to skip that tutorial (not recommended) or no longer have the blend file, you can download it [here](/blend/getting_started.blend)

</alert>

## Linear

Let's take another quick look at our scene. We've got an *Output* bone that moves along the X axis based on the location of an *Input* bone. For the time being the movement is linear because that's the default interpolation. The animation below demonstrates this with ghosted bones to mark the two poses we defined, along with a graph to illustrate the linear interpolation being used to interpolate between the two poses.

## Presets

If you look at the **Interpolation** panel directly underneath the list of **RBF Drivers**, you'll see a dropdown menu above the graph view where you can select the interpolation type. Try selecting a smoother interpolation preset from the dropdown menu, something like **Quadratic** or **Quintic**. If you now move the *Input* bone between 0 and 1 along the X axis, you'll see the movement of the *Output* is modified according to the interpolation setting. The animations below illustrate the effect of a few of the interpolation presets.

## Custom Curves

The preset interpolation curves will be sufficient for most needs, but if you prefer you can also define your own interpolation curve by selecting **Curve** from the dropdown menu. This allows you to edit the curve in the graph view. The animation below illustrates a custom interpolation curve.

## Next Steps

In this tutorial we've covered the basics of RBF driver interpolation. There are some more advanced options available for particular use cases that are covered in the [interpolation](/manual/interpolation) section of the manual, but for the moment keep your blend file open and continue to the next tutorial where we'll see some of the power of RBF drivers as we expand our RBF driver to include more inputs, outputs and poses.
