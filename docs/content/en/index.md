---
title: 'Introduction'
description: ''
position: 1
fullscreen: true
---

To understand RBF drivers, it's helpful to first take a look at Blender's native drivers so that we can see how RBF drivers are different, and what makes them so powerful.

## Blender Drivers

On a basic level, a driver allows you to control the value of *one* property (the *driven* property) using the value of one or more other properties (the *driving* properties). This makes them somewhat similar to some of Blender's constraints, but whereas constraints set up predefined relationships between properties, drivers offer much more flexibility in defining how the *driven* property is affected by the *driving* properties.

Let's look at a simple use-case to illustrate how Blender's native drivers can be used to fix a common problem in character rigging. The animation below shows a basic arm rig that doesn't deform the mesh very well during flexion of the forearm: the elbow doesn't hold its volume, the mesh breaks down on the inside of the elbow, and we don't see the contraction of the biceps.

There are a myriad of ways to fix these problems, but for our purposes we're going to stick with adding shape keys to the character mesh. We'll create shape keys for the elbow, inner arm and bicep, and set up drivers to drive their values based on the rotation of the forearm.

So far so good, but we'd like to take things a bit further and have the forearm and bicep deform properly during forearm pronation as well as flexion. We can create shape keys for those too, but this is where things start to get very tricky because somehow we're going to need to mix the values of *multiple* shape keys together based on *multiple* forearm rotation values. We could achieve this by using multiple drivers, helper bones or some nifty math, but it's going to be painful to set up and very unpleasant to work with further down the line.

What we want is a quick and simple way to set up a relationship between multiple *driving* properties and multiple *driven* properties. We can do this with RBF drivers.

## RBF Drivers

Much like Blender's native drivers, with RBF drivers you select what properties you want to act as *driving* properties (known as *inputs* in RBF drivers) but unlike Blender's drivers, you're not limited to a single *driven* property (known as a *outputs* in RBF drivers), and you don't need to define a mathematical relationship between those *inputs* and *outputs*

and what you  you want to act as *driven* properties (known as *outputs*). But instead of defining a fixed 

You then simply need to define *poses*, which tell the
RBF driver that when the *inputs* are like *this*, the *outputs* should be like *that*.

In our example, we just need to pose the forearm, set the shape key values so that 

