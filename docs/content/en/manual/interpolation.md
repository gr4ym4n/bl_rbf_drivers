---
title: Interpolation
menuTitle: Interpolation
description: 'Familiarize yourself with the basic process and options when setting up an RBF driver'
position: 202
category: Manual
fullscreen: false
---

An RBF driver's interpolation settings adjust how the [output](/manual/outputs) values transition between poses. Using the interpolation you can precisely control how and when the RBF driver's [outputs](/manual/outputs) are activated as the [inputs](/manual/inputs) change.

![Interpolation panel](/img/manual-interpolation-panel.jpg)

We can use a very simple RBF driver to illustrate the effect of the interpolation. In the examples below we're using the location of an "Input" bone to drive the location of an "Output" bone. Using a *linear* interpolation (the default), the "Output" bone moves in lockstep with the "Input" bone.

<img src="/img/manual-interpolation-linear.gif" alt="Linear interpolation" width="100%">

If we change the interpolation to "Cubic", then the acceleration of the "Output" bone is no longer constant; it *eases* in and out according to the interpolation curve.

<img src="/img/manual-interpolation-cubic.gif" alt="Cubic interpolation" width="100%">

## Driver Interpolation

The driver's main **Interpolation** panel is used to set the default interpolation for all of that driver's poses. There are a number of preset interpolation types to choose from, as well as a [**Custom Curve**](#custom-curve) option to define your own interpolation curve.

### Linear (default)

A linear interpolation does not result in any adjustment of the output values. They are driven directly according to the [pose weights](/manual/poses#weight).

<img src="/img/manual-interpolation-linear.gif" alt="Linear interpolation" width="100%">

### Sinusoidal

<img src="/img/manual-interpolation-sinusoidal.gif" alt="Sinusoidal interpolation" width="100%">

### Quadratic

<img src="/img/manual-interpolation-quadratic.gif" alt="Quadratic interpolation" width="100%">

### Cubic

<img src="/img/manual-interpolation-cubic.gif" alt="Cubic interpolation" width="100%">

### Quartic

<img src="/img/manual-interpolation-quartic.gif" alt="Quartic interpolation" width="100%">

### Quintic

<img src="/img/manual-interpolation-quintic.gif" alt="Quintic interpolation" width="100%">

### Custom Curve

With a custom curve you are free to define any interpolation curve you wish. After selecting the **Custom Curve** option you can use the [curve editor](#curve-editor) to add, remove and adjust control points.

<img src="/img/manual-interpolation-custom.gif" alt="Custom interpolation" width="100%">

## Curve Editor

The Curve editor is a slightly limited version of the curve editor present in the Blender's node editor. 

![Interpolation curve editor](/img/manual-interpolation-curve-editor.jpg)

### Editing Control Points

Left-click anywhere along the curve to select or add a new control point, then drag to set its position. To remove one (or more) control points, first select the control point or points and the click the **X** button above curve editor graph.

### Setting Control Point Handles

Each control point has a handle type setting which can be changed using the options above the curve graph display. You can choose from **Auto**, **Auto-Clamped** or **Vector** handle types.

<alert type="info">

The curve displayed in the curve editor will only be editable if you have selected the [**Custom Curve**](#custom-curve) option as the interpolation type.

</alert>

## Pose Interpolation

By default, each pose will use the RBF driver's interpolation settings. It is however possible to override the interpolation on a per-pose basis. For further details you can read about pose interpolation [here](/manual/poses/interpolation)
