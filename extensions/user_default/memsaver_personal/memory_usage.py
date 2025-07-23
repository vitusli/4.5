#!/usr/bin/python3
# copyright (c) 2018- polygoniq xyz s.r.o.

# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.types import Context, Event
import bpy_extras
import typing
import collections
import datetime
import enum
import tempfile
import glob
import subprocess
import os
import shutil
import json
import logging
from . import polib
from . import preferences
from . import __package__ as base_package

logger = logging.getLogger(f"polygoniq.{__name__}")


MODULE_CLASSES: typing.List[typing.Type] = []


FLOAT_SIZE = 4
INT_SIZE = 4
BYTE_SIZE = 1
STRING_SIZE = 16  # made up estimation
VEC2_SIZE = 2 * FLOAT_SIZE
VEC3_SIZE = 3 * FLOAT_SIZE
VEC4_SIZE = 4 * FLOAT_SIZE


HTML_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "html_export", "template.html")
CSS_STYLE_PATH = os.path.join(os.path.dirname(__file__), "html_export", "style.css")
JS_SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "html_export", "script.js")


class HtmlVariable(enum.Enum):
    STYLE = "STYLE"
    SCRIPT = "SCRIPT"
    JSON_DATA = "JSON_DATA"
    MEMSAVER_VERSION = "MEMSAVER_VERSION"


def get_image_size_bytes(image: bpy.types.Image) -> int:
    """Returns the memory usage of an image in bytes"""
    width, height = image.size
    color_depth = image.depth // 8
    return width * height * color_depth


def get_mesh_triangle_count(mesh: bpy.types.Mesh) -> int:
    """Returns the number of triangles in a mesh"""
    mesh.calc_loop_triangles()
    return len(mesh.loop_triangles)


class DatablockMemoryUsage:
    def __init__(
        self,
        datablock: bpy.types.ID,
        scope: typing.Optional[str] = None,
    ):
        self.bytes = 0
        self.type_ = type(datablock).__name__
        if hasattr(datablock, "name_full"):
            self.title = datablock.name_full
        else:
            self.title = datablock.name
        if scope is not None:
            self.title += f" ({scope})"

        if isinstance(datablock, bpy.types.Mesh):
            vertex_count = get_mesh_triangle_count(datablock) * 3

            # vertex position, 3x float32, in an "ideal" mesh, one vertex location is shared by 6 triangle vertices
            self.bytes += (vertex_count // 6) * VEC3_SIZE
            # normal, 3x float32
            self.bytes += vertex_count * VEC3_SIZE

            # we assume 2x float32
            uv_layer_size = VEC2_SIZE * vertex_count
            self.bytes += uv_layer_size * len(datablock.uv_layers)

            # we assume 3x int8
            vertex_color_size = 3 * BYTE_SIZE * vertex_count
            self.bytes += vertex_color_size * len(datablock.vertex_colors)

            # TODO: This model is super simplified

        elif isinstance(datablock, bpy.types.Image):
            self.bytes += get_image_size_bytes(datablock)

        assert self.bytes >= 0, f"Datablock '{self.title}' cannot use negative memory"

    def __repr__(self) -> str:
        return f"{self.type_}: {self.title} - {self.bytes} B"


class BlendMemoryUsage:
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.datablocks_memory_usage: typing.Dict[str, DatablockMemoryUsage] = {}
        self.target_to_dependencies: typing.DefaultDict[str, typing.Set[str]] = (
            collections.defaultdict(set)
        )
        self.dependency_to_targets: typing.DefaultDict[str, typing.Set[str]] = (
            collections.defaultdict(set)
        )

    def _datablock_key(self, datablock: bpy.types.ID, scope: typing.Optional[str] = None) -> str:
        # NodeTrees are owned by materials and between materials NodeTree names can clash, so we
        # assign the scope as part of the datablock_key to make it unique.
        key = f"{type(datablock).__name__}: "
        if hasattr(datablock, "name_full"):
            key += datablock.name_full
        else:
            key += datablock.name
        if scope is not None:
            key += f" ({scope})"
        return key

    def record_blend(self) -> None:
        assert os.path.exists(self.filepath), f"File '{self.filepath}' does not exist"
        bpy.ops.wm.open_mainfile(filepath=self.filepath)
        if bpy.context.scene is not None:
            depsgraph = bpy.context.evaluated_depsgraph_get()
            self.record_datablock(bpy.context.scene, depsgraph)

    def record_dependency(self, target: bpy.types.ID, dependency: bpy.types.ID) -> None:
        target_key = self._datablock_key(target)
        dependency_key = self._datablock_key(dependency)

        self.target_to_dependencies[target_key].add(dependency_key)
        self.dependency_to_targets[dependency_key].add(target_key)

    def record_datablock(
        self,
        datablock: bpy.types.ID,
        depsgraph: bpy.types.Depsgraph,
        scope: typing.Optional[str] = None,
    ) -> None:
        datablock_key = self._datablock_key(datablock, scope)
        if datablock_key in self.datablocks_memory_usage:
            return  # already recorded

        self.datablocks_memory_usage[datablock_key] = DatablockMemoryUsage(datablock, scope)

        if isinstance(datablock, bpy.types.Scene):
            self._record_scene_dependencies(datablock, depsgraph)
        elif isinstance(datablock, bpy.types.World):
            self._record_world_dependencies(datablock, depsgraph)
        elif isinstance(datablock, bpy.types.Collection):
            self._record_collection_dependencies(datablock, depsgraph)
        elif isinstance(datablock, bpy.types.Object):
            self._record_object_dependencies(datablock, depsgraph)
        elif isinstance(datablock, bpy.types.Material):
            self._record_material_dependencies(datablock, depsgraph)
        elif isinstance(datablock, bpy.types.NodeTree):  # TODO: or only ShaderNodeTree?
            self._record_node_tree_dependencies(datablock, depsgraph)
        elif isinstance(
            datablock,
            (
                bpy.types.Camera,
                bpy.types.Light,
                bpy.types.Mesh,  # meshes don't depend on anything
                bpy.types.Curve,  # curves don't depend on anything
                bpy.types.Image,  # images don't depend on anything
                bpy.types.Armature,  # TODO: Support armatures, armatures are ligthweight
            ),
        ):
            pass
        else:
            logger.warning(f"{datablock} not taken into account in estimation!")

    def _record_scene_dependencies(
        self, scene: bpy.types.Scene, depsgraph: bpy.types.Depsgraph
    ) -> None:
        if scene.world is not None:
            self.record_datablock(scene.world, depsgraph)
            self.record_dependency(scene, scene.world)

        self.record_datablock(scene.collection, depsgraph)
        self.record_dependency(scene, scene.collection)

    def _record_world_dependencies(
        self, world: bpy.types.World, depsgraph: bpy.types.Depsgraph
    ) -> None:
        if world.use_nodes:
            self.record_datablock(world.node_tree, depsgraph, self._datablock_key(world))
            self.record_dependency(world, world.node_tree)

    def _record_collection_dependencies(
        self,
        collection: bpy.types.Collection,
        depsgraph: bpy.types.Depsgraph,
    ) -> None:
        for obj in collection.objects:
            if obj.hide_render:
                continue  # skip hidden objects

            self.record_datablock(obj, depsgraph)
            self.record_dependency(collection, obj)

        for child_collection in collection.children:
            if child_collection.hide_render:
                continue  # skip hidden collections

            self.record_datablock(child_collection, depsgraph)
            self.record_dependency(collection, child_collection)

    def _record_object_dependencies(
        self, obj: bpy.types.Object, depsgraph: bpy.types.Depsgraph
    ) -> None:
        if obj.data is not None:
            recorded_data = obj.data
            scope = None
            if len(obj.modifiers) > 0:
                if obj.data.users > 1:
                    scope = self._datablock_key(obj)
                adjusted_mods: typing.List[
                    typing.Union[bpy.types.SubsurfModifier, bpy.types.MultiresModifier]
                ] = []
                for mod in obj.modifiers:
                    if isinstance(mod, (bpy.types.SubsurfModifier, bpy.types.MultiresModifier)):
                        adjusted_mods.append(mod)
                        mod.levels = mod.render_levels
                if len(adjusted_mods) > 0:
                    depsgraph.update()
                recorded_data = obj.evaluated_get(depsgraph).data
            self.record_datablock(recorded_data, depsgraph, scope)
            self.record_dependency(obj, recorded_data)
        if obj.instance_type == 'COLLECTION':
            if obj.instance_collection is not None:
                self.record_datablock(obj.instance_collection, depsgraph)
                self.record_dependency(obj, obj.instance_collection)
            else:
                logger.warning(
                    f"Object {obj.name} has instance_type='COLLECTION' but its "
                    f"instance_collection is None! Skipping..."
                )

        for material_slot in obj.material_slots:
            if material_slot.material is not None:
                self.record_datablock(material_slot.material, depsgraph)
                self.record_dependency(obj, material_slot.material)

        for child_object in obj.children:  # TODO: this takes O(len(bpy.data.objects))!
            self.record_datablock(child_object, depsgraph)
            self.record_dependency(obj, child_object)
            self._record_object_dependencies(child_object, depsgraph)

    def _record_material_dependencies(
        self, material: bpy.types.Material, depsgraph: bpy.types.Depsgraph
    ) -> None:
        if not material.use_nodes:
            logger.warning(
                f"Warning: Cannot record dependencies of {material.name}, only node based "
                f"materials are supported for now."
            )
            return

        if material.node_tree is not None:
            self.record_datablock(material.node_tree, depsgraph, self._datablock_key(material))
            self.record_dependency(material, material.node_tree)

    def _record_node_tree_dependencies(
        self, node_tree: bpy.types.NodeTree, depsgraph: bpy.types.Depsgraph
    ) -> None:
        for node in node_tree.nodes:
            if isinstance(node, bpy.types.ShaderNodeTexImage):
                self.record_dependency(node_tree, node)
                self._record_shader_node_tex_image_dependencies(node, depsgraph)
            elif isinstance(node, bpy.types.ShaderNodeTexEnvironment):
                self.record_dependency(node_tree, node)
                self._record_shader_node_tex_environment_dependencies(node, depsgraph)
            elif hasattr(node, "image"):  # generic image node to support other render engines
                self.record_dependency(node_tree, node)
                self._record_node_image_dependencies(node, depsgraph)
            elif isinstance(node, bpy.types.ShaderNodeGroup):
                self.record_dependency(node_tree, node)
            else:
                # TODO: Tons of nodes we don't support yet
                pass

    def _record_node_image_dependencies(
        self, node: bpy.types.Node, depsgraph: bpy.types.Depsgraph
    ) -> None:
        """Records image dependencies for generic image nodes

        Recording image dependencies from generic image nodes allows support for Octane and possibly
        other render engines with custom shader nodes. The only requirement for the node is to
        contain an image attribute.
        """
        if node.image is not None:
            self.record_datablock(node.image, depsgraph)
            self.record_dependency(node, node.image)

    def _record_shader_node_tex_image_dependencies(
        self, node: bpy.types.ShaderNodeTexImage, depsgraph: bpy.types.Depsgraph
    ) -> None:
        self._record_node_image_dependencies(node, depsgraph)

    def _record_shader_node_tex_environment_dependencies(
        self, node: bpy.types.ShaderNodeTexEnvironment, depsgraph: bpy.types.Depsgraph
    ) -> None:
        self._record_node_image_dependencies(node, depsgraph)

    def _record_shader_node_group_dependencies(
        self, node: bpy.types.ShaderNodeGroup, depsgraph: bpy.types.Depsgraph
    ) -> None:
        if node.node_tree is not None:
            self.record_datablock(node.node_tree, depsgraph)
            self.record_dependency(node, node.node_tree)

    def __repr__(self) -> str:
        return f"""
        Filename: {self.filepath}
        Datablocks memory usage: {self.datablocks_memory_usage}
        Target to dependencies: {self.target_to_dependencies}
        Dependency targets: {self.dependency_to_targets}
        """


class MemoryUsageStatistics:
    def __init__(self, filepath: str, timestamp: datetime.datetime):
        self.timestamp = timestamp
        if os.path.isfile(filepath) and filepath.endswith(".blend"):
            blend_filepaths = [filepath]
        elif os.path.isdir(filepath):
            blend_filepaths = glob.glob(os.path.join(filepath, "**", "*.blend"), recursive=True)
        else:
            raise FileNotFoundError("Invalid file path")
        self.blends_memory_usage: typing.List[BlendMemoryUsage] = [
            BlendMemoryUsage(os.path.abspath(filepath).replace("\\", "/"))
            for filepath in blend_filepaths
        ]

    def calculate_memory_usage(self) -> None:
        for blend_memory_usage in self.blends_memory_usage:
            blend_memory_usage.record_blend()
            if len(blend_memory_usage.datablocks_memory_usage) == 0:
                logger.warning(
                    f"'{blend_memory_usage.filepath}': Memory usage could not be calculated with no datablocks."
                )

    def debug_print(self) -> None:
        for memory_usage in self.blends_memory_usage:
            print(f"{memory_usage}\n")

    def as_dict(self) -> typing.Dict:
        memory_usage_list = []
        for blend_memory_usage in self.blends_memory_usage:
            sorted_by_usage = sorted(
                blend_memory_usage.datablocks_memory_usage.values(),
                key=lambda x: x.bytes,
                reverse=True,
            )
            total_usage_bytes = sum(usage.bytes for usage in sorted_by_usage)
            # We want to avoid zero division when calculating percentages
            if total_usage_bytes == 0:
                total_usage_bytes = 1
            memory_usage_list.append(
                {
                    "id": blend_memory_usage.filepath,
                    "name": blend_memory_usage.filepath.split("/")[-1],
                    "size_bytes": total_usage_bytes,
                    "datablocks": [
                        {
                            "id": f"{blend_memory_usage.filepath}:{datablock.type_}:{datablock.title}",
                            "type": datablock.type_,
                            "name": datablock.title,
                            "size_bytes": datablock.bytes,
                            "size_factor": datablock.bytes / total_usage_bytes,
                        }
                        for datablock in sorted_by_usage
                    ],
                }
            )
        return {
            "memory_usage": memory_usage_list,
            "timestamp": self.timestamp.isoformat(),
        }

    def write_json_report(self, fp: typing.IO) -> None:
        json.dump(self.as_dict(), fp, indent=4)

    def write_html_report(self, fp: typing.IO) -> None:
        with open(HTML_TEMPLATE_PATH) as backbone_template_fp:
            backbone_template = backbone_template_fp.read()
        with open(CSS_STYLE_PATH) as css_fp:
            css_style = css_fp.read()
        with open(JS_SCRIPT_PATH) as js_fp:
            js_script = js_fp.read()

        # Infer memsaver version so we can use it in the HTML for correct documentation link
        mod_info = polib.utils_bpy.get_addon_mod_info(base_package)
        memsaver_version = ".".join(map(str, mod_info["version"]))

        replace_dict = {
            HtmlVariable.STYLE.value: css_style,
            HtmlVariable.SCRIPT.value: js_script,
            HtmlVariable.JSON_DATA.value: json.dumps(self.as_dict()),
            HtmlVariable.MEMSAVER_VERSION.value: memsaver_version,
        }
        final_html = backbone_template.format(**replace_dict)
        fp.write(final_html)


def run_memory_usage_estimation(
    filepath: str, output_filepath: str, timestamp: datetime.datetime
) -> None:
    _, ext = os.path.splitext(output_filepath)
    try:
        output_type = preferences.MemoryEstimateOutputType(ext.upper()[1:])
    except ValueError:
        raise ValueError(f"Unsupported file extension: {ext}")
    stats = MemoryUsageStatistics(filepath, timestamp)
    stats.calculate_memory_usage()

    if not os.path.exists(os.path.dirname(output_filepath)):
        os.makedirs(os.path.dirname(output_filepath))

    with open(output_filepath, mode="w") as out_file:
        if output_type == preferences.MemoryEstimateOutputType.JSON:
            stats.write_json_report(out_file)
            logger.info(f"Wrote memory estimation JSON to: {out_file.name}")
        elif output_type == preferences.MemoryEstimateOutputType.HTML:
            stats.write_html_report(out_file)
            logger.info(f"Wrote memory estimation HTML to: {out_file.name}")


def run_memory_usage_estimation_background(
    filepath: str, output_filepath: str, timestamp: datetime.datetime
) -> subprocess.Popen:
    exec_code = (
        "import sys\n"
        "import traceback\n"
        # datetime is required by 'repr(timestamp)'
        "import datetime\n"
        # This code will run in a separate subprocess
        # In order to debug, comment out the code bellow and set breakpoints
        #
        # "import bpy\n"
        # "import os\n"
        # "sys.executable = os.path.join(\n"
        # "    os.path.split(sys.argv[0])[0],\n"
        # "    f'{bpy.app.version[0]}.{bpy.app.version[1]}',\n"
        # "    'python',\n"
        # "    'bin',\n"
        # "    'python.exe',\n"
        # ")\n"
        # "import debugpy\n"
        # "debugpy.listen(address=('localhost', 6969))\n"
        # "debugpy.wait_for_client()\n"
        # "debugpy.breakpoint()\n"
        #
        "try:\n"
        f"    import {base_package}\n"
        f"    {__name__}.{run_memory_usage_estimation.__name__}({repr(filepath)}, {repr(output_filepath)}, {repr(timestamp)})\n"
        "except Exception as e:\n"
        "    traceback.print_exc()\n"
        "    sys.exit(1)"
    )
    SCRIPT_SRC = f"exec({repr(exec_code)})"
    return subprocess.Popen(
        [
            bpy.app.binary_path,
            "--background",
            "--python-expr",
            SCRIPT_SRC,
        ],
    )


def get_output_filepath(timestamp: datetime.datetime) -> str:
    prefs = preferences.get_preferences(bpy.context)
    try:
        output_type = preferences.MemoryEstimateOutputType(prefs.memory_estimation_output_type)
    except ValueError:
        raise ValueError(f"Unknown output type: {prefs.memory_estimation_output_type}")
    return os.path.join(
        prefs.memory_estimation_output_directory,
        f"memory_usage_{timestamp.strftime('%Y-%m-%d_%H-%M-%S')}.{output_type.value.lower()}",
    )


class EstimateMemoryUsageBase(bpy.types.Operator):
    bl_label = "Estimate Memory Usage"

    estimation_process: typing.Optional[subprocess.Popen] = None
    timer_event: typing.Optional[bpy.types.Timer] = None
    output_filepath: str = ""

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return (
            EstimateMemoryUsageBase.estimation_process is None
            and EstimateMemoryUsageBase.timer_event is None
        )

    @polib.utils_bpy.safe_modal()
    def modal(self, context: bpy.types.Context, event: bpy.types.Event):
        # Both timer and event as None means the process should be cancelled
        if (
            EstimateMemoryUsageBase.estimation_process is None
            and EstimateMemoryUsageBase.timer_event is None
        ):
            logger.info("Cancelling memory estimation process")
            return {'CANCELLED'}

        # If only one of them is None, there is a problem
        if EstimateMemoryUsageBase.estimation_process is None:
            raise RuntimeError("Expected a running memory estimation process")
        if EstimateMemoryUsageBase.timer_event is None:
            raise RuntimeError("Expected a running timer event")

        if EstimateMemoryUsageBase.estimation_process.poll() is not None:
            if EstimateMemoryUsageBase.estimation_process.returncode != 0:
                self.report({'ERROR'}, "Memory estimation failed. Check the console for details.")
            else:
                polib.utils_bpy.xdg_open_file(EstimateMemoryUsageBase.output_filepath)
                self.report({'INFO'}, "Memory estimation finished.")

            context.window_manager.event_timer_remove(EstimateMemoryUsageBase.timer_event)
            EstimateMemoryUsageBase.timer_event = None
            EstimateMemoryUsageBase.estimation_process = None
            EstimateMemoryUsageBase.output_filepath = ""
            polib.ui_bpy.tag_areas_redraw(context, {'VIEW_3D'})
            return {'FINISHED'}

        return {'PASS_THROUGH'}

    def start_estimation_process(self, filepath: str, context: bpy.types.Context) -> None:
        timestamp = datetime.datetime.now()
        EstimateMemoryUsageBase.output_filepath = get_output_filepath(timestamp)
        EstimateMemoryUsageBase.estimation_process = run_memory_usage_estimation_background(
            filepath, EstimateMemoryUsageBase.output_filepath, timestamp
        )
        EstimateMemoryUsageBase.timer_event = context.window_manager.event_timer_add(
            1.0, window=context.window
        )
        context.window_manager.modal_handler_add(self)


@polib.log_helpers_bpy.logged_operator
class CancelMemoryUsageEstimation(bpy.types.Operator):
    bl_idname = "memsaver.cancel_memory_usage_estimation"
    bl_label = "Cancel Memory Usage Estimation"
    bl_description = "Cancels the memory usage estimation process"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        return (
            EstimateMemoryUsageBase.estimation_process is not None
            or EstimateMemoryUsageBase.timer_event is not None
        )

    def execute(self, context: bpy.types.Context):
        if EstimateMemoryUsageBase.estimation_process is not None:
            EstimateMemoryUsageBase.estimation_process.terminate()
            EstimateMemoryUsageBase.estimation_process = None

        if EstimateMemoryUsageBase.timer_event is not None:
            context.window_manager.event_timer_remove(EstimateMemoryUsageBase.timer_event)
            EstimateMemoryUsageBase.timer_event = None
        return {'FINISHED'}


MODULE_CLASSES.append(CancelMemoryUsageEstimation)


@polib.log_helpers_bpy.logged_operator
class EstimateMemoryUsageCurrentFile(EstimateMemoryUsageBase):
    bl_idname = "memsaver.estimate_memory_usage_current_file"
    bl_description = (
        "Goes through datablocks of this file that would have to be loaded for rendering, "
        "estimates how much memory is needed for each one."
    )
    bl_options = {'REGISTER'}

    def execute(self, context: bpy.types.Context):
        self.temp_folder = tempfile.mkdtemp(prefix="memsaver_")
        filename = (
            os.path.basename(bpy.data.filepath) if bpy.data.filepath != "" else "memory_usage.blend"
        )
        temp_filepath = os.path.join(self.temp_folder, filename)
        bpy.ops.wm.save_as_mainfile(filepath=temp_filepath, copy=True)
        self.start_estimation_process(temp_filepath, context)
        return {'RUNNING_MODAL'}

    def modal(self, context: Context, event: Event):
        ret = super().modal(context, event)
        if ret == {'FINISHED'} and os.path.exists(self.temp_folder):
            shutil.rmtree(self.temp_folder)
        return ret


MODULE_CLASSES.append(EstimateMemoryUsageCurrentFile)


@polib.log_helpers_bpy.logged_operator
class EstimateMemoryUsage(EstimateMemoryUsageBase, bpy_extras.io_utils.ImportHelper):
    bl_idname = "memsaver.estimate_memory_usage"
    bl_description = (
        "Goes through datablocks of files from 'filepath' that would have to be loaded for rendering, "
        "estimates how much memory is needed for each one."
    )
    bl_options = {'REGISTER'}

    # These are the primary file types the user should select
    # All other file types work as well, but are not visible by default
    filter_glob: bpy.props.StringProperty(default="*.blend", options={'HIDDEN'})

    filename: bpy.props.StringProperty(options={'HIDDEN', 'SKIP_SAVE'}, default="")

    def execute(self, context: bpy.types.Context):
        # We check whether any blend file(s) can be found but pass the initial filepath to the script
        # As too many filepaths would exceed the Popen input limit
        is_blend_found = False
        if os.path.isdir(self.filepath):
            is_blend_found = (
                next(glob.iglob(os.path.join(self.filepath, "**", "*.blend"), recursive=True), None)
                is not None
            )
        elif os.path.isfile(self.filepath) and self.filepath.endswith(".blend"):
            is_blend_found = True
        else:
            self.report({'ERROR'}, "Invalid file path")
            return {'CANCELLED'}
        if not is_blend_found:
            self.report({'ERROR'}, "No .blend files found")
            return {'CANCELLED'}
        self.start_estimation_process(self.filepath, context)
        return {'RUNNING_MODAL'}


MODULE_CLASSES.append(EstimateMemoryUsage)


def register():
    for cls in MODULE_CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(MODULE_CLASSES):
        bpy.utils.unregister_class(cls)
