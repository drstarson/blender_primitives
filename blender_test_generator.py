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
import glob
import bpy


class Asset():
    """Represents an imported object and it's material and textures."""

    def __init__(self, filepath):
        """Import OBJ file and create asset object."""

        self.filepath = filepath
        print('- Importing OBJ file: {}'.format(filepath))

        bpy.ops.import_scene.obj(filepath=filepath)
        self.object = bpy.context.selected_objects[0]
        self.name = os.path.splitext(os.path.basename(filepath))[0]

        # Make material
        self.make_material()
        self.set_textures()

    def make_material(self):
        """Create a new emtpy material using the principled shader."""

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

        # NOTE: Hardcoded, but this should come from a map
        principled.inputs['Subsurface'].default_value = 0.1

        self.mat_links.new(principled.outputs['BSDF'],
                           output.inputs['Surface'])

        self.principled = principled

    def make_image_node(self, image_path):
        """Make an image node."""

        image = bpy.data.images.load(image_path, check_existing=False)
        node_image = self.mat_nodes.new(type='ShaderNodeTexImage')
        node_image.image = image

        return node_image

    def set_textures(self):
        """Find textures in the OBJ file's folder and add to material."""

        def map_type(texture):
            """Return type of texture by finding its suffix."""

            name = os.path.splitext((os.path.basename(texture)))[0].lower()
            suffix = name.partition('_')[2]

            return suffix or 'diffuse'

        # Find textures
        folder = os.path.dirname(self.filepath) + os.path.sep
        found_textures = glob.glob(folder + self.name + '*.jpg')

        if not any(found_textures):
            print('[!] No textures found!')
            return

        # Organize by type
        tex_types = [map_type(t) for t in found_textures]
        textures = dict(zip(tex_types, found_textures))

        print('Found textures {}'.format(textures))

        # Make diffuse image node
        diffuse = self.make_image_node(textures['diffuse'])
        diffuse.location = self.principled.location
        diffuse.location.x -= 750
        diffuse.name = 'Diffuse Map'

        # Ambient Occlusion has to be mixed with the diffuse map
        if 'ao' in textures:
            ao = self.make_image_node(textures['ao'])
            ao.location = self.principled.location
            ao.location.x -= 500
            ao.name = 'Ambient Occlusion Map'

            mix = self.mat_nodes.new('ShaderNodeMixRGB')
            mix.name = 'Apply Ambient Occlusion'
            mix.blend_type = 'MULTIPLY'
            mix.location = self.principled.location
            mix.location.x -= 250
            mix.inputs['Fac'].default_value = 1

            self.mat_links.new(diffuse.outputs['Color'], mix.inputs['Color1'])
            self.mat_links.new(ao.outputs['Color'], mix.inputs['Color2'])
            self.mat_links.new(mix.outputs['Color'],
                               self.principled.inputs['Base Color'])

        # Otherwise, we can just plug the diffuse into the principled shader
        else:
            self.mat_links.new(diffuse.outputs['Color'],
                               self.principled.inputs['Base Color'])


def path(*paths):
    """Return a  relative path from the script."""

    if bpy.app.background:
        base = os.path.dirname(__file__)
    else:
        base = os.path.dirname(bpy.path.abspath('//'))

    return os.path.join(base, *paths)


def setup_scene(scene):
    """Setup world and lighting for the scene."""

    # Setup test table
    bpy.ops.mesh.primitive_plane_add(radius=5)
    plane = bpy.context.selected_objects[0]

    # Setup camera
    if not scene.camera:
        camera = bpy.data.cameras.new("Camera")
        camera_obj = bpy.data.objects.new("Camera", camera)
        scene.objects.link(camera_obj)
        scene.camera = camera_obj

    scene.camera.location = (-1.23, -2.36, 2.18)
    scene.camera.rotation_euler = (1, 0, -0.5)

    # Setup world lighting
    scene.world.use_nodes = True
    world_nodes = scene.world.node_tree.nodes
    world_links = scene.world.node_tree.links

    env_map = world_nodes.new('ShaderNodeTexEnvironment')
    env_map.location = world_nodes['Background'].location
    env_map.location.x -= 250

    if False:
        world_links.new(env_map.outputs['Color'],
                        world_nodes['Background'].inputs['Color'])


def setup_render(scene):
    """Setup rendering settings."""

    scene.render.engine = 'CYCLES'
    scene.render.resolution_percentage = 100

    # This value will depend on the HDRi/lighting and the amount of SSS
    # used. More complicated lighting or higher SSS will take more samples
    # to produce a clean render
    scene.cycles.samples = 250
    scene.cycles.preview_samples = 250

    scene.view_settings.view_transform = 'Filmic'
    scene.view_settings.look = 'Filmic - Base Contrast'

    scene.render.filepath = '//render.jpg'
    scene.render.image_settings.file_format = 'JPEG'
    scene.render.image_settings.color_mode = 'RGB'


def setup_compositing(scene):
    """Setup compositing nodes."""

    scene.use_nodes = True
    comp_nodes = scene.node_tree.nodes
    comp_links = scene.node_tree.links

    lens_distortion = comp_nodes.new('CompositorNodeLensdist')
    lens_distortion.inputs['Dispersion'].default_value = 0.001

    comp_links.new(comp_nodes['Render Layers'].outputs['Image'],
                   lens_distortion.inputs['Image'])

    comp_links.new(lens_distortion.outputs['Image'],
                   comp_nodes['Composite'].inputs['Image'])


if __name__ == "__main__":

    filepath = path('assets', 'objects', 'pumpkin', 'pumpkin.obj')
    scene = bpy.context.scene

    setup_scene(scene)
    setup_render(scene)
    setup_compositing(scene)

    try:
        pumpkin = Asset(filepath)
    except (RuntimeError, FileNotFoundError):
        print('[!] Can\'t find file {}!'.format(filepath))

    if bpy.app.background:
        # Only render if called from the command line (makes
        # testing easier)
        bpy.ops.render.render(write_still=True)
