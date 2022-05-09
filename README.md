
# RBF Drivers

RBF Drivers is an addon (plugin) for [Blender](https://www.blender.org/) that enables the use of [radial basis functions](https://en.wikipedia.org/wiki/Radial_basis_function) in rigging and animation workflows.

- [Gumroad](https://jamesvsnowden.gumroad.com/l/rbf-drivers)
- [Blender Market](https://blendermarket.com/products/rbf-drivers)
- [Artstation](https://www.artstation.com/a/2238325)
- Cubebrush (coming soon!)

## Features

### Fast & Intuitive Workflow

Solving rigging and animation issues often requires a complex spaghetti of constraints and drivers. RBF drivers offer a uniquely friendly way to achieve very complex or otherwise impossible results extremely quickly.

### Realtime & Performant

RBF Drivers has been carefully designed to have the minimum runtime cost. The drivers it creates all run within Blender's dependency graph and once set up do not require python. On even moderate systems you can expect to run hundreds of simultaneous RBF drivers without any perceptible performance cost. It's very unlikely that RBF Drivers will ever be the bottleneck.

### Built on native tools

RBF Drivers builds on Blender's native toolset, using Blender's built-in drivers and custom properties to construct a [radial basis function network](https://en.wikipedia.org/wiki/Radial_basis_function_network) that's not hidden in scripts and code. This has the important advantage that RBF systems built with RBF Drivers can be sent down the pipeline, shared with colleagues or freinds, or even sold without the end-user needing the addon to be installed in order for it to work.

### Flexibility

In contrast to version 1, RBF Drivers 2 allows almost any input and output to the system. You are no longer limited to using pose bones and transforms as inputs.