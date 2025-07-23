'''
This module contains all of the interface classes for the addon. Sanctus Library UI can be found in the 3D viewport, shader editor and compositor.
'''

from . import auto_load as al
from .auto_load.common import *
from . import library_manager as lm
from . import operators as ops
from . import baking
from . import dev_info
from . import filters
from . import discounts
from . import constants
from . import panel_ui_sections as sections

SANCTUS_CONTEXT_PROP_NAME: str = 'sl_context_switch'

class DocButtons:

    def __init__(self, layout: bt.UILayout):
        r = layout.row(align=True)
        r.alignment = 'RIGHT'
        r.scale_y = 2.0
        r.scale_x = 2.0
        self.layout = r

    def documentation(self):
        ops.library.OpenDocumentation().draw_ui(self.layout, al.UIIcon(al.BIcon.QUESTION))
        return self

    def baking(self):
        ops.library.OpenBakingGuideLink().draw_ui(self.layout, al.UIIcon(al.BIcon.QUESTION))
        return self

    def discrod(self):
        ops.library.OpenDiscordLink().draw_ui(self.layout, al.UIIcon(lm.MANAGER.icon_id(Path('icons/icon'))))
        return self
    
    def patreon(self):
        ops.library.OpenPatreonLink().draw_ui(self.layout, al.UIIcon(lm.MANAGER.icon_id(Path("icons/patreon"))))
        return self
    
    def material_editor(self):
        ops.library.OpenMaterialEditorGuideLink().draw_ui(self.layout, al.UIIcon(al.BIcon.QUESTION))

    def shader_tools(self):
        ops.library.OpenShaderToolsGuideLink().draw_ui(self.layout, al.UIIcon(al.BIcon.QUESTION))


def draw_discount_codes(layout: bt.UILayout):
    if not discounts.has_codes():
        return

    col = al.UI.column(layout, align=True)
    for code, discount in discounts.CODES:
        op = ops.library.CopyText(text=code)

        al.UI.label(col, f'{discount}% OFF code', alignment=al.UIAlignment.CENTER, alert=True)
        op.draw_ui(col, al.UIOptionsOperator(text=code))
        col.separator()


def draw_purchase_info(layout: bt.UILayout):
    al.UI.label(layout, 'Get the Full Version:', alignment=al.UIAlignment.CENTER)
    al.UI.operator(
        layout,
        bpy.ops.wm.url_open,
        dict(url=constants.BLENDER_MARKET_PRODUCT_LINK), al.UIOptionsOperator(text='Blender Market'))
    al.UI.operator(
        layout,
        bpy.ops.wm.url_open,
        dict(url=constants.GUMROAD_PRODUCT_LINK), al.UIOptionsOperator(text='Gumroad'))

    draw_discount_codes(layout)


@al.register
class TogglableUI(bt.Panel):
    '''is the parent of the 3D viewport UI because it is possible to disable the main UI from the 3D viewport through the preferences.'''

    bl_region_type = 'UI'
    bl_space_type = 'VIEW_3D'
    bl_label = 'Sanctus Library Free' if dev_info.LITE_VERSION else 'Sanctus Library'
    bl_category = 'Sanctus'

    @classmethod
    def poll(cls, context):
        try:
            prefs = al.get_prefs()
            return prefs.interface().use_static_panel()
        except:
            return False

    def draw(self, context):  # function has to be defined to make this class registerable
        if dev_info.LITE_VERSION:
            draw_purchase_info(self.layout.box().column(align=True))

    def draw_header_preset(self, context: bt.Context):
        ops.library.ReloadLibrary().draw_ui(self.layout, al.UIOptionsProp(text='', icon=al.BIcon.FILE_REFRESH))
        if dev_info.DEVELOPER_MODE:
            ops.library.OpenPreferences().draw_ui(self.layout, al.UIOptionsOperator(text='', icon=al.BIcon.PREFERENCES))


@al.depends_on(TogglableUI)
@al.register
class View3DUI(bt.Panel):
    bl_idname = 'SL_PT_View3DPanel'
    bl_label = 'Viewport Panel'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id: str = TogglableUI.bl_idname

    def draw(self, context: bt.Context):
        l = self.layout

        lm.AssetClasses.draw(l)

        d: dict[str, sections.SanctusPanelSection] = {
            lm.AssetClasses.MATERIALS: sections.SanctusMaterialSection,
            lm.AssetClasses.GNTOOLS: sections.SanctusGNAssetsSection,
            lm.AssetClasses.DECALS: sections.SanctusDecalsSection,
        }
        sanctus_filters = filters.SanctusLibraryFilters.get_from(al.get_wm())
        if sanctus_filters.use_filters and lm.AssetClasses.get_active() == lm.AssetClasses.MATERIALS:
            sanctus_filters.draw(l.box())

        section = d[lm.AssetClasses.get_active()]

        section_layout = l.column()

        if bpy.app.version < section.minimum_blend_version:
            al.UI.label(
                section_layout,
                f"The {section.name} feature requires Blender Version {'.'.join(str(x) for x in section.minimum_blend_version)} or higher",
                icon=al.BIcon.ERROR
            )
        else:
            section.draw_ui(section_layout, context)

        DocButtons(section_layout).documentation().discrod().patreon()



@al.register
class BakingUI(bt.Panel):
    bl_idname = 'SL_PT_baking'
    bl_label = 'Material Baking'
    bl_description = 'Bake Settings for the Sanctus Library'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Sanctus'
    bl_order = 2

    @classmethod
    def poll(cls, context: al.BContext[bt.SpaceNodeEditor]):
        try:
            nt = context.space_data.edit_tree
            return (
                isinstance(nt, bt.ShaderNodeTree) 
                and nt in [mat.node_tree for mat in bpy.data.materials]
                and context.object is not None
                )
        except:
            return False

    def draw(self, context: bt.Context):
        l = self.layout

        baking_queue = baking.queue.BakingQueue.get_from(context.object)
        baking.ui.BakingQueueDrawer(baking_queue, l.box(), context).draw()
        manager = baking.texture_sets.TextureSetManager.get_from(context.scene)
        baking.ui.TextureSetManagerDrawer(manager, l.box(), context).draw()
        DocButtons(l).baking()


@al.register
class ShaderEditorUI(bt.Panel):
    bl_idname: str = 'SL_PT_ShaderEditor'
    bl_label: str = 'Shader Tools'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Sanctus'
    bl_order = 1

    @classmethod
    def poll(cls, context: al.BContext[bt.SpaceNodeEditor]):
        if not isinstance(context.space_data.edit_tree, bt.ShaderNodeTree):
            return False
        return True

    def draw(self, context: bt.Context):
        sections.SanctusShaderSection.draw_ui(self.layout, context)
        DocButtons(self.layout).shader_tools()


@al.register
class MaterialEditorUI(bt.Panel):
    bl_idname = 'SL_PT_MaterialEditor'
    bl_label = 'Material Editor'
    bl_description = ''
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Sanctus'
    bl_order = 0

    @classmethod
    def poll(cls, context: al.BContext[bt.SpaceNodeEditor]):
        if not isinstance(context.space_data.edit_tree, bt.ShaderNodeTree):
            return False
        return True
    
    def draw(self, context: bt.Context):
        l = self.layout
        sections.SanctusMaterialEditorSection.draw_ui(l, context)
        
        prefs = al.get_prefs()
        DocButtons(l).material_editor()
        


@al.register
class CompositorEditorUI(bt.Panel):
    bl_idname: str = 'SL_PT_CompositorEditor'
    bl_label: str = 'Sanctus Tools'
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = 'Sanctus'
    bl_order = 1

    @classmethod
    def poll(cls, context: al.BContext[bt.SpaceNodeEditor]):
        if not isinstance(context.space_data.edit_tree, bt.CompositorNodeTree):
            return False
        return True

    def draw(self, context: bt.Context):
        sections.SanctusCompositorSection.draw_ui(self.layout, context)

from . import preferences as pref
