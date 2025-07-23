import bpy
from bpy.props import StringProperty
from bpy.types import Operator


class MBRIDGE_OT_options(Operator):
    bl_label = "Options"
    bl_idname = "mbridge.options"
    bl_options = {"REGISTER", "INTERNAL"}

    asset_id: StringProperty(options={"SKIP_SAVE", "HIDDEN"})

    @classmethod
    def description(cls, context, properties):
        return "Show options"

    def show_options(self, context, asset):
        def draw(self, context):
            layout = self.layout
            props = context.scene.mbridge

            # View3D specific options
            if context.area.type == "VIEW_3D":
                col = layout.column(align=True)

                if context.mode == "OBJECT":
                    # Asset type specific settings
                    if props.asset_type == "ASSETS":
                        col.prop(props.assets, "import_lods")
                        subcol = col.column()
                        subcol.active = props.assets.import_lods
                        subcol.prop(props.assets, "create_lod_group")
                    elif props.asset_type == "PLANTS":
                        col.prop(props.plants, "import_lods")
                        subcol = col.column()
                        subcol.active = props.plants.import_lods
                        subcol.prop(props.plants, "create_lod_group")
                    elif props.asset_type == "SURFACES":
                        col.prop(props.surfaces, "apply_material")
                        col.prop(props.surfaces, "mark_asset")

                    # Material edit option
                    layout.separator()
                    col = layout.column(align=True)
                    col.enabled = any(asset.id in mat.name for mat in bpy.data.materials)
                    col.operator("mbridge.material_edit", icon="MATERIAL").asset_id = asset.id

                elif context.mode == "PAINT_TEXTURE" and bpy.app.version < (4, 3, 0):
                    col.prop(props.brushes, "use_tex_mask")

            # Common options
            layout.operator("wm.path_open", icon="FILE_FOLDER", text="Open Folder").filepath = asset.path
            layout.separator()
            layout.operator("wm.url_open", icon="URL", text="View Online").url = f"https://quixel.com/assets/{asset.id}"

        context.window_manager.popup_menu(draw, title="Options", icon="QUESTION")

    def execute(self, context):
        props = context.scene.mbridge
        assets = props.get_assets(context)

        asset = next((a for a in assets if a.id == self.asset_id), None)
        if asset:
            self.show_options(context, asset)

        return {"FINISHED"}


classes = (MBRIDGE_OT_options,)
register, unregister = bpy.utils.register_classes_factory(classes)
