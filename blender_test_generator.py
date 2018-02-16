"""
This script takes an OBJ file and renders it to a jpg file using Cycles.

Textures are expected to be jpg files in the same folder as the OBJ file. They
should also have the same name for diffuse textures, and use suffixes for other
maps (ao, roughness, etc.).

Usage (command line):
    $ blender -b -P blender_test_generator.py

Requires:
    - Blender 2.79
    - The "Import-Export: Wavefront OBJ" addon enabled

"""

import os
import bpy


class Asset():

    def __init__(self, path):
        # Import OBJ file
        # Build material
        pass

    def make_material(self):
        pass


def path(*paths):
    """Return a  relative path from the script."""

    if bpy.app.background:
        base = os.path.dirname(__file__)
    else:
        base = os.path.dirname(bpy.path.abspath('//../'))

    return os.path.join(base, *paths)


def setup_scene(scene):
    """Setup world and lighting for the scene."""
    pass


def setup_render(scene):
    """Setup rendering settings."""

    scene.render.engine = 'CYCLES'
    scene.render.resolution_percentage = 100


def setup_compositing(scene):
    """Setup compositing nodes."""


if __name__ == "__main__":
    pass
