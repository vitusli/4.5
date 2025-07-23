from bpy.types import Context, OperatorProperties
import mathutils
import random
import os
import bpy
import bmesh
import time
from bpy_extras.io_utils import ImportHelper
import numpy as np
from subprocess import run
import rna_keymap_ui
from .addon_update_checker import *
from pathlib import Path

bl_info = {
    "name": "ColorFrame Renders Pro",
    "author": "Amandeep",
    "description": "Create Beautiful Colored Wireframe Renders",
    "blender": (2, 93, 0),
    "version": (4, 1, 14),
    "location": "N-Panel > ColorFrame",
    "warning": "",
    "category": "Object",
}


# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
def draw_hotkeys(col, km_name):
    kc = bpy.context.window_manager.keyconfigs.user
    for kmi in [a.idname for b, a in addon_keymaps]:
        km2 = kc.keymaps[km_name]
        kmi2 = []
        for a, b in km2.keymap_items.items():
            if a == kmi:
                kmi2.append(b)
        if kmi2:
            for a in kmi2:
                col.context_pointer_set("keymap", km2)
                rna_keymap_ui.draw_kmi([], kc, km2, a, col, 0)


def get_collections(self, context):
    return [
        ("New", "New", "New"),
    ] + [(p.name, p.name, p.name) for p in preferences().saved_palettes]


PREFERENCES_PATH = (
    Path(bpy.utils.user_resource("SCRIPTS")).parent / "config" / "CFR_Palettes"
)


def savePreferences():
    if not os.path.isdir(PREFERENCES_PATH):
        os.makedirs(PREFERENCES_PATH)
    for a in preferences().saved_palettes:
        with open(
            os.path.join(PREFERENCES_PATH, f"{a.name}.txt"),
            mode="w+",
            newline="\n",
            encoding="utf-8",
        ) as file:
            for p in a.palettes:
                colors = ""
                for c in p.colors:
                    colors += str(c.color[:]) + "=="
                file.write(f"{p.name}=>{colors}\n")


def loadPreferences():
    if not os.path.isdir(PREFERENCES_PATH):
        os.makedirs(PREFERENCES_PATH)
    preferences().saved_palettes.clear()
    for a in os.listdir(PREFERENCES_PATH):
        if os.path.isfile(os.path.join(PREFERENCES_PATH, a)):
            with open(
                os.path.join(PREFERENCES_PATH, a),
                mode="r",
                newline="\n",
                encoding="utf-8",
            ) as file:
                palettes = file.readlines()
                # print(a,palettes)
                e = preferences().saved_palettes.add()
                e.name = a.split(".")[0]
                for p in palettes:
                    t = e.palettes.add()
                    t.name = p.split("=>")[0]
                    for c in p.split("=>")[1].split("=="):
                        try:
                            color = t.colors.add()
                            color.color = eval(c)
                        except:
                            t.colors.remove(len(t.colors) - 1)


def object_sets_by_dimensions(objects, count=5):
    obj_dims = []
    for obj in objects:
        obj_dims.append((obj, obj.dimensions.x + obj.dimensions.y + obj.dimensions.z))
    if obj_dims:
        obj_dims = sorted(obj_dims, key=lambda x: x[1])
        max_dim = obj_dims[len(obj_dims) - 1][1]
        # print(min_dim,max_dim)
        sets = []
        steps = max_dim / count
        for i in range(1, count + 1):
            # print(i*steps)
            objects_in_set = []
            for o, d in obj_dims:
                if d <= i * steps and d > (i - 1) * steps:
                    objects_in_set.append(o)
            sets.append(objects_in_set)
        return sets
    return []


def refresh_palette_names(self, context):
    for p in preferences().saved_palettes:
        # index = .find(self.name)
        # if index:
        final_name = p.name
        i = 1
        while final_name in [a.name for a in preferences().saved_palettes if a != p]:
            final_name = p.name + f"_{i}"
            i = i + 1
        p.name = final_name


class CFR_Color(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty()
    color: bpy.props.FloatVectorProperty(
        name="Color", subtype="COLOR", soft_max=1, soft_min=0, default=[1.0, 1.0, 1.0]
    )


class CFR_Palette(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(default="Palette")
    colors: bpy.props.CollectionProperty(type=CFR_Color)


class CFR_Palettes_Collections(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(default="Collection", name="Collection Name")
    palettes: bpy.props.CollectionProperty(type=CFR_Palette, name="Palettes")


def draw_palette(
    context,
    layout,
    pallete,
    collection=None,
    show_label=False,
    delete_button=False,
    height=2,
):
    if show_label:
        layout.prop(pallete, "name", text="")
        layout.separator()
    row1 = layout.split(factor=0.9 if delete_button else 1)
    row1.scale_y = height
    row = row1.row(align=True)
    # row.scale_y = 2

    for c in pallete.colors:
        row.prop(c, "color", text="")
    if delete_button and collection:
        op = row1.operator("cfr.deletepalette", icon="TRASH", text="")
        op.collection = collection.name
        op.name = pallete.name


class CFR_PT_Extras(bpy.types.Panel):
    bl_label = "CFR Extras"
    bl_idname = "CFR_PT_Extras"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ColorFrame"
    bl_order = 2

    def draw(self, context):
        self.layout.label(text="Use CFR Colors in your materials!")
        row = self.layout.column(align=True)
        row.operator("cfr.setupcfrmaterials", text="Setup/Update CFR Materials")
        row.operator(
            "cfr.setupcfrmaterials", text="Disable CFR Materials"
        ).disable = True
        self.layout.prop(preferences(), "auto_update_materials")


class CFR_PT_Colorframe_Renders(bpy.types.Panel):
    bl_label = "ColorFrame Renders"
    bl_idname = "OBJECT_PT_Colorframe_Renders"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ColorFrame"
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        draw_update_section_for_panel(layout, context)
        mats = set(
            [
                a
                for b in context.selected_objects
                if b.type in {"MESH", "CURVE", "TEXT", "SURFACE"}
                for a in b.data.materials
                if a
            ]
        )
        # print(mats)
        if context.scene.cfr_line_art_enabled:
            layout.label(
                text="Temporarily turn off Line Art if performance is slow!",
                icon="ERROR",
            )
        layout.row().prop(context.scene, "shading_type", expand=True)
        layout.row().prop(context.scene, "coloring_method", expand=True)
        # if context.scene.shading_type == 'STUDIO':
        #     layout.prop(context.scene, 'use_metallic', toggle=True)
        row = layout.row(align=True)

        row.prop(context.scene, "cfr_color", text="")

        row.operator("cfr.setcolor")
        layout.prop(context.scene, "cfr_palettes")
        for p in preferences().saved_palettes:
            if p.name == context.scene.cfr_palettes:
                for a in p.palettes:
                    box = layout.box()

                    row = box.row(align=True)
                    row.scale_y = (
                        2
                        if a.name == context.scene.selected_pallet.palette
                        and p.name == context.scene.selected_pallet.collection
                        else 1
                    )
                    draw_palette(
                        context,
                        row,
                        a,
                        collection=p,
                        height=1,
                        delete_button=preferences().show_delete_button,
                    )
                    row.separator()
                    op = row.operator(
                        "cfr.loadpalette",
                        text="",
                        icon="CHECKMARK",
                        depress=True
                        if a.name == context.scene.selected_pallet.palette
                        and p.name == context.scene.selected_pallet.collection
                        else False,
                    )
                    op.collection = p.name
                    op.palette = a.name
        if (
            context.scene.cfr_palettes != "Clipboard"
            and context.scene.cfr_palettes != context.scene.selected_pallet.collection
        ):
            for p in preferences().saved_palettes:
                if p.name == context.scene.selected_pallet.collection:
                    for a in p.palettes:
                        if a.name == context.scene.selected_pallet.palette:
                            box = layout.box()
                            box.label(text=f"Active Palette : {a.name}")
                            draw_palette(context, box, a)
        # if context.scene.cfr_palettes!="Clipboard":
        #     for p in preferences().saved_palettes:
        #         if p.name == context.scene.selected_pallet.collection:
        #             for a in p.palettes:
        #                 if a.name==context.scene.selected_pallet.palette:
        #                     box=layout.box()
        #                     box.label(text=a.name)
        #                     draw_palette(context, box, a)

        layout.operator("cfr.randomcolors")
        if (
            not (
                context.scene.shading_type == "STUDIO"
                and context.scene.coloring_method == "Viewport"
            )
            and context.mode == "OBJECT"
        ):
            layout.operator("cfr.randomcolorbydimensions")
            layout.operator("cfr.randomcolorbycollection")
        layout.separator()
        layout.prop(context.scene, "cfr_wire_opacity")
        layout.prop(context.scene, "cfr_wire_color")

        if not context.scene.cfr_transparent:
            layout.prop(context.scene, "cfr_bg_color")
        layout.prop(context.scene, "cfr_transparent", icon="TEXTURE", toggle=True)
        row = layout.row(align=True)
        row.prop(context.space_data.shading, "show_cavity", toggle=True)
        row.prop(context.space_data.shading, "show_shadows", toggle=True)
        layout.separator()
        row = layout.row(align=True)
        row.scale_y = 2
        if not context.scene.cfr_preview_enabled:
            row.operator("cfr.preview", icon="RESTRICT_VIEW_OFF", depress=False)
        else:
            row.operator("cfr.disablepreview", icon="RESTRICT_VIEW_ON", depress=True)
        layout.separator()
        layout.label(text="Render:")
        row = layout.row(align=True)
        row.operator("cfr.render", icon="RESTRICT_RENDER_OFF")

        row.operator("cfr.renderanimation", icon="RENDER_ANIMATION")
        row = layout.row(align=True)
        row.operator("cfr.renderadvanced", icon="OPTIONS")
        # row.operator("cfr.renderwireframe", icon="RENDER_ANIMATION",text='Render Animation').animation=True
        layout.prop(context.scene, "cfr_render_directory", text="Output Directory")
        layout.operator("cfr.opendirectory", icon="FILEBROWSER")
        if context.scene.coloring_method == "Viewport":
            for m in mats:
                r = layout.row(align=True)
                r = r.split(factor=0.5)
                r.label(text=m.name, icon_value=layout.icon(m))
                r.prop(m, "diffuse_color", text="")
                if context.scene.shading_type == "STUDIO":
                    r.prop(m, "cfr_metallic", toggle=True)
        elif context.scene.coloring_method == "Object":
            if [
                a
                for a in context.selected_objects
                if a.type in {"MESH", "CURVE", "SURFACE", "TEXT"}
            ]:
                layout.label(text="Selected Objects")
                for s in [
                    a
                    for a in context.selected_objects
                    if a.type in {"MESH", "CURVE", "SURFACE", "TEXT"}
                ]:
                    layout.prop(s, "color", text=s.name)
                layout.separator()
        else:
            if [a for a in context.selected_objects if a.type == "MESH"]:
                layout.label(text="Selected Objects")
                for s in [a for a in context.selected_objects if a.type == "MESH"]:
                    layout.prop(s, "cfr_color", text=s.name)
                layout.separator()


class CFR_PT_LineArt(bpy.types.Panel):
    bl_label = "Line Art"
    bl_idname = "OBJECT_PT_CFR_Line_Art"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ColorFrame"
    bl_order = 1

    def draw(self, context):
        layout = self.layout
        if not context.scene.camera:
            layout.label(
                text="Make sure there is an active camera in the scene!", icon="ERROR"
            )
        if not context.scene.cfr_line_art_object:
            layout.operator("cfr.addlineart")
        else:
            layout.prop(context.scene, "cfr_line_art_enabled", toggle=True)
            if context.scene.cfr_line_art_enabled:
                if bpy.app.version < (4, 3, 0):
                    layout.prop(
                        context.scene.cfr_line_art_object.data.layers[0],
                        "tint_color",
                        text="Color",
                    )
                else:
                    layout.prop(
                        context.scene.cfr_line_art_object.data.materials[
                            0
                        ].grease_pencil,
                        "color",
                        text="Color",
                    )
                layout.prop(
                    context.scene.cfr_line_art_object.data.layers[0],
                    "opacity",
                    text="Opacity",
                )
                if not preferences().auto_update_line_art_thickness:
                    row = layout.row()
                    row = row.split(factor=0.8, align=True)
                    row.prop(context.scene, "cfr_line_art_thickness")
                    row.operator(
                        "cfr.updatelineartthickness", icon="CHECKMARK", text=""
                    )
                else:
                    if bpy.app.version < (4, 3, 0):
                        layout.prop(
                            context.scene.cfr_line_art_object.data.layers[0],
                            "line_change"
                            if bpy.app.version < (4, 3, 0)
                            else "radius_offset",
                            text="Thickness",
                        )
                    else:
                        layout.prop(
                            context.scene.cfr_line_art_object.modifiers[0],
                            "thickness",
                            text="Thickness",
                        )
                layout.prop(
                    preferences(), "auto_update_line_art_thickness", toggle=True
                )
                if bpy.app.version < (4, 3, 0):
                    layout.prop(
                        context.scene.cfr_line_art_object.data,
                        "pixel_factor",
                        text="Thickness Multiplier",
                    )
                else:
                    layout.prop(
                        context.scene.cfr_line_art_object.modifiers["Thickness"],
                        "thickness_factor",
                        text="Thickness Multiplier",
                    )


class CFR_PT_Palettes(bpy.types.Panel):
    bl_label = "CFR Palettes"
    bl_idname = "OBJECT_PT_CFR_Palettes"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "ColorFrame"
    bl_order = 3

    def draw(self, context):
        layout = self.layout

        layout.operator("cfr.savepalette")
        layout.label(text="Get Palettes:")
        layout.operator(
            "wm.url_open", text="Open Coolors", icon="COLORSET_04_VEC"
        ).url = "https://coolors.co/palettes/trending"
        layout.operator(
            "wm.url_open", text="Open ColorHunt", icon="COLORSET_06_VEC"
        ).url = "https://colorhunt.co"


def add_ao_overlay(og_img, ao_img, strength=1):
    cmd = [bpy.app.binary_path]
    cmd.append("--background")
    cmd.append("--factory-startup")
    cmd.append("--python")
    cmd.append(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "add_ao_overlay.py")
    )
    cmd.append("--")
    cmd.append(og_img)
    cmd.append(ao_img)
    cmd.append(str(strength))
    run(cmd)


def update_auto_update_line_art(self, context):
    if self.auto_update_line_art_thickness:
        if bpy.app.version < (4, 3, 0):
            context.scene.cfr_line_art_object.data.layers[
                "Lines"
            ].line_change = context.scene.cfr_line_art_thickness
        else:
            context.scene.cfr_line_art_object.modifiers[
                0
            ].thickness = context.scene.cfr_line_art_thickness
    else:
        context.scene.cfr_line_art_thickness = (
            context.scene.cfr_line_art_object.data.layers["Lines"].line_change
        )


class CFRPrefs(bpy.types.AddonPreferences, AddonUpdateChecker):
    bl_idname = __package__
    default_path: bpy.props.StringProperty(
        name="ColorFrame Renders Directory",
        subtype="DIR_PATH",
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), "CFR Renders"),
    )
    save_all_to_default_path: bpy.props.BoolProperty(
        default=False,
        name="Save all renders to this directory, regardless of whether the file has been saved or not",
        description="Save all renders to this path instead of a folder in the same directory as the blend file",
    )
    saved_palettes: bpy.props.CollectionProperty(type=CFR_Palettes_Collections)
    show_palettes: bpy.props.BoolProperty(default=False, name="Saved Palettes")
    convert_to_linear: bpy.props.BoolProperty(
        default=True,
        name="Convert Palettes to LinearRGB Space",
        description="Blender viewport autocorrects for gamma so the colors might look a little faded in the palettes but they will look good in the viewport. Toggling this 'ON' will make the color palettes look exactly as you copied them but the viewport (as well as the renders) will turn out darker.",
    )
    show_delete_button: bpy.props.BoolProperty(
        default=False, name="Show Delete Button in the N-Panel"
    )
    auto_update_line_art_thickness: bpy.props.BoolProperty(
        default=True,
        name="Auto Update",
        description="Auto Update Line Art Thickness when value is changed.\nDisable if its lagging when changing thickness",
        update=update_auto_update_line_art,
    )
    auto_update_materials: bpy.props.BoolProperty(
        default=True,
        name="Auto Update Materials",
        description="Auto update materials when Coloring method is changed",
    )
    auto_create_render_directory: bpy.props.BoolProperty(
        default=True,
        name="Automatically Create Render Directory",
        description="Automatically create a render directory in current file's parent directory if Output Directory isn't set",
    )

    def draw(self, context):
        layout = self.layout
        draw_update_section_for_prefs(layout, context)
        draw_hotkeys(layout, "3D View")
        layout.prop(self, "default_path")
        layout.prop(self, "save_all_to_default_path")
        layout.prop(self, "auto_create_render_directory")
        layout.prop(self, "show_delete_button")
        layout.prop(self, "convert_to_linear")
        layout2 = layout.column()
        row = layout2.row(align=True)
        row.alignment = "LEFT"
        row.prop(
            self,
            "show_palettes",
            emboss=False,
            icon="TRIA_DOWN" if self.show_palettes else "TRIA_RIGHT",
        )

        if self.show_palettes:
            col = layout2.column()
            for p in self.saved_palettes:
                layout2.separator(factor=1)
                layout2.separator(factor=1)
                col = layout2.box()
                row = col.row()
                row = row.split(factor=0.9)
                row.prop(p, "name")
                op = row.operator("cfr.deletecollection", text="", icon="TRASH")
                op.name = p.name
                for c in p.palettes:
                    draw_palette(
                        context, col, c, p, show_label=True, delete_button=True
                    )
                    col.separator(factor=1)
            col.operator("cfr.import_palettes")


def preferences() -> CFRPrefs:
    return bpy.context.preferences.addons[__package__].preferences


class CFR_OT_Load_Palettes(bpy.types.Operator, ImportHelper):
    bl_idname = "cfr.import_palettes"
    bl_label = "Load Color Palettes"
    bl_description = "Load Color Palettes from txt file"
    bl_options = {"PRESET", "UNDO"}

    filename_ext = ".txt"

    filter_glob: bpy.props.StringProperty(default="*.txt", options={"HIDDEN"})

    def execute(self, context):
        success = True
        path = self.filepath
        if not os.path.isdir(
            os.path.join(
                os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    )
                ),
                "config",
                "CFR_Palettes",
            )
        ):
            os.mkdir(
                os.path.join(
                    os.path.dirname(
                        os.path.dirname(
                            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        )
                    ),
                    "config",
                    "CFR_Palettes",
                )
            )
        initial_palettes = len(preferences().saved_palettes)
        try:
            if os.path.isfile(path):
                with open(path, mode="r", newline="\n", encoding="utf-8") as file:
                    palettes = file.readlines()
                    # print(a,palettes)
                    e = preferences().saved_palettes.add()
                    filename = os.path.basename(path)
                    e.name = filename.split(".")[0]
                    for p in palettes:
                        t = e.palettes.add()
                        t.name = p.split("=>")[0]
                        for c in p.split("=>")[1].split("=="):
                            try:
                                color = t.colors.add()
                                color.color = eval(c)
                            except:
                                t.colors.remove(len(t.colors) - 1)
        except:
            success = False
            if initial_palettes != len(preferences().saved_palettes):
                preferences().saved_palettes.remove(
                    len(preferences().saved_palettes) - 1
                )
        if success:
            self.report({"INFO"}, "Palettes loaded successfully!")
        else:
            self.report({"WARNING"}, "Invalid Data!")
        return {"FINISHED"}


class CFR_OT_Set_Color(bpy.types.Operator):
    bl_idname = "cfr.setcolor"
    bl_label = "Set Color"
    bl_description = "Set Color"
    bl_options = {"REGISTER", "UNDO"}
    create_mats: bpy.props.BoolProperty(
        default=False,
        name="Auto Create Materials",
        description="Create new materials if no material is found on the object",
    )
    auto_hide_wireframe: bpy.props.BoolProperty(
        default=True,
        name="Auto Hide Wireframe Objects",
        description="Automatically hide objects with display type wireframe for better preview",
    )
    select_children: bpy.props.BoolProperty(
        default=False,
        name="Color Empty's Children",
        description="Also color the objects parented to the empties in the selection",
    )

    def draw(self, context):
        layout = self.layout
        if (
            context.mode != "EDIT_MESH"
            and context.scene.shading_type == "STUDIO"
            and context.scene.coloring_method == "Viewport"
        ):
            layout.prop(self, "create_mats")
        layout.prop(self, "auto_hide_wireframe")
        layout.prop(self, "select_children")

    @classmethod
    def poll(cls, context):
        return context.active_object

    def execute(self, context):
        if self.select_children:
            for obj in self.selected:
                try:
                    obj = bpy.data.objects[obj]

                    if obj.type == "EMPTY":
                        self.selected.extend(
                            [
                                ob.name
                                for ob in obj.children
                                if ob.type in {"MESH", "CURVE", "TEXT", "SURFACE"}
                            ]
                        )
                except:
                    pass
        if not self.selected:
            self.report({"WARNING"}, "Nothing Selected!")
            return {"CANCELLED"}
        if context.mode == "OBJECT":
            selected = [
                o
                for o in context.scene.objects
                if o.name in self.selected and o.type != "EMPTY"
            ]
            for s in selected:
                if context.scene.coloring_method == "Viewport":
                    if self.create_mats and not s.data.materials:
                        mat = bpy.data.materials.new(name="CFR_Material")
                        s.data.materials.append(mat)
                    for mat in s.data.materials:
                        if mat:
                            r, g, b = context.scene.cfr_color
                            mat.diffuse_color = (r, g, b, 1.0)
                            mat.roughness = 0.6
                elif context.scene.coloring_method == "Object":
                    r, g, b = context.scene.cfr_color
                    s.color = context.scene.cfr_color[:] + (1,)
                else:
                    if s.type == "MESH":
                        mesh = s.data
                        if "CFR" not in [a.name for a in mesh.vertex_colors]:
                            color_layer = mesh.vertex_colors.new(name="CFR")
                        else:
                            color_layer = mesh.vertex_colors["CFR"]

                        r, g, b = context.scene.cfr_color
                        s.cfr_color = context.scene.cfr_color
                        a = np.tile(
                            (
                                linearrgb_to_srgb(r),
                                linearrgb_to_srgb(g),
                                linearrgb_to_srgb(b),
                                1,
                            ),
                            len(color_layer.data),
                        )
                        color_layer.data.foreach_set("color", a)
                        # for data in color_layer.data:

                        #    data.color = (r, g, b, 1.0)

                if self.auto_hide_wireframe and s.display_type == "WIRE":
                    s.hide_set(True)
        else:
            bm = bmesh.from_edit_mesh(context.active_object.data)
            selected = [i.index for i in bm.faces if i.select]
            bpy.ops.object.editmode_toggle()
            mesh = context.active_object.data
            if "CFR" not in [a.name for a in mesh.vertex_colors]:
                color_layer = mesh.vertex_colors.new(name="CFR")
            else:
                color_layer = mesh.vertex_colors["CFR"]
            for poly in selected:
                for idx in mesh.polygons[poly].loop_indices:
                    r, g, b = context.scene.cfr_color
                    color_layer.data[idx].color = (
                        linearrgb_to_srgb(r),
                        linearrgb_to_srgb(g),
                        linearrgb_to_srgb(b),
                        1,
                    )
            bpy.ops.object.editmode_toggle()
        return {"FINISHED"}

    def invoke(self, context, event):
        self.selected = [
            ob.name
            for ob in context.selected_objects
            if ob.type in {"MESH", "CURVE", "TEXT", "SURFACE", "EMPTY"}
        ]

        return self.execute(context)


def traverse_tree(t):
    yield t
    for child in t.children:
        yield from traverse_tree(child)


def get_colors_from_palette_name(collection, name):
    for p in preferences().saved_palettes:
        if p.name == collection:
            for a in p.palettes:
                if a.name == name:
                    return a.colors
    return []


class CFR_OT_Random_Color_By_Collection(bpy.types.Operator):
    bl_idname = "cfr.randomcolorbycollection"
    bl_label = "Random Colors by Collection"
    bl_description = "Random Colors by Collection using color palette\nCTRL+LMB:Don't use color pallete"
    bl_options = {"REGISTER", "UNDO"}

    seed: bpy.props.IntProperty(default=1, name="Seed")
    auto_hide_wireframe: bpy.props.BoolProperty(
        default=True,
        name="Auto Hide Wireframe Objects",
        description="Automatically hide objects with display type wireframe for better preview",
    )

    def execute(self, context):
        colors = []
        for o in context.scene.objects:
            o.select_set(False)
        random.seed(self.seed)
        if not self.ctrl:
            colors = get_colors_from_link(bpy.context.window_manager.clipboard)
            if context.scene.cfr_palettes != "Clipboard":
                colors = [
                    c.color
                    for c in get_colors_from_palette_name(
                        context.scene.selected_pallet.collection,
                        context.scene.selected_pallet.palette,
                    )
                ]

        for c in traverse_tree(context.scene.collection):
            # print(c)
            if not colors:
                context.scene.cfr_color = [random.random() for i in range(3)]
                r, g, b = context.scene.cfr_color
                col = mathutils.Color((r, g, b))
                col.v = 1
                context.scene.cfr_color = col
            else:
                context.scene.cfr_color = colors[random.randint(0, len(colors) - 1)]
            # print(c.all_objects[:])
            # print(c, context.scene.cfr_color)
            if context.scene.coloring_method == "Object":
                for o in [a for a in c.all_objects]:
                    r, g, b = context.scene.cfr_color
                    o.color = context.scene.cfr_color[:] + (1,)
            else:
                for o in [a for a in c.all_objects if a.type == "MESH"]:
                    mesh = o.data
                    if "CFR" not in [a.name for a in mesh.vertex_colors]:
                        color_layer = mesh.vertex_colors.new(name="CFR")
                    else:
                        color_layer = mesh.vertex_colors["CFR"]
                    r, g, b = context.scene.cfr_color
                    o.cfr_color = context.scene.cfr_color
                    a = np.tile([r, g, b, 1], len(color_layer.data))
                    color_layer.data.foreach_set("color", a)
                    # for data in color_layer.data:
                    #    data.color = (r, g, b, 1.0)
            if self.auto_hide_wireframe and o.display_type == "WIRE":
                o.hide_set(True)
        return {"FINISHED"}

    def invoke(self, context, event):
        self.ctrl = event.ctrl
        return self.execute(context)


class CFR_OT_Random_Color_By_Dimensions(bpy.types.Operator):
    bl_idname = "cfr.randomcolorbydimensions"
    bl_label = "Random Colors by Dimensions"
    bl_description = "Random Colors by Object Dimensions using color palette\nCTRL+LMB:Don't use color pallete"
    bl_options = {"REGISTER", "UNDO"}

    count: bpy.props.IntProperty(default=10, name="Count", min=1)
    seed: bpy.props.IntProperty(default=1, name="Seed")
    auto_hide_wireframe: bpy.props.BoolProperty(
        default=True,
        name="Auto Hide Wireframe Objects",
        description="Automatically hide objects with display type wireframe for better preview",
    )
    select_children: bpy.props.BoolProperty(
        default=False,
        name="Color Empty's Children",
        description="Also color the objects parented to the empties in the selection",
    )

    def execute(self, context):
        if self.select_children:
            for obj in self.selected:
                try:
                    obj = bpy.data.objects[obj]

                    if obj.type == "EMPTY":
                        self.selected.extend(
                            [
                                ob.name
                                for ob in obj.children
                                if ob.type in {"MESH", "CURVE", "TEXT", "SURFACE"}
                            ]
                        )
                except:
                    pass
        if not self.selected:
            self.report({"WARNING"}, "Nothing Selected!")
            return {"CANCELLED"}
        colors = []
        for o in context.scene.objects:
            o.select_set(False)
        selected = [
            o
            for o in context.scene.objects
            if o.name in self.selected and o.type != "EMPTY"
        ]
        random.seed(self.seed)
        if not self.ctrl:
            colors = get_colors_from_link(bpy.context.window_manager.clipboard)
            if context.scene.cfr_palettes != "Clipboard":
                colors = [
                    c.color
                    for c in get_colors_from_palette_name(
                        context.scene.selected_pallet.collection,
                        context.scene.selected_pallet.palette,
                    )
                ]
        for c in object_sets_by_dimensions(selected, max(1, self.count)):
            if not colors:
                context.scene.cfr_color = [random.random() for i in range(3)]
                r, g, b = context.scene.cfr_color
                col = mathutils.Color((r, g, b))
                col.v = 1
                context.scene.cfr_color = col
            else:
                context.scene.cfr_color = colors[random.randint(0, len(colors) - 1)]
            if context.scene.coloring_method == "Vertex":
                # print(c.all_objects[:])
                for o in [a for a in c if a.type == "MESH"]:
                    mesh = o.data
                    if "CFR" not in [a.name for a in mesh.vertex_colors]:
                        color_layer = mesh.vertex_colors.new(name="CFR")
                    else:
                        color_layer = mesh.vertex_colors["CFR"]
                    r, g, b = context.scene.cfr_color
                    o.cfr_color = context.scene.cfr_color
                    a = np.tile([r, g, b, 1], len(color_layer.data))
                    color_layer.data.foreach_set("color", a)
                    # for data in color_layer.data:
                    #    data.color = (r, g, b, 1.0)
            else:
                for o in [a for a in c]:
                    r, g, b = context.scene.cfr_color
                    o.color = context.scene.cfr_color[:] + (1,)
            if self.auto_hide_wireframe and o.display_type == "WIRE":
                o.hide_set(True)

        return {"FINISHED"}

    def invoke(self, context, event):
        self.ctrl = event.ctrl
        self.selected = [
            ob.name for ob in context.selected_objects if ob.type in {"MESH", "EMPTY"}
        ]

        return self.execute(context)


def select(obj, active=True):
    if obj:
        obj.select_set(True)
        if active:
            bpy.context.view_layer.objects.active = obj


class CFR_OT_Save_Palette(bpy.types.Operator):
    bl_idname = "cfr.savepalette"
    bl_label = "Save Color Palette"
    bl_description = "Save Color Palette(from Clipboard) to favorites"
    bl_options = {"REGISTER", "UNDO"}
    name: bpy.props.StringProperty(default="Palette", name="Name")
    collection: bpy.props.EnumProperty(
        items=get_collections, default=0, name="Collection"
    )
    collection_name: bpy.props.StringProperty(
        default="Collection", name="Collection Name"
    )

    def draw(self, context):
        layout = self.layout

        row = layout.row(align=True)
        row.scale_y = 2
        for c in context.scene.cfr_temp_palette:
            row.prop(c, "color", text="")
        layout.prop(self, "name")
        layout.prop(self, "collection")
        if self.collection == "New":
            layout.prop(self, "collection_name")
        # layout.prop(context.scene, 'cfr_temp_palette')

    def execute(self, context):
        # colors = get_colors_from_link(bpy.context.window_manager.clipboard)
        colors = [c.color for c in context.scene.cfr_temp_palette]
        if colors:
            already_exists = (
                True
                if preferences().saved_palettes.find(self.collection_name) >= 0
                else False
            )
            # print(not preferences().saved_palettes.find(self.collection_name))
            if self.collection == "New" and not already_exists:
                pc = preferences().saved_palettes.add()
                pc.name = self.collection_name
            else:
                if self.collection == "New":
                    pc = preferences().saved_palettes[self.collection_name]
                else:
                    pc = preferences().saved_palettes[self.collection]
            p = pc.palettes.add()
            final_name = self.name
            i = 1
            while final_name in [a.name for a in pc.palettes]:
                final_name = self.name + f"_{i}"
                i = i + 1
            p.name = final_name
            for c in colors:
                t = p.colors.add()
                t.color = c
        return {"FINISHED"}

    def invoke(self, context, event):
        context.scene.cfr_temp_palette.clear()
        colors = get_colors_from_link(bpy.context.window_manager.clipboard)
        if colors:
            p = context.scene.cfr_temp_palette
            for c in colors:
                t = p.add()
                t.color = c
        else:
            self.report(
                {"WARNING"},
                "No Color Palette Found! (Copy url from coolors.co or colorhunt.co)",
            )
            return {"CANCELLED"}
        return context.window_manager.invoke_props_dialog(self)


class Selected_Palette(bpy.types.PropertyGroup):
    collection: bpy.props.StringProperty()
    palette: bpy.props.StringProperty()


class CFR_OT_Load_Palette(bpy.types.Operator):
    bl_idname = "cfr.loadpalette"
    bl_label = "Load Color Palette"
    bl_description = "Load Color Palette"
    bl_options = {"REGISTER", "UNDO"}
    palette: bpy.props.StringProperty(default="", options={"HIDDEN", "SKIP_SAVE"})
    collection: bpy.props.StringProperty(default="", options={"HIDDEN"})

    def execute(self, context):
        for a in preferences().saved_palettes:
            if a.name == self.collection:
                for p in a.palettes:
                    if p.name == self.palette:
                        context.scene.selected_pallet.collection = self.collection
                        context.scene.selected_pallet.palette = self.palette
        return {"FINISHED"}


class CFR_OT_Delete_Collection(bpy.types.Operator):
    bl_idname = "cfr.deletecollection"
    bl_label = "Delete Collection"
    bl_description = "Delete Collection"
    bl_options = {"REGISTER", "UNDO"}
    name: bpy.props.StringProperty(default="", options={"HIDDEN", "SKIP_SAVE"})

    def execute(self, context):
        index = preferences().saved_palettes.find(self.name)
        if index != None:
            preferences().saved_palettes.remove(index)
            if not os.path.isdir(
                os.path.join(
                    os.path.dirname(
                        os.path.dirname(
                            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        )
                    ),
                    "config",
                    "CFR_Palettes",
                )
            ):
                for f in os.listdir(
                    os.path.join(
                        os.path.dirname(
                            os.path.dirname(
                                os.path.dirname(
                                    os.path.dirname(os.path.abspath(__file__))
                                )
                            )
                        ),
                        "config",
                        "CFR_Palettes",
                    )
                ):
                    if f.split(".")[0] == self.name:
                        os.remove(
                            os.path.join(
                                os.path.dirname(
                                    os.path.dirname(
                                        os.path.dirname(
                                            os.path.dirname(os.path.abspath(__file__))
                                        )
                                    )
                                ),
                                "config",
                                "CFR_Palettes",
                                f"{self.name}.txt",
                            )
                        )
        return {"FINISHED"}


class CFR_OT_Delete_Palette(bpy.types.Operator):
    bl_idname = "cfr.deletepalette"
    bl_label = "Delete Color Palette"
    bl_description = "Delete Color Palette"
    bl_options = {"REGISTER", "UNDO"}
    collection: bpy.props.StringProperty(default="", options={"HIDDEN", "SKIP_SAVE"})
    name: bpy.props.StringProperty(default="", options={"HIDDEN", "SKIP_SAVE"})

    def execute(self, context):
        # print(self.collection)
        index = preferences().saved_palettes.find(self.collection)
        if index >= 0:
            index2 = preferences().saved_palettes[index].palettes.find(self.name)
            if (
                context.scene.selected_pallet.collection
                == preferences().saved_palettes[index].name
                and context.scene.selected_pallet.collection
                == preferences().saved_palettes[index].palettes[index2].name
            ):
                context.scene.selected_pallet.collection = ""
                context.scene.selected_pallet.palette = ""
            preferences().saved_palettes[index].palettes.remove(index2)

        return {"FINISHED"}


def Diff(li1, li2):
    return list(list(set(li1) - set(li2)) + list(set(li2) - set(li1)))


def get_loose_selections(obj):
    bpy.ops.mesh.hide(unselected=True)
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    verts = [v for v in bm.faces if v.select and not v.hide]
    unproccessed = set(verts[:])
    bpy.ops.mesh.select_all(action="DESELECT")
    selection_sets = []
    if unproccessed:
        vert = unproccessed.pop()
        while vert:
            vert.select = True

            bpy.ops.mesh.select_linked()
            selection_sets.append(
                [a.index for a in bm.faces if a.select and not a.hide]
            )
            for a in bm.faces:
                if a.select:
                    a.select = False
                    if a in unproccessed:
                        unproccessed.remove(a)
            if unproccessed:
                vert = unproccessed.pop()
            else:
                vert = None
    bpy.ops.mesh.reveal(select=False)
    deselect_all()
    return selection_sets
    print(selection_sets, len(selection_sets))


def get_loose_selections2(obj):
    mesh = obj.data
    bpy.ops.mesh.hide(unselected=True)
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    verts = [v for v in mesh.polygons if v.select and not v.hide]
    unproccessed = set(verts[:])
    for v in verts:
        v.select = False
    selection_sets = []
    vert = unproccessed.pop()
    # print(unproccessed)
    while vert:
        vert.select = True

        bpy.ops.mesh.select_linked()
        mesh.update()
        print("Appending", [a.index for a in mesh.polygons if a.select and not a.hide])
        selection_sets.append([a for a in mesh.polygons if a.select and not a.hide])
        for a in mesh.polygons:
            if a.select:
                a.select = False
                if a in unproccessed:
                    print("Removing", a.index)
                    unproccessed.remove(a)
        print("unproccessed", unproccessed)
        if unproccessed:
            vert = unproccessed.pop()
        else:
            vert = None
    bpy.ops.mesh.reveal(select=False)
    print(selection_sets, len(selection_sets))


def assignColor(data):
    # print("Hi")
    object, context, colors = data
    if not colors:
        context.scene.cfr_color = [random.random() for i in range(3)]
        r, g, b = context.scene.cfr_color
        col = mathutils.Color((r, g, b))
        col.v = 1
        context.scene.cfr_color = col
    else:
        context.scene.cfr_color = colors[random.randint(0, len(colors) - 1)]
    if object.type == "MESH":
        mesh = object.data
        if "CFR" not in [a.name for a in mesh.vertex_colors]:
            color_layer = mesh.vertex_colors.new(name="CFR")
        else:
            color_layer = mesh.vertex_colors["CFR"]
        r, g, b = context.scene.cfr_color
        object.cfr_color = context.scene.cfr_color
        # print(time.time()-st)
        a = np.tile([r, g, b, 1], len(color_layer.data))
        color_layer.data.foreach_set("color", a)
        # for data in color_layer.data:
        #    data.color = (r, g, b, 1.0)


import colorsys


def create_gradient(a, b, t):
    print(a.r / 255, a.g / 255, a.b / 255)
    print(b.r / 255, b.g / 255, b.b / 255)
    print(colorsys.rgb_to_hsv(a.r / 255, a.g / 255, a.b / 255))
    d = b.h - a.h
    if a.h > b.h:
        h3 = b.h
        b.h = a.h
        a.h = h3
        d = -d
        t = 1 - t

    if d > 0.5:
        a.h = a.h + 1
        h = (a.h + t * (b.h - a.h)) % 1

    if d <= 0.5:
        h = a.h + t * d
    return (
        (a.r + t * (b.r - a.r)) / 255,
        (a.g + t * (b.g - a.g)) / 255,
        (a.b + t * (b.b - a.b)) / 255,
    )


# print(create_gradient(mathutils.Color((250,250,110)),mathutils.Color((42,72,88)),0.5))
class CFR_OT_Random_Colors(bpy.types.Operator):
    bl_idname = "cfr.randomcolors"
    bl_label = "Random Colors"
    bl_description = "Set Random color for each object using color palette\nCTRL+LMB:Don't use color pallete"
    bl_options = {"REGISTER", "UNDO"}
    seed: bpy.props.IntProperty(default=1, name="Seed")
    create_mats: bpy.props.BoolProperty(
        default=False,
        name="Auto Create Materials",
        description="Create new materials if no material is found on the object",
    )
    auto_hide_wireframe: bpy.props.BoolProperty(
        default=True,
        name="Auto Hide Wireframe Objects",
        description="Automatically hide objects with display type wireframe for better preview",
    )
    select_children: bpy.props.BoolProperty(
        default=False,
        name="Color Empty's Children",
        description="Also color the objects parented to the empties in the selection",
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "seed")
        if context.mode != "EDIT_MESH" and context.scene.coloring_method == "Viewport":
            layout.prop(self, "create_mats")
        layout.prop(self, "auto_hide_wireframe")
        layout.prop(self, "select_children")

    def execute(self, context):
        if self.select_children:
            for obj in self.selected:
                try:
                    obj = bpy.data.objects[obj]

                    if obj.type == "EMPTY":
                        self.selected.extend(
                            [
                                ob.name
                                for ob in obj.children
                                if ob.type in {"MESH", "CURVE", "TEXT", "SURFACE"}
                            ]
                        )
                except:
                    pass
        if not self.selection_sets and not self.selected:
            self.report({"WARNING"}, "Nothing Selected!")
            return {"FINISHED"}
        st = time.time()
        if context.mode == "OBJECT":
            colors = []
            for o in context.scene.objects:
                o.select_set(False)

            random.seed(self.seed)
            if not self.ctrl:
                colors = get_colors_from_link(bpy.context.window_manager.clipboard)
                if context.scene.cfr_palettes != "Clipboard":
                    colors = [
                        tuple(c.color[:])
                        for c in get_colors_from_palette_name(
                            context.scene.selected_pallet.collection,
                            context.scene.selected_pallet.palette,
                        )
                    ]
            selected = [
                o
                for o in context.scene.objects
                if o.name in self.selected and o.type != "EMPTY"
            ]
            # object_sets_by_dimensions(selected)

            for s in selected:
                if not colors:
                    context.scene.cfr_color = [random.random() for i in range(3)]
                    r, g, b = context.scene.cfr_color
                    col = mathutils.Color((r, g, b))
                    col.v = 1
                    context.scene.cfr_color = col
                else:
                    context.scene.cfr_color = colors[random.randint(0, len(colors) - 1)]
                if context.scene.coloring_method == "Viewport":
                    if self.create_mats and not s.data.materials:
                        mat = bpy.data.materials.new(name="CFR_Material")
                        s.data.materials.append(mat)
                    for mat in s.data.materials:
                        if mat:
                            if colors:
                                mat.diffuse_color = colors[
                                    random.randint(0, len(colors) - 1)
                                ] + (1,)
                            else:
                                col = mathutils.Color(
                                    [random.random() for i in range(3)]
                                )
                                col.v = 1
                                mat.diffuse_color = (col.h, col.s, col.v, 1)
                            mat.roughness = 0.6
                elif context.scene.coloring_method == "Object":
                    r, g, b = context.scene.cfr_color
                    s.color = context.scene.cfr_color[:] + (1,)
                else:
                    if s.type == "MESH":
                        mesh = s.data
                        if "CFR" not in [a.name for a in mesh.vertex_colors]:
                            color_layer = mesh.vertex_colors.new(name="CFR")
                        else:
                            color_layer = mesh.vertex_colors["CFR"]
                        r, g, b = context.scene.cfr_color
                        s.cfr_color = context.scene.cfr_color

                        a = np.tile([r, g, b, 1], len(color_layer.data))
                        color_layer.data.foreach_set("color", a)
                        # for data in color_layer.data:
                        #    data.color = (r, g, b, 1.0)

                if self.auto_hide_wireframe and s.display_type == "WIRE":
                    s.hide_set(True)
            context.area.tag_redraw()
            # print(time.time()-st)
        else:
            random.seed(self.seed)
            for s in self.selection_sets:
                if not self.ctrl:
                    colors = get_colors_from_link(bpy.context.window_manager.clipboard)
                    if context.scene.cfr_palettes != "Clipboard":
                        colors = [
                            tuple(c.color[:])
                            for c in get_colors_from_palette_name(
                                context.scene.selected_pallet.collection,
                                context.scene.selected_pallet.palette,
                            )
                        ]
                if not colors:
                    context.scene.cfr_color = [random.random() for i in range(3)]
                    r, g, b = context.scene.cfr_color
                    col = mathutils.Color((r, g, b))
                    col.v = 1
                    context.scene.cfr_color = col
                else:
                    context.scene.cfr_color = colors[random.randint(0, len(colors) - 1)]
                selected = s
                # print("Coloring",selected)
                bpy.ops.object.editmode_toggle()
                mesh = context.active_object.data
                if "CFR" not in [a.name for a in mesh.vertex_colors]:
                    color_layer = mesh.vertex_colors.new(name="CFR")
                else:
                    color_layer = mesh.vertex_colors["CFR"]
                for poly in selected:
                    for idx in mesh.polygons[poly].loop_indices:
                        r, g, b = context.scene.cfr_color
                        color_layer.data[idx].color = (r, g, b, 1.0)
                bpy.ops.object.editmode_toggle()
                deselect_all()
        return {"FINISHED"}

    def invoke(self, context, event):
        self.selection_sets = []
        if context.mode == "EDIT_MESH":
            self.selection_sets = get_loose_selections(context.active_object)
        self.selection_sets = sorted(self.selection_sets, key=lambda x: len(x))
        self.ctrl = event.ctrl
        self.selected = [
            ob.name
            for ob in context.selected_objects
            if ob.type in {"MESH", "CURVE", "TEXT", "SURFACE", "EMPTY"}
        ]

        self.alt = event.alt
        return self.execute(context)


def disableOverlays(context):
    # overlays=[]
    props = context.scene.cfr_props
    overlays = [
        "show_annotation",
        "show_axis_x",
        "show_axis_y",
        "show_axis_z",
        "show_bones",
        "show_cursor",
        "show_curve_normals",
        "show_edge_bevel_weight",
        "show_edge_crease",
        "show_edge_seams",
        "show_edge_sharp",
        "show_edges",
        "show_extra_edge_angle",
        "show_extra_edge_length",
        "show_extra_face_angle",
        "show_extra_face_area",
        "show_extra_indices",
        "show_extras",
        "show_face_center",
        "show_face_normals",
        "show_face_orientation",
        "show_faces",
        "show_fade_inactive",
        "show_floor",
        "show_freestyle_edge_marks",
        "show_freestyle_face_marks",
        "show_look_dev",
        "show_motion_paths",
        "show_object_origins",
        "show_object_origins_all",
        "show_occlude_wire",
        "show_onion_skins",
        "show_ortho_grid",
        "show_outline_selected",
        "show_paint_wire",
        "show_relationship_lines",
        "show_split_normals",
        "show_stats",
        "show_statvis",
        "show_text",
        "show_vertex_normals",
        "show_weight",
        "show_wireframes",
        "show_wpaint_contours",
        "show_xray_bone",
        "use_gpencil_show_directions",
        "use_gpencil_show_material_name",
    ]
    save = []
    for overlay in overlays:
        # print(f"{overlay} : bpy.props.BoolProperty(default=False)")
        # save.append((overlay, getattr(context.space_data.overlay, overlay)))
        try:
            setattr(props, overlay, str(getattr(context.space_data.overlay, overlay)))
        except Exception:
            pass

        try:
            setattr(context.space_data.overlay, overlay, False)
        except Exception:
            pass

    return save


def enableOverlays(context):
    overlays = [
        "show_annotation",
        "show_axis_x",
        "show_axis_y",
        "show_axis_z",
        "show_bones",
        "show_cursor",
        "show_curve_normals",
        "show_edge_bevel_weight",
        "show_edge_crease",
        "show_edge_seams",
        "show_edge_sharp",
        "show_edges",
        "show_extra_edge_angle",
        "show_extra_edge_length",
        "show_extra_face_angle",
        "show_extra_face_area",
        "show_extra_indices",
        "show_extras",
        "show_face_center",
        "show_face_normals",
        "show_face_orientation",
        "show_faces",
        "show_fade_inactive",
        "show_floor",
        "show_freestyle_edge_marks",
        "show_freestyle_face_marks",
        "show_look_dev",
        "show_motion_paths",
        "show_object_origins",
        "show_object_origins_all",
        "show_occlude_wire",
        "show_onion_skins",
        "show_ortho_grid",
        "show_outline_selected",
        "show_paint_wire",
        "show_relationship_lines",
        "show_split_normals",
        "show_stats",
        "show_statvis",
        "show_text",
        "show_vertex_normals",
        "show_weight",
        "show_wireframes",
        "show_wpaint_contours",
        "show_xray_bone",
        "use_gpencil_show_directions",
        "use_gpencil_show_material_name",
    ]
    for overlay in overlays:
        if getattr(context.scene.cfr_props, overlay, ""):
            try:
                setattr(
                    context.space_data.overlay,
                    overlay,
                    eval(getattr(context.scene.cfr_props, overlay, False)),
                )
            except Exception:
                pass

            try:
                setattr(context.scene.cfr_props, "", False)
            except Exception:
                pass


def deselect_all():
    if bpy.context.mode == "OBJECT":
        bpy.ops.object.select_all(action="DESELECT")
    elif "EDIT" in bpy.context.mode:
        bpy.ops.mesh.select_all(action="DESELECT")


def hex_to_rgb(color_str):
    # supports '123456', '#123456' and '0x123456'
    (r, g, b), a = (
        map(lambda component: component / 255, bytes.fromhex(color_str[-6:])),
        1.0,
    )
    if preferences().convert_to_linear:
        return (srgb_to_linearrgb(r), srgb_to_linearrgb(g), srgb_to_linearrgb(b))
    else:
        return (r, g, b)


def srgb_to_linearrgb(c):
    if c < 0:
        return 0
    elif c < 0.04045:
        return c / 12.92
    else:
        return ((c + 0.055) / 1.055) ** 2.4


import math


def linearrgb_to_srgb(c):
    if c <= 0.0031308:
        c *= 12.92
    else:
        c = 1.055 * math.pow(c, 1.0 / 2.4) - 0.055
    return c


def get_colors_from_link(link):
    if "colorhunt" in link:
        color_string = link[link.index("palette/") + 8 :]
        color_parts = [color_string[i : i + 6] for i in range(0, len(color_string), 6)]
        colors = []
        for c in color_parts:
            colors.append(hex_to_rgb(c))
        return colors
    elif "coolors" in link:
        color_parts = link[link.index("coolors.co/") + 11 :].replace("/", "").split("-")
        colors = []
        for c in color_parts:
            colors.append(hex_to_rgb(c))
        return colors

    return None


show_wireframes = None
shading_type = None
render_pass = None
color_type = None
background_color = None
background_type = None
show_cavity = None
wireframe_opacity = None
gtao_distance = None
light_type = None
taa_samples = None
show_overlays = None
saved_overlays = []
wire_color = None
studio_light = None
preview_enabled = False
transparent = None


def create_wireframe_image(
    context,
    preview=False,
    animation=False,
    only_wireframe=False,
    output_format="PNG",
    custom_name="",
    add_ao=False,
    ao_strength=0.5,
):
    st = time.time()
    props = context.scene.cfr_props

    props.show_wireframes = str(context.space_data.overlay.show_wireframes)
    props.shading_type = context.space_data.shading.type
    props.render_pass = context.space_data.shading.render_pass
    props.color_type = context.space_data.shading.color_type
    props.background_color = context.space_data.shading.background_color
    props.background_type = context.space_data.shading.background_type
    # props.show_cavity = context.space_data.shading.show_cavity
    # print(context.space_data.shading.show_cavity,props.show_cavity)
    props.wireframe_opacity = context.space_data.overlay.wireframe_opacity
    props.gtao_distance = context.scene.eevee.gtao_distance
    props.light_type = context.space_data.shading.light

    props.taa_samples = context.scene.eevee.taa_samples
    props.show_overlays = str(context.space_data.overlay.show_overlays)
    props.wire_color = context.preferences.themes[0].view_3d.wire.copy()
    props.studio_light = context.space_data.shading.studio_light
    props.transparent = str(context.scene.render.film_transparent)
    props.view_transform = context.scene.view_settings.view_transform

    if preview:
        global saved_overlays

    saved_overlays = disableOverlays(context)
    if not preview:
        if context.area:
            if context.area.type == "VIEW_3D":
                if len([a for a in context.scene.objects if a.type == "CAMERA"]) != 0:
                    context.area.spaces[0].region_3d.view_perspective = "CAMERA"
                    try:
                        bpy.ops.view3d.view_center_camera()
                    except:
                        pass

    filename = bpy.path.basename(bpy.data.filepath)
    filename = os.path.splitext(filename)[0]
    blendname = bpy.path.basename(bpy.data.filepath).rpartition(".")[0]
    filepath = os.path.splitext(bpy.data.filepath)[0]
    if not filepath or preferences().save_all_to_default_path:
        filepath = preferences().default_path
    # print(filepath)
    fname = blendname if not custom_name else custom_name
    if not fname:
        fname = "Untitled"
    # if bpy.data.is_saved:
    if context.scene.cfr_render_directory.startswith("//"):
        context.scene.cfr_render_directory = bpy.path.abspath(
            context.scene.cfr_render_directory
        )
    if not context.scene.cfr_render_directory:
        if not os.path.exists(os.path.join(filepath, "ColorFrame Renders")):
            if not os.path.isdir(filepath):
                os.mkdir(filepath)
            os.mkdir(os.path.join(filepath, "ColorFrame Renders"))
        context.scene.cfr_render_directory = os.path.join(
            filepath, "ColorFrame Renders"
        )
    filepath = os.path.join(filepath, "ColorFrame Renders")
    if context.scene.cfr_render_directory and os.path.isdir(
        os.path.abspath(bpy.path.abspath(context.scene.cfr_render_directory))
    ):
        filepath = os.path.abspath(bpy.path.abspath(context.scene.cfr_render_directory))
    og_filepath = context.scene.render.filepath
    og_file_format = context.scene.render.image_settings.file_format
    og_format = context.scene.render.ffmpeg.format
    og_color_mode = context.scene.render.image_settings.color_mode
    if animation and output_format == "MP4":
        context.scene.render.image_settings.file_format = "FFMPEG"
        context.scene.render.ffmpeg.format = "MPEG4"
    else:
        context.scene.render.image_settings.file_format = "PNG"
        context.scene.render.image_settings.color_mode = "RGBA"
    # print(filepath)
    files = [file for file in os.listdir(filepath) if file.startswith(blendname)]
    i = 0
    name = fname
    while (
        fname
        + ("_ColorFrame." if not custom_name else ".")
        + ("mp4" if animation and output_format == "MP4" else "png")
    ) in files:
        fname = f"{name}_{i}"
        i += 1

    if preview:
        global \
            preview_enabled, \
            transparent, \
            studio_light, \
            wire_color, \
            show_wireframes, \
            shading_type, \
            render_pass, \
            color_type, \
            background_color, \
            background_type, \
            show_cavity, \
            wireframe_opacity, \
            gtao_distance, \
            light_type, \
            taa_samples, \
            show_overlays
        preview_enabled = True

    # print("Saved : ", wire_color)
    context.scene.render.film_transparent = context.scene.cfr_transparent
    context.preferences.themes[0].view_3d.wire = context.scene.cfr_wire_color
    context.space_data.overlay.show_overlays = True
    context.scene.eevee.taa_samples = 32
    context.space_data.shading.light = context.scene.shading_type
    context.space_data.shading.type = "SOLID" if not only_wireframe else "WIREFRAME"
    if (
        context.scene.shading_type == "STUDIO"
        and context.scene.coloring_method == "Viewport"
        and preview
        and not context.scene.cfr_props.switched_light_mode
    ):
        try:
            context.space_data.shading.studio_light = "outdoor.sl"
            context.scene.cfr_props.switched_light_mode = True
        except:
            pass
    # context.space_data.shading.show_cavity = False
    # print(props.show_cavity)
    context.space_data.overlay.wireframe_opacity = context.scene.cfr_wire_opacity
    context.scene.eevee.gtao_distance = 0.5
    try:
        context.scene.view_settings.view_transform = "Standard"
    except:
        pass
    context.space_data.overlay.show_wireframes = True
    if not only_wireframe:
        if context.scene.coloring_method == "Viewport":
            context.space_data.shading.color_type = "MATERIAL"
        elif context.scene.coloring_method == "Object":
            context.space_data.shading.color_type = "OBJECT"
        elif context.scene.coloring_method == "Textured":
            context.space_data.shading.color_type = "TEXTURE"
        else:
            context.space_data.shading.color_type = "VERTEX"
    # context.space_data.shading.color_type = 'MATERIAL' if context.scene.shading_type == 'STUDIO' and context.scene.use_metallic else 'VERTEX'
    context.space_data.shading.background_type = "VIEWPORT"
    context.space_data.shading.background_color = context.scene.cfr_bg_color
    context.scene.render.use_file_extension = True
    if not preview:
        # print(os.path.join(filepath,"ColorFrame Renders"))

        final_name = os.path.join(
            filepath, fname + ("_ColorFrame" if not custom_name else "")
        )

        context.scene.render.filepath = final_name
        view_data = context.space_data
        if animation:
            bpy.ops.render.opengl(
                "INVOKE_DEFAULT", write_still=True, animation=animation
            )
        else:
            bpy.ops.render.opengl(write_still=True, animation=animation)
        shading_type_before_ao = view_data.shading.type
        render_pass_before_ao = view_data.shading.render_pass
        if add_ao and not animation:
            ao_path = os.path.join(filepath, fname + ("_AO_ColorFrame"))
            view_data.shading.type = "MATERIAL"
            view_data.shading.render_pass = "AO"
            use_gtao = context.scene.eevee.use_gtao
            context.scene.eevee.use_gtao = True
            context.scene.render.filepath = ao_path
            bpy.ops.render.opengl(write_still=True, animation=animation)
            view_data.shading.render_pass = render_pass_before_ao
            view_data.shading.type = shading_type_before_ao
            context.scene.eevee.use_gtao = use_gtao
            ao_path = ao_path + ".png"
        final_name = final_name + ".png"

        if not animation:
            if os.path.isfile(final_name):
                image = bpy.data.images.load(final_name)
            if add_ao:
                if os.path.exists(ao_path):
                    add_ao_overlay(final_name, ao_path, ao_strength)
        # if not preview_enabled:
        #     if context.scene.cfr_props.background_type:
        #         disablepreview(context)

        # disablepreview(context)
        # enableOverlays(context, saved_overlays)

        # context.scene.eevee.taa_samples = taa_samples
        # bpy.context.scene.view_settings.view_transform = view_transform
        # bpy.context.space_data.shading.color_type = color_type
        # bpy.context.space_data.shading.background_color = background_color
        # bpy.context.space_data.shading.background_type = background_type
        # context.space_data.shading.show_cavity = show_cavity
        # context.space_data.overlay.wireframe_opacity = wireframe_opacity
        # context.scene.eevee.gtao_distance = gtao_distance
        # context.space_data.shading.type = shading_type
        # context.space_data.shading.render_pass = render_pass
        # context.space_data.overlay.show_wireframes = show_wireframes
        # context.space_data.overlay.show_overlays = show_overlays
        # bpy.context.space_data.shading.light = light_type
        # context.preferences.themes[0].view_3d.wire = wire_color
        # context.space_data.shading.studio_light = studio_light
        return final_name
    context.scene.render.filepath = og_filepath
    context.scene.render.image_settings.file_format = og_file_format
    context.scene.render.ffmpeg.format = og_format
    context.scene.render.image_settings.color_mode = og_color_mode
    return None
    # print(st-time.time())


class CFR_Saved_Props(bpy.types.PropertyGroup):
    switched_light_mode: bpy.props.BoolProperty(default=False)
    show_wireframes: bpy.props.StringProperty(default="")
    shading_type: bpy.props.StringProperty(default="")
    render_pass: bpy.props.StringProperty(default="")
    color_type: bpy.props.StringProperty(default="")
    background_color: bpy.props.FloatVectorProperty(size=3)
    background_type: bpy.props.StringProperty(default="")
    show_cavity: bpy.props.StringProperty(default="")
    wireframe_opacity: bpy.props.FloatProperty(default=1)
    gtao_distance: bpy.props.FloatProperty(default=0.5)
    light_type: bpy.props.StringProperty(default="")
    taa_samples: bpy.props.IntProperty(default=16)
    show_overlays: bpy.props.StringProperty(default="")
    wire_color: bpy.props.FloatVectorProperty(size=3)
    studio_light: bpy.props.StringProperty(default="")
    preview_enabled: bpy.props.StringProperty(default="")
    transparent: bpy.props.StringProperty(default="")
    view_transform: bpy.props.StringProperty(default="")
    show_edge_sharp: bpy.props.StringProperty(default="")
    show_annotation: bpy.props.StringProperty(default="")
    show_axis_x: bpy.props.StringProperty(default="")
    show_axis_y: bpy.props.StringProperty(default="")
    show_axis_z: bpy.props.StringProperty(default="")
    show_bones: bpy.props.StringProperty(default="")
    show_cursor: bpy.props.StringProperty(default="")
    show_curve_normals: bpy.props.StringProperty(default="")
    show_edge_bevel_weight: bpy.props.StringProperty(default="")
    show_edge_crease: bpy.props.StringProperty(default="")
    show_edge_seams: bpy.props.StringProperty(default="")
    show_edges: bpy.props.StringProperty(default="")
    show_extra_edge_angle: bpy.props.StringProperty(default="")
    show_extra_edge_length: bpy.props.StringProperty(default="")
    show_extra_face_angle: bpy.props.StringProperty(default="")
    show_extra_face_area: bpy.props.StringProperty(default="")
    show_extra_indices: bpy.props.StringProperty(default="")
    show_extras: bpy.props.StringProperty(default="")
    show_face_center: bpy.props.StringProperty(default="")
    show_face_normals: bpy.props.StringProperty(default="")
    show_face_orientation: bpy.props.StringProperty(default="")
    show_faces: bpy.props.StringProperty(default="")
    show_fade_inactive: bpy.props.StringProperty(default="")
    show_floor: bpy.props.StringProperty(default="")
    show_freestyle_edge_marks: bpy.props.StringProperty(default="")
    show_freestyle_face_marks: bpy.props.StringProperty(default="")
    show_look_dev: bpy.props.StringProperty(default="")
    show_motion_paths: bpy.props.StringProperty(default="")
    show_object_origins: bpy.props.StringProperty(default="")
    show_object_origins_all: bpy.props.StringProperty(default="")
    show_occlude_wire: bpy.props.StringProperty(default="")
    show_onion_skins: bpy.props.StringProperty(default="")
    show_ortho_grid: bpy.props.StringProperty(default="")
    show_outline_selected: bpy.props.StringProperty(default="")
    show_paint_wire: bpy.props.StringProperty(default="")
    show_relationship_lines: bpy.props.StringProperty(default="")
    show_split_normals: bpy.props.StringProperty(default="")
    show_stats: bpy.props.StringProperty(default="")
    show_statvis: bpy.props.StringProperty(default="")
    show_text: bpy.props.StringProperty(default="")
    show_vertex_normals: bpy.props.StringProperty(default="")
    show_weight: bpy.props.StringProperty(default="")
    show_wpaint_contours: bpy.props.StringProperty(default="")
    show_xray_bone: bpy.props.StringProperty(default="")
    use_gpencil_show_directions: bpy.props.StringProperty(default="")
    use_gpencil_show_material_name: bpy.props.StringProperty(default="")


def disablepreview(context, change_preview_state=True):
    # print(taa_samples,saved_overlays,view_transform)
    global preview_enabled  # , transparent, studio_light, wire_color, show_wireframes, shading_type, render_pass, color_type, background_color, background_type, show_cavity, wireframe_opacity, gtao_distance, light_type, taa_samples, show_overlays
    if change_preview_state:
        preview_enabled = False
        context.scene.cfr_preview_enabled = False

    props = context.scene.cfr_props
    enableOverlays(context)
    # print(props.color_type,props.shading_type)
    if props.gtao_distance != None:
        context.scene.eevee.gtao_distance = props.gtao_distance
        context.space_data.shading.type = props.shading_type
    if props.taa_samples != None:
        context.scene.eevee.taa_samples = props.taa_samples
    if props.color_type:
        context.space_data.shading.color_type = props.color_type
        props.color_type = ""
    if props.background_color != None:
        context.space_data.shading.background_color = props.background_color
    if props.background_type:
        context.space_data.shading.background_type = props.background_type
        props.background_type = ""
    # if props.show_cavity != None:
    #     context.space_data.shading.show_cavity = props.show_cavity
    if props.wireframe_opacity != None:
        context.space_data.overlay.wireframe_opacity = props.wireframe_opacity

    if props.render_pass:
        context.space_data.shading.render_pass = props.render_pass
        props.render_pass = ""
    if props.show_wireframes:
        context.space_data.overlay.show_wireframes = eval(props.show_wireframes)
        props.show_wireframes = ""
    if props.show_overlays:
        context.space_data.overlay.show_overlays = eval(props.show_overlays)
        props.show_overlays = ""
    if props.light_type:
        context.space_data.shading.light = props.light_type
        props.light_type = ""
    if props.wire_color != None:
        context.preferences.themes[0].view_3d.wire = props.wire_color
    if props.studio_light and (
        context.space_data.shading.light == "MATCAP"
        or context.space_data.shading.light == "FLAT"
        or context.space_data.shading.studio_light == "outdoor.sl"
    ):
        try:
            # print(props.studio_light)
            context.space_data.shading.studio_light = props.studio_light
            props.studio_light = ""
        except Exception as e:
            print(e)
    if props.transparent:
        context.scene.render.film_transparent = eval(props.transparent)
        props.transparent = ""
    if props.view_transform:
        try:
            context.scene.view_settings.view_transform = props.view_transform
        except:
            pass


def get_output_options(self, context):
    if self.animation:
        return (
            ("MP4", "MP4 (Black Background)", "MP4"),
            ("PNG", "PNG-Sequence (Transparent Background)", "PNG"),
        )
    else:
        return (("PNG", "PNG(Transparent Background)", "PNG"),)


class CFR_OT_Render_Advanced(bpy.types.Operator):
    bl_idname = "cfr.renderadvanced"
    bl_label = "Render Advanced"
    bl_description = "Render with more options"
    bl_options = {
        "REGISTER",
    }
    only_wireframe: bpy.props.BoolProperty(
        default=False,
        name="Only Wireframe",
        description="Render only the wireframes of the scene, excluding any objects.",
    )
    animation: bpy.props.BoolProperty(default=False, name="Animation")
    output_format: bpy.props.EnumProperty(
        items=get_output_options, name="Output Format"
    )
    name: bpy.props.StringProperty(default="", name="Output File Name")
    add_ao: bpy.props.BoolProperty(default=False, name="Add Ambient Occlusion")
    ao_strength: bpy.props.FloatProperty(
        default=0.5, min=0, max=1, name="AO Mix Strength"
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "only_wireframe")
        layout.prop(self, "animation")
        if self.animation:
            layout.prop(self, "output_format")
            if self.output_format == "PNG" and not context.scene.cfr_transparent:
                layout.label(
                    text="Make sure 'Transparent Background' is enabled, otherwise the background color will be applied!",
                    icon="INFO",
                )
        else:
            layout.prop(self, "add_ao")
            if self.add_ao:
                layout.prop(self, "ao_strength")
        layout.prop(self, "name")

    def execute(self, context):
        if context.scene.cfr_render_directory:
            if not os.path.isdir(
                os.path.abspath(bpy.path.abspath(context.scene.cfr_render_directory))
            ):
                self.report(
                    {"WARNING"},
                    f"Render Directory {context.scene.cfr_render_directory} does not exist",
                )
                return {"FINISHED"}
        elif bpy.data.is_saved and not preferences().auto_create_render_directory:
            self.report({"WARNING"}, f"Specify a valid Output Directory")
            return {"FINISHED"}
        if not self.animation:
            self.output_format = "PNG"
        for o in context.scene.objects:
            try:
                o.select_set(False)
            except:
                pass
        if len([a for a in context.scene.objects if a.type == "CAMERA"]) == 0:
            self.report({"WARNING"}, "No Camera found! Using View!")
            # return {'CANCELLED'}
        for s in [a for a in context.scene.objects if a.type == "MESH"]:
            if "CFR" in [a.name for a in s.data.vertex_colors]:
                s.data.vertex_colors["CFR"].active = True
        if context.scene.cfr_props.background_type:
            disablepreview(context, False)
        path = create_wireframe_image(
            context,
            animation=self.animation,
            only_wireframe=self.only_wireframe,
            output_format=self.output_format,
            custom_name=self.name,
            add_ao=self.add_ao,
            ao_strength=self.ao_strength,
        )
        context.scene.cfr_preview_enabled = True
        if path:
            self.report({"INFO"}, "Render Saved to: " + path)
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=600)


class CFR_OT_Render(bpy.types.Operator):
    bl_idname = "cfr.render"
    bl_label = "Render"
    bl_description = "Render Colorframe"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if context.scene.cfr_render_directory:
            if not os.path.isdir(
                os.path.abspath(bpy.path.abspath(context.scene.cfr_render_directory))
            ):
                self.report(
                    {"WARNING"},
                    f"Render Directory {context.scene.cfr_render_directory} does not exist",
                )
                return {"FINISHED"}
        elif bpy.data.is_saved and not preferences().auto_create_render_directory:
            self.report({"WARNING"}, f"Specify a valid Output Directory")
            return {"FINISHED"}

        for o in context.scene.objects:
            try:
                o.select_set(False)
            except:
                pass
        if len([a for a in context.scene.objects if a.type == "CAMERA"]) == 0:
            self.report({"WARNING"}, "No Camera found! Using View!")
            # return {'CANCELLED'}
        for s in [a for a in context.scene.objects if a.type == "MESH"]:
            if "CFR" in [a.name for a in s.data.vertex_colors]:
                s.data.vertex_colors["CFR"].active = True
        if context.scene.cfr_props.background_type:
            disablepreview(context, False)
        path = create_wireframe_image(context)
        context.scene.cfr_preview_enabled = True
        if path:
            self.report({"INFO"}, "Image Saved to: " + path)
        return {"FINISHED"}


class CFR_OT_RenderAnimation(bpy.types.Operator):
    bl_idname = "cfr.renderanimation"
    bl_label = "Render Animation"
    bl_description = "Render Colorframe Animation"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (
            len([a for a in context.scene.objects if a.type == "CAMERA"]) != 0
            and context.scene.camera
        )

    def execute(self, context):
        if context.scene.cfr_render_directory:
            if not os.path.isdir(
                os.path.abspath(bpy.path.abspath(context.scene.cfr_render_directory))
            ):
                self.report(
                    {"WARNING"},
                    f"Render Directory {context.scene.cfr_render_directory} does not exist",
                )
                return {"FINISHED"}
        elif bpy.data.is_saved and not preferences().auto_create_render_directory:
            self.report({"WARNING"}, f"Specify a valid Output Directory")
            return {"FINISHED"}
        for o in context.scene.objects:
            try:
                o.select_set(False)
            except:
                pass
        if len([a for a in context.scene.objects if a.type == "CAMERA"]) == 0:
            self.report({"WARNING"}, "No Camera found!")
            # return {'CANCELLED'}
        for s in [a for a in context.scene.objects if a.type == "MESH"]:
            if "CFR" in [a.name for a in s.data.vertex_colors]:
                s.data.vertex_colors["CFR"].active = True
        if context.scene.cfr_props.background_type:
            disablepreview(context, False)
        path = create_wireframe_image(context, animation=True)
        context.scene.cfr_preview_enabled = True
        if path:
            self.report({"INFO"}, "Video Saved to: " + path)
        return {"FINISHED"}


class CFR_OT_Update_Line_Art_Thickness(bpy.types.Operator):
    bl_idname = "cfr.updatelineartthickness"
    bl_label = "Update"
    bl_description = "Update line art thickness"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (
            len([a for a in context.scene.objects if a.type == "CAMERA"]) != 0
            and context.scene.camera
        )

    def execute(self, context):
        if bpy.app.version < (4, 3, 0):
            context.scene.cfr_line_art_object.data.layers[
                "Lines"
            ].line_change = context.scene.cfr_line_art_thickness
        else:
            context.scene.cfr_line_art_object.modifiers[
                0
            ].thickness = context.scene.cfr_line_art_thickness
        return {"FINISHED"}


import bmesh
import bgl
import gpu
from gpu_extras.batch import batch_for_shader


class CFR_OT_AddLineArt(bpy.types.Operator):
    bl_idname = "cfr.addlineart"
    bl_label = "Add Line Art"
    bl_description = "Add Grease pencil line art"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return context.scene.camera and context.mode == "OBJECT"

    def execute(self, context):
        if len([a for a in context.scene.objects if a.type == "CAMERA"]) != 0:
            context.area.spaces[0].region_3d.view_perspective = "CAMERA"
        if bpy.app.version >= (4, 3, 0):
            bpy.ops.object.grease_pencil_add(
                align="WORLD",
                location=(0, 0, 0),
                scale=(1, 1, 1),
                type="LRT_SCENE" if bpy.app.version <= (4, 1, 0) else "LINEART_SCENE",
                use_in_front=False,
                stroke_depth_offset=0.5,
            )
        else:
            bpy.ops.object.gpencil_add(
                align="WORLD",
                location=(0, 0, 0),
                scale=(1, 1, 1),
                type="LRT_SCENE" if bpy.app.version <= (4, 1, 0) else "LINEART_SCENE",
                use_in_front=False,
                stroke_depth_offset=0.5,
            )
        gp_object = context.active_object
        gp_object.name = "CFR Line Art"
        gp_object.hide_select = True
        context.scene.cfr_line_art_object = gp_object
        if bpy.app.version >= (4, 3, 0):
            line_art_mod = gp_object.modifiers[0]
        else:
            line_art_mod = gp_object.grease_pencil_modifiers[0]
        if bpy.app.version >= (4, 3, 0):
            gp_object.modifiers.new(type="GREASE_PENCIL_THICKNESS", name="Thickness")
            # gp_object.modifiers["Thickness"].use_uniform_thickness=True
            # gp_object.modifiers.new(type='GREASE_PENCIL_TINT',name='Tint')
        line_art_mod.use_material = True
        line_art_mod.use_crease_on_sharp = False
        line_art_mod.use_edge_overlap = True
        line_art_mod.use_overlap_edge_type_support = True
        line_art_mod.use_back_face_culling = True
        line_art_mod.use_fuzzy_intersections = True
        line_art_mod.use_fuzzy_all = True
        line_art_mod.use_detail_preserve = True
        line_art_mod.use_geometry_space_chain = True
        line_art_mod.use_material = True
        line_art_mod.thickness = 1
        gp_object.data.layers[0].tint_factor = 1
        if bpy.app.version >= (4, 3, 0):
            gp_object.data.layers[0].radius_offset = 1
        else:
            gp_object.data.layers[0].line_change = 1
        context.scene.cfr_line_art_enabled = True
        return {"FINISHED"}


class CFR_OT_TogglePreview(bpy.types.Operator):
    bl_idname = "cfr.togglepreview"
    bl_label = "Toggle Preview"
    bl_description = "Toggle Preview"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if context.scene.cfr_preview_enabled:
            bpy.ops.cfr.disablepreview("INVOKE_DEFAULT")
        else:
            bpy.ops.cfr.preview("INVOKE_DEFAULT")
        return {"FINISHED"}


class CFR_OT_Preview(bpy.types.Operator):
    bl_idname = "cfr.preview"
    bl_label = "Preview"
    bl_description = "Preview the Render"
    bl_options = {"REGISTER", "UNDO"}
    reenable: bpy.props.BoolProperty(default=False, options={"SKIP_SAVE", "HIDDEN"})

    def execute(self, context):
        # obj=context.active_object
        # obj_evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        # bm = bmesh.new()
        # bm.from_mesh(obj_evaluated.data)
        # coords = [obj_evaluated.matrix_world@v.co+v.normal*0.001 for v in bm.verts]
        # indices = [(e.verts[0].index,e.verts[1].index) for e in bm.edges if e.calc_face_angle(5)>0.3]
        # self.shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        # self.color=(0,0,0,1)
        # self.batch = batch_for_shader(self.shader, 'LINES', {"pos": coords},indices=indices)

        # self.mat=None
        # def draw():
        #     if self.shader is not None and self.batch is not None:
        #         bgl.glLineWidth(6)
        #         bgl.glEnable(bgl.GL_BLEND)
        #         bgl.glEnable(bgl.GL_DEPTH_TEST)
        #         bgl.glEnable(bgl.GL_LINE_SMOOTH)
        #         self.shader.bind()
        #         self.shader.uniform_float("color", self.color)
        #         self.batch.draw(self.shader)
        #         bgl.glDisable(bgl.GL_DEPTH_TEST)
        #         bgl.glDisable(bgl.GL_BLEND)
        # self.drawHandle=bpy.types.SpaceView3D.draw_handler_add(draw, (), 'WINDOW', 'POST_VIEW')
        enable_line_art = False

        # if context.scene.cfr_line_art_enabled:
        #     context.scene.cfr_line_art_enabled=False
        #     enable_line_art=True
        if not self.reenable:
            for o in context.scene.objects:
                try:
                    o.select_set(False)
                except:
                    pass
            if context.scene.coloring_method == "Vertex":
                for s in [a for a in context.scene.objects if a.type == "MESH"]:
                    if "CFR" in [a.name for a in s.data.vertex_colors]:
                        s.data.vertex_colors["CFR"].active = True
        if (
            context.scene.coloring_method == "Viewport"
            and not context.scene.cfr_props.switched_light_mode
        ):
            try:
                self.report(
                    {"INFO"},
                    "Lighting switched to recommended lighting mode!(Change back from the viewport shading settings)",
                )
            except:
                pass
        if context.scene.cfr_props.background_type:
            disablepreview(context)
        create_wireframe_image(context, preview=True)
        context.scene.cfr_preview_enabled = True
        if enable_line_art:
            context.scene.cfr_line_art_enabled = True
        return {"FINISHED"}


class CFR_OT_Disable_Preview(bpy.types.Operator):
    bl_idname = "cfr.disablepreview"
    bl_label = "Disable Preview"
    bl_description = "Disable Preview"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        for s in [a for a in context.scene.objects if a.type == "MESH"]:
            if "CFR" in [a.name for a in s.data.vertex_colors]:
                s.data.vertex_colors["CFR"].active = True
        if context.scene.cfr_props.background_type:
            disablepreview(context)
        context.scene.cfr_preview_enabled = False
        return {"FINISHED"}


class CFR_OT_Display_Message(bpy.types.Operator):
    bl_idname = "cfr.displaymessage"
    bl_label = "Display message"
    bl_options = {"REGISTER", "UNDO"}
    message: bpy.props.StringProperty(options={"SKIP_SAVE"})

    def execute(self, context):
        self.report({"WARNING"}, self.message)
        return {"FINISHED"}


class CFR_OT_Open_Directory(bpy.types.Operator):
    bl_idname = "cfr.opendirectory"
    bl_label = "View Renders"
    bl_description = "Open Render's Directory"
    bl_options = {"REGISTER"}

    def draw(self, context):
        self.layout.label(text="No Render Directory exists for this file")
        self.layout.label(text="Open Default Directory?")

    def execute(self, context):
        filepath = os.path.splitext(bpy.data.filepath)[0]
        if (
            not (
                context.scene.cfr_render_directory
                and os.path.isdir(
                    os.path.abspath(
                        bpy.path.abspath(context.scene.cfr_render_directory)
                    )
                )
            )
            or preferences().save_all_to_default_path
        ):
            filepath = preferences().default_path
        # if not os.path.exists(os.path.join(filepath, "ColorFrame Renders")):
        #     if not os.path.isdir(filepath):
        #         os.mkdir(filepath)
        #     os.mkdir(os.path.join(filepath, "ColorFrame Renders"))

        filepath = os.path.join(filepath, "ColorFrame Renders")
        if not os.path.exists(filepath):
            filepath = os.path.join(preferences().default_path, "ColorFrame Renders")
        if context.scene.cfr_render_directory:
            if not os.path.isdir(
                os.path.abspath(bpy.path.abspath(context.scene.cfr_render_directory))
            ):
                self.report(
                    {"WARNING"},
                    f"Render Directory {context.scene.cfr_render_directory} does not exist",
                )
                return {"FINISHED"}
            filepath = os.path.abspath(
                bpy.path.abspath(context.scene.cfr_render_directory)
            )
            if not os.path.exists(filepath):
                self.report({"WARNING"}, f"Render Directory {filepath} does not exist")
                return {"FINISHED"}
        bpy.ops.wm.path_open(filepath=filepath)
        return {"FINISHED"}

    def invoke(self, context, event):
        filepath = os.path.splitext(bpy.data.filepath)[0]
        if (
            filepath
            and not (
                context.scene.cfr_render_directory
                and os.path.isdir(
                    os.path.abspath(
                        bpy.path.abspath(context.scene.cfr_render_directory)
                    )
                )
            )
            and not preferences().save_all_to_default_path
        ):
            return context.window_manager.invoke_props_dialog(self)
        return self.execute(context)


class CFR_OT_Setup_CFR_Materials(bpy.types.Operator):
    bl_idname = "cfr.setupcfrmaterials"
    bl_label = "Setup Materials"
    bl_description = "Setup all materials in scene to use CFR colors"
    bl_options = {"REGISTER", "UNDO"}
    disable: bpy.props.BoolProperty(
        name="Disable", default=False, options={"SKIP_SAVE"}
    )

    @classmethod
    def description(cls, context: Context, properties: OperatorProperties) -> str:
        if properties.disable:
            return "Disable all CFR nodes in materials to return them to their original state"
        else:
            return "Setup all materials in scene to use CFR colors"

    def execute(self, context):
        if self.disable:
            context.scene.cfr_materials_enabled = False
            for object in context.scene.objects:
                try:
                    for mat in object.data.materials:
                        disable_cfr_material_setup(mat)
                except:
                    pass
        else:
            context.scene.cfr_materials_enabled = True
            for object in context.scene.objects:
                try:
                    for mat in object.data.materials:
                        add_cfr_material_setup(context, mat)
                except:
                    pass

        return {"FINISHED"}


class CFR_UL_Materials_UIList(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname
    ):
        view = item

        if self.layout_type in {"DEFAULT", "COMPACT"}:
            if view:
                row = layout.row()
                row.prop(view, "name", text="", emboss=False, icon_value=icon)
                row.prop(view, "cfr_metallic")

        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.label(text="", icon_value=icon)


classes = (
    CFR_OT_Display_Message,
    CFR_OT_Render_Advanced,
    CFR_OT_Update_Line_Art_Thickness,
    CFR_PT_LineArt,
    CFR_OT_AddLineArt,
    CFR_OT_TogglePreview,
    CFR_OT_Load_Palettes,
    CFR_OT_Delete_Palette,
    Selected_Palette,
    CFR_Saved_Props,
    CFR_Color,
    CFR_Palette,
    CFR_Palettes_Collections,
    CFR_UL_Materials_UIList,
    CFR_OT_Load_Palette,
    CFR_OT_Set_Color,
    CFR_PT_Colorframe_Renders,
    CFRPrefs,
    CFR_OT_Random_Colors,
    CFR_OT_RenderAnimation,
    CFR_OT_Render,
    CFR_OT_Random_Color_By_Collection,
    CFR_OT_Disable_Preview,
    CFR_OT_Preview,
    CFR_OT_Random_Color_By_Dimensions,
    CFR_OT_Save_Palette,
    CFR_OT_Delete_Collection,
    CFR_PT_Palettes,
    CFR_PT_Extras,
    CFR_OT_Open_Directory,
    CFR_OT_Setup_CFR_Materials,
)

icon_collection = {}
addon_keymaps = []


def color_update(self, context):
    mesh = self.data
    if "CFR" not in [a.name for a in mesh.vertex_colors]:
        color_layer = mesh.vertex_colors.new(name="CFR")
    else:
        color_layer = mesh.vertex_colors["CFR"]
    r, g, b = self.cfr_color
    # st=time.time()
    a = np.tile([r, g, b, 1], len(color_layer.data))
    color_layer.data.foreach_set("color", a)
    # for data in color_layer.data:
    #    data.color = (r, g, b, 1.0)
    # print(self.cfr_color)
    # print(time.time()-st)


def metallic_update(self, context):
    if self.cfr_metallic:
        self.metallic = 1
    else:
        self.metallic = 0


def coloring_method_update(self, context):
    reenable_preview(self, context)
    if preferences().auto_update_materials:
        for object in context.scene.objects:
            try:
                for mat in object.data.materials:
                    add_cfr_material_setup(
                        context, mat, context.scene.cfr_materials_enabled
                    )
            except:
                pass


def reenable_preview(self, context):
    if self.cfr_preview_enabled:
        bpy.ops.cfr.preview("INVOKE_DEFAULT", reenable=True)

    # else:
    #     bpy.ops.cfr.displaymessage('INVOKE_DEFAULT',message="Preview is disabled")


def get_palettes(self, context):
    return [
        ("Clipboard", "Clipboard", "Clipboard"),
    ] + [(p.name, p.name, p.name) for p in preferences().saved_palettes]


def update_line_art_thickness(self, context):
    return
    if preferences().auto_update_line_art_thickness:
        context.scene.cfr_line_art_object.data.layers[
            "Lines"
        ].line_change = self.cfr_line_art_thickness


def update_line_art_enabled(self, context):
    if self.cfr_line_art_object:
        if self.cfr_line_art_enabled:
            self.cfr_line_art_object.hide_set(False)
            self.cfr_line_art_object.hide_viewport = False
            self.cfr_line_art_object.hide_render = False
        else:
            self.cfr_line_art_object.hide_set(True)
            self.cfr_line_art_object.hide_viewport = True
            self.cfr_line_art_object.hide_render = True


def get_color(self, i):
    for a in bpy.data.materials:
        if a.user_of_id(self.id_data.original):
            return a.diffuse_color[i]


def append_node_group(name):
    asset_file = os.path.join(os.path.dirname(__file__), "Assets", "Assets.blend")
    with bpy.data.libraries.load(asset_file) as (data_from, data_to):
        data_to.node_groups = [ng for ng in data_from.node_groups if ng == name]
    return data_to.node_groups[0]


def get_cfr_node_group():
    if "CFR_NodeGroup" not in bpy.data.node_groups:
        ng = append_node_group("CFR_NodeGroup")
    return bpy.data.node_groups["CFR_NodeGroup"]


def add_cfr_material_setup(context, material, make_active=True):
    tree = material.node_tree
    if tree:
        if "CFR Node Group" not in tree.nodes:
            cfr_node_group = get_cfr_node_group()
            group_node = tree.nodes.new(type="ShaderNodeGroup")
            group_node.node_tree = cfr_node_group
            group_node.name = "CFR Node Group"
            group_node.location = 0, 1000

        else:
            group_node = tree.nodes["CFR Node Group"]
        if "CFR Material Output" not in tree.nodes:
            output_node = tree.nodes.new("ShaderNodeOutputMaterial")
            output_node.location = 200, 1000
            output_node.name = "CFR Material Output"
        else:
            output_node = tree.nodes["CFR Material Output"]
        color_attribute = group_node.node_tree.nodes["Color Attribute"]
        object_info = group_node.node_tree.nodes["Object Info"]
        group_input = group_node.node_tree.nodes["Group Input"]
        bsdf = group_node.node_tree.nodes["Principled BSDF"]
        links = bsdf.inputs["Alpha"].links
        for link in links:
            group_node.node_tree.links.remove(link)
        if context.scene.coloring_method == "Object":
            group_node.node_tree.links.new(
                object_info.outputs["Color"], bsdf.inputs["Base Color"]
            )
            group_node.node_tree.links.new(
                object_info.outputs["Alpha"], bsdf.inputs["Alpha"]
            )
        elif context.scene.coloring_method == "Vertex":
            group_node.node_tree.links.new(
                color_attribute.outputs["Color"], bsdf.inputs["Base Color"]
            )
            group_node.node_tree.links.new(
                color_attribute.outputs["Alpha"], bsdf.inputs["Alpha"]
            )
        else:
            group_node.node_tree.links.new(
                group_input.outputs["Color"], bsdf.inputs["Base Color"]
            )
            group_node.node_tree.links.new(
                group_input.outputs["Alpha"], bsdf.inputs["Alpha"]
            )

        tree.links.new(group_node.outputs[0], output_node.inputs[0])
        add_driver_to_input(material, group_node, 0)
        add_driver_to_input(material, group_node, 1)
        add_driver_to_input(material, group_node, 2)
        add_driver_to_input(material, group_node, 3)
        if make_active:
            output_node.is_active_output = True
        if context.scene.coloring_method == "Textured":
            disable_cfr_material_setup(material)


def disable_cfr_material_setup(material):
    tree = material.node_tree
    if tree and "CFR Material Output" in tree.nodes:
        output_node = tree.nodes["CFR Material Output"]
        output_node.is_active_output = False
        for node in tree.nodes:
            if node.bl_idname == "ShaderNodeOutputMaterial" and node != output_node:
                node.is_active_output = True


def add_driver_to_input(material, group_node, i):
    if i < 3:
        f_curve = group_node.inputs["Color"].driver_add(f"default_value", i)
        var_name = "Color"
    else:
        f_curve = group_node.inputs["Alpha"].driver_add(f"default_value")
        var_name = "Alpha"
    driver = f_curve.driver

    if var_name not in driver.variables:
        var = driver.variables.new()
        var.name = var_name
        var.targets[0].data_path = f"diffuse_color[{i}]"
        var.targets[0].id_type = "MATERIAL"
        var.targets[0].id = material
        driver.expression = var_name
    else:
        var = driver.variables[var_name]
        var.targets[0].data_path = f"diffuse_color[{i}]"
        var.targets[0].id_type = "MATERIAL"
        var.targets[0].id = material
        driver.expression = var_name
    # driver.type = "SCRIPTED"
    # driver.expression = f"get_color(self,{i})"
    # driver.use_self=True


@bpy.app.handlers.persistent
def register_drivers(a, b):
    bpy.app.driver_namespace["get_color"] = get_color


def register():
    from bpy.utils import register_class

    for cls in classes:
        register_class(cls)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    kmaps = [("cfr.togglepreview", "P", "shift")]

    km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
    if kc:
        for op, k, sp in kmaps:
            kmi = km.keymap_items.new(
                op,
                type=k,
                value="PRESS",
                alt="alt" in sp,
                shift="shift" in sp,
                ctrl="ctrl" in sp,
            )
            addon_keymaps.append((km, kmi))
    bpy.types.Scene.cfr_color = bpy.props.FloatVectorProperty(
        name="CFR Color",
        subtype="COLOR",
        soft_max=1,
        soft_min=0,
        default=[1.0, 1.0, 1.0],
    )
    bpy.types.Object.cfr_color = bpy.props.FloatVectorProperty(
        name="CFR Color",
        subtype="COLOR",
        soft_max=1,
        soft_min=0,
        default=[1.0, 1.0, 1.0],
        update=color_update,
    )
    bpy.types.Scene.cfr_wire_color = bpy.props.FloatVectorProperty(
        name="Wire Color",
        subtype="COLOR",
        soft_max=1,
        soft_min=0,
        default=[0.1, 0.1, 0.1],
        update=reenable_preview,
    )
    bpy.types.Scene.cfr_bg_color = bpy.props.FloatVectorProperty(
        name="Background Color",
        subtype="COLOR",
        soft_max=1,
        soft_min=0,
        default=[0.5, 0.5, 0.5],
        update=reenable_preview,
    )
    bpy.types.Material.cfr_metallic = bpy.props.BoolProperty(
        name="Metallic", default=False, update=metallic_update
    )
    bpy.types.Scene.use_metallic = bpy.props.BoolProperty(
        name="Use Viewport Colors", default=True, update=reenable_preview
    )
    bpy.types.Scene.coloring_method = bpy.props.EnumProperty(
        items=(
            ("Vertex", "Vertex", "Vertex"),
            ("Object", "Object", "Object"),
            ("Viewport", "Viewport", "Viewport"),
            ("Textured", "Textured", "Textured"),
        ),
        default=1,
        name="Coloring Method",
        update=coloring_method_update,
    )
    bpy.types.Scene.use_object_colors = bpy.props.BoolProperty(
        name="Use Object Colors", default=True, update=reenable_preview
    )
    bpy.types.Scene.cfr_wire_opacity = bpy.props.FloatProperty(
        default=0.7, min=0, max=1, name="WireFrame Opacity", update=reenable_preview
    )
    bpy.types.Scene.shading_type = bpy.props.EnumProperty(
        items=(
            ("FLAT", "FLAT", "FLAT"),
            ("MATCAP", "MATCAP", "MATCAP"),
            ("STUDIO", "STUDIO", "STUDIO"),
        ),
        default=2,
        name="Shading",
        update=reenable_preview,
    )
    bpy.types.Scene.cfr_palettes = bpy.props.EnumProperty(
        items=get_palettes, name="Palette", default=0, update=refresh_palette_names
    )
    bpy.types.Scene.cfr_temp_palette = bpy.props.CollectionProperty(type=CFR_Color)
    bpy.types.Scene.cfr_transparent = bpy.props.BoolProperty(
        default=False, name="Transparent Background", update=reenable_preview
    )
    bpy.types.Scene.cfr_props = bpy.props.PointerProperty(type=CFR_Saved_Props)
    bpy.types.Scene.selected_pallet = bpy.props.PointerProperty(type=Selected_Palette)
    bpy.types.Scene.cfr_preview_enabled = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.cfr_line_art_enabled = bpy.props.BoolProperty(
        default=False, name="Enable Line Art", update=update_line_art_enabled
    )
    bpy.types.Scene.cfr_line_art_object = bpy.props.PointerProperty(
        type=bpy.types.Object
    )
    bpy.types.Scene.cfr_line_art_thickness = bpy.props.IntProperty(
        default=1, name="Thickness", min=0, max=300, update=update_line_art_thickness
    )
    bpy.types.Scene.cfr_materials_enabled = bpy.props.BoolProperty(default=False)
    bpy.types.Scene.cfr_render_directory = bpy.props.StringProperty(
        name="Render Directory", default="", subtype="DIR_PATH"
    )
    loadPreferences()
    addon_update_checker.register("123aee8a17c993e71d1d1de18c2c5413")
    bpy.app.handlers.load_post.append(register_drivers)


def unregister():
    savePreferences()
    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    addon_update_checker.unregister()
    try:
        bpy.app.handlers.load_post.remove(register_drivers)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    register()
