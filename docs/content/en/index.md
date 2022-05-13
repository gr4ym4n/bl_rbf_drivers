---
title: ''
menuTitle: 'About'
description: ''
position: 1
fullscreen: true
---

<img class="ml-auto mr-auto pb-8" width="80%" src="/svg/rbf-drivers-logo.svg" onerror="this.src='/img/rbf-drivers-logo.png'">

RBF Drivers brings the power and expressivity of radial basis function networks to Blender, enabling complex rigging and animation that would otherwise be difficult or even impossible with Blender's native tools.

<alert type="info">

#### What does RBF mean?

RBF stands for [Radial Basis Function](https://en.wikipedia.org/wiki/Radial_basis_function). **RBF Drivers** builds a [radial basis function network](https://en.wikipedia.org/wiki/Radial_basis_function_network) inside Blender's dependency graph. An RBF network is a kind of [neural network](https://en.wikipedia.org/wiki/Neural_network) that predicts output values based on input values and a set of training data.

</alert>

Fundamentally **RBF Drivers** let you animate any number of *output* values based on any number of *input* values. We do this by defining *poses*. Defining a pose is simply telling **RBF Drivers** that when *these* input values are like *this*, I want *those* output values to be like *that*. **RBF Drivers** does all the heavy lifting to make it happen. In contrast to setting up constraints and Blender's native drivers you dont need to define *how* something happens, just *what* happens.

RBF systems have been used to great effect in other popular 3D software packages for some time, and have become an indispensible tool for riggers and animators. RBF Drivers is an implementation of an RBF system designed from the ground up for Blender. The workflow is intuitive enough that relative beginners can get up and running quickly, and the features are extensive enough to offer more experienced users full control.

## Features

* **Intuitive workflow**  
  Set your inputs and outputs, add some poses, and your good to go. Behind the scenes the addon builds and manages the neural network while exposing a straightforward process.
* **Reduced complexity**  
  RBF drivers can often replace multiple constraints and long driver chains with one simple interface, allowing riggers and animators to achieve great results quickly and stay in the flow.
* **Exceptional control**  
  Complete control over interpolation curves along with animatable influence on individual outputs and poses as well as per-pose interpolation options offer a very high degree of control for advanced use-cases.
* **Excellent performance**  
  RBF Drivers has been carefully designed such that all runtime calculations are performed in native C by Blender's dependency graph.
* **Fully scriptable**  
  A comprehensive python API allows RBF drivers to be built and configured entirely from script.
* **No strings attached**  
  Because RBF Drivers builds on Blender's native toolset, you're free to send your creations down the pipeline, share them with others or even sell them online. Once they're set up there is no requirement for the addon to be installed for the RBF drivers to keep working

## Documentation



## Support

* [Issues](https://github.com/jamesvsnowden/bl_rbf_drivers/issues)
* [Discussion](https://github.com/jamesvsnowden/bl_rbf_drivers/discussions)