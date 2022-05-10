---
title: Frequently Asked Questions
menuTitle: FAQ
description: 'Familiarize yourself with the basic process and options when setting up an RBF driver'
position: 207
category: Manual
fullscreen: true
---

#### What does RBF mean?

RBF stands for [radial basis function](https://en.wikipedia.org/wiki/Radial_basis_function), which is a function that depends on the distance between an input value and some other sampled data point. RBF Drivers uses Blender's native drivers to build an [RBF network](https://en.wikipedia.org/wiki/Radial_basis_function_network), which is a type of neural network that uses radial basis functions for activation.

#### Which Object should I add an RBF driver to?

In many situations, you will have an RBF driver with inputs coming from one data target (such as an armature bone) and outputs on another data target (such as shape keys). You are free to create the RBF driver on the object where the inputs are found, the object where the outputs are found, or even an entirely separate object. You should choose whatever makes sense to you ([with some caveats](#i-think-rbf-drivers-is-causing-a-circular-dependency-what-can-i-do)) but as a general rule of thumb its preferred that the RBF driver is added to the object where the outputs are to be found.

#### I think RBF Drivers is causing a circular dependency. What can I do?

Blender's [dependency graph](https://wiki.blender.org/wiki/Source/Depsgraph) went through some much needed improvements back in version 2.8, but circular dependencies are nevertheless still very much possible. RBF drivers are carefully designed not to produce circular dependencies as long as the normal rules governing Blender's dependency graph are adhered to, but it doesn't prevent you from creating them. If you create an RBF driver that uses the location of an object to drive itself, then obviously you've created a circular dependency. If you're sure that it's the RBF driver itself that's causing the problem then [file an bug report](/support), but please take a little time to verify your setup before you do.

#### What are the extra custom properties RBF Drivers is creating?

To run the [RBF network](#what-does-rbf-mean) that RBF Drivers builds internally, we need to store and reference quite a lot of data. We could just hide this away in a proprietary data structure, but that would mean that if you share your work with other users that don't have the addon installed, the drivers wouldn't work. Instead we opted to use Blender's custom properties as a storage medium, and reference them from the drivers. You shouldn't ever need to edit or [delete](#can-i-delete-the-custom-properties-created-by-rbf-drivers) these properties yourself. If you do things will likely go wrong.

#### Can I delete the custom properties created by RBF Drivers?

The short answer is no. In fact RBF drivers will under normal circumstances be able to recreate properties that have been deleted without any data loss, but it's not recommended that you edit or delete them yourself.

#### Why is my output target snapping back to it's rest pose?

Each [input](/manual/inputs) [pose](/manual/poses) has a *radius* that is calculated internally as the distance to its nearest neighbor (though you can adjust it using the [radius](/manual/poses#radius) setting for the pose). If the input target values are outside of all the pose radii, the RBF driver can't calculate a weight for any of the poses and output targets will snap back to their origins. The simple solution is to create a pose that covers the input target values.

#### Can I have more than one RBF driver with the same output?

No. RBF drivers use Blender's native drivers to drive the driven properties, and there can only be one driver per driven property. This is entirely logical as the driven property has no way of deciding which driver value is should use. If you want to drive a property based on the output of two RBF drivers, you will need to use custom properties as the outputs for the RBF drivers and create your own driver to combine the output values. It is unlikely that you would want to do this, but if you're familiar with Blender's drivers it shouldn't be difficult and RBF drivers won't get in your way.

#### Where is my license key?

RBF Drivers - as with all Blender addons - is realeased under an open source GPL license. However, if you purchased the addon through any of our sales channels then we provide some extra support and services as a way of expressing our gratitude for supporting development.

You should have received a license key either with the sales receipt or shortly afterwards by email. If you haven't received a license key within 48 hours of your purchase please [get in touch](/support).
