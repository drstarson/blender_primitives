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

    def __init__(self, filepath):

        # Import OBJ file
        self.filepath = filepath
        print('- Importing OBJ file: {}'.format(filepath))

        bpy.ops.import_scene.obj(filepath=filepath)
        self.object = bpy.context.selected_objects[0]
        self.name = os.path.splitext(os.path.basename(filepath))[0]

        self.make_material()

    def make_material(self):

        # Make a new material
        self.material = bpy.data.materials.new(self.name)
        self.material.use_nodes = True
        self.mat_nodes = self.material.node_tree.nodes
        self.mat_links = self.material.node_tree.links

        self.object.data.materials[0] = self.material

        # Switch diffuse to principled shader
        location = self.mat_nodes['Diffuse BSDF'].location.copy()
        output = self.mat_nodes['Material Output']
        self.mat_nodes.remove(self.mat_nodes['Diffuse BSDF'])
        principled = self.mat_nodes.new('ShaderNodeBsdfPrincipled')
        principled.location = location

        self.mat_links.new(principled.outputs['BSDF'],
                           output.inputs['Surface'])


def path(*paths):
    """Return a  relative path from the script."""

    if bpy.app.background:
        base = os.path.dirname(__file__)
    else:
        base = os.path.dirname(bpy.path.abspath('//'))

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

    scene.use_nodes = True


if __name__ == "__main__":

    filepath = path('assets', 'objects', 'pumpkin', 'pumpkin.obj')
    scene = bpy.context.scene

    setup_render(scene)
    setup_compositing(scene)

    try:
        pumpkin = Asset(filepath)
    except (RuntimeError, FileNotFoundError):
        print('[!] Can\'t find file {}!'.format(filepath))
