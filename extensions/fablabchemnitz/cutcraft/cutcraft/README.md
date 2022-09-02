# cut-craft


## Python package

Note that this package is written for Python 3, however requires Python 2 compatibility for Inkscape integration.

The `cutcraft` package contains components in the following categories:

| Folder    | Description                                          |
| --------- | ---------------------------------------------------- |
| core      | Core components (point, line etc).                   |
| platforms | Platforms used to construct shapes (circular etc).   |
| shapes    | Fundamental 3D shapes (cylinder, cone, sphere etc).  |
| supports  | Vertical supports to hold the shape levels apart.    |


## Core

| Module    | Description                                                                 |
| --------- | --------------------------------------------------------------------------- |
| point     | A 2D point with `x` and `y` coordinates.                                    |
| rectangle | Two `point`s defining topleft and bottom right for a rectangle.             |
| trace     | An ordered collection of `point`s.                                          |
| part      | A collection of one or more `trace`s.                                       |
| line      | A type of `trace` with two `point`s defining the start and end of the line. |
| circle    | A type of `trace` with `point`s defining a circle.                          |
| neopixel  | A type of `trace` with the `point`s defining a cutout suitable to fit a variety of [NeoPixels](https://www.adafruit.com/category/168). |


## Shapes

| Module   | Description                            |
| -------- | -------------------------------------- |
| shape    | The core 3D functionality for a shape. |
| cone     | A cone `shape`.                        |
| cylinder | A cylinder `shape`.                    |
| sphere   | A 3D spherical `shape`.                |

> Note that the fundamental `shape`s listed above can be used flexibly considering the number of `circle` segments can be specified.  For example a `cone` with 4 segments becomes a **pyramid**, and a `cylinder` with 4 segments becomes a **cube**.


## Supports

| Module   | Description                                         |
| -------- | --------------------------------------------------- |
| support  | The core support structure functionality.           |
| pier     | A pier like `support` to hold `shape` levels apart. |
| face     | A solid face to `support` `shape` levels.           |


## Python 2 vs 3 Compatibility

The initial aim was to develop only for Python 3, however [Inkscape](https://inkscape.org) currently uses Python 2 as the default interpreter for extensions.  As a result, the following should be noted while reviewing the code:

1) The calls to `super()` are written in a way that works with both versions of Python.
2) The `math.isclose()` function is not available in Python 2 so a local version has been created in [util.py](util.py).
