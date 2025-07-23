'''
Implements the UI for both the `queue` and `texture_sets` modules
'''
from .. import auto_load as al
from ..auto_load.common import *

from . import utils

from . import queue
from . import texture_sets
from . import settings

@al.register_property(bt.WindowManager)
class SanctusIsBaking(al.BoolProperty):

    def __init__(self):
        return super().__init__(
            name='Is Baking',
            default=False
        )
    
    @classmethod
    def get(cls, parent: bt.WindowManager, attr_name: str = None):
        return super().get(parent, attr_name)




# QUEUE

class SocketPathDrawer(al.PropertyDrawer[queue.SocketPath]):

    def draw(self, bake_map: queue.BakeMap):
        target = self.target
        row = al.UI.row(self.layout, align=True)
        if target.is_valid_socket_path():
            al.UI.label(row, target.get_socket_path_formatted(), icon=al.BIcon.DOT)
            bake_map.socket_paths.get_remove_element(target).draw_ui(row, options=al.UIOptionsOperator(text='', icon=al.BIcon.REMOVE, emboss=False))
        else:
            bake_map.socket_paths.get_remove_element(target).draw_ui(al.UI.alert(row), al.UIOptionsOperator(text='Invalid Socket Path', icon=al.BIcon.ERROR, emboss=False))


class BakeMapDrawer(al.PropertyDrawer[queue.BakeMap]):

    context: al.BContext[bt.SpaceNodeEditor]

    def draw(self, queue: queue.BakingQueue):
        from . import operators
        target = self.target
        material = next(x for x in bpy.data.materials if x.node_tree == self.context.space_data.edit_tree)
        
        col = al.UI.column(self.layout, align=True)

        header_row = al.UI.row(col, align=True)

        if target.map_type() in utils.MapType.explicit():
            al.UI.label(header_row, target.get_map_name())
        else:
            target.other_name.draw_ui(header_row, al.UILabel(''))
        
        al.UI.popover(header_row, self, al.UIIcon(al.BIcon.SETTINGS))
        target.is_hidden.draw_as_icon_switch(header_row, al.BIcon.RESTRICT_RENDER_ON, al.BIcon.RESTRICT_RENDER_OFF, hide_highlighting=False, invert_value=True)
        queue.bake_maps.get_remove_element(target).draw_ui(header_row, al.UIIcon(al.BIcon.REMOVE))

        enable_add_sockets = target.is_material_available(material)
        if enable_add_sockets:
            operators.AddSocketToMap(bake_map=target).draw_ui(al.UI.enabled(col, enable_add_sockets), al.UIOptionsOperator(text='Add Socket', icon=al.BIcon.PLUS))

        for socket_path in target.socket_paths():
            SocketPathDrawer(socket_path, col, self.context).draw(target)

    def draw_panel(self):
        target = self.target
        col = al.UI.column(self.layout)
        col.use_property_split = True
        col.use_property_decorate = False

        target.map_type.draw_ui(col, al.UILabel("Type"))
        if not target.map_type() in utils.MapType.explicit():
            target.other_name.draw_ui(col)
            target.other_is_colorspace.draw_as_switch(col, 'Color', 'Non-Color')
        target.samples.draw_ui(col)
        target.is_hidden.draw_ui(col, al.UIOptionsProp(text='Enabled', invert_checkbox=True))


class BakingQueueSettingsDrawer(al.PropertyDrawer[queue.BakingQueueSettings]):

    def draw(self):
        from .. import decals

        target = self.target
        
        header = al.UI.row(self.layout, align=True)
        al.UI.label(header, '', icon=al.BIcon.SETTINGS)
        show_details = target.show_expanded.draw_as_dropdown(header, 'Settings', 'Settings...')

        if not show_details:
            return
        
        col = al.UI.column(self.layout, align=True)
        col.use_property_split = True
        col.use_property_decorate = False

        target.resolution_preset.draw_ui(col)
        if target.resolution_preset() == utils.ResolutionPreset.CUSTOM:
            target.custom_resolution.draw_ui(al.UI.row(col, align=True), al.UILabel(' '))

        target.use_auto_margin.draw_ui(col)
        if not target.use_auto_margin():
            target.margin.draw_ui(col)

        target.use_auto_bake_settings.draw_ui(col)
        if not target.use_auto_bake_settings():
            target.ray_distance.draw_ui(col)
        
        if len(decals.get_decal_children(self.context.object)) > 0:
            target.bake_decals.draw_ui(col)
        target.override_sets.draw_ui(col)


class BakingQueueDrawer(al.PropertyDrawer[queue.BakingQueue]):

    def draw(self):
        from . import operators
        target = self.target
        col = al.UI.column(self.layout)

        settings_layout = al.UI.column(col.box())
        BakingQueueSettingsDrawer(target.settings(), settings_layout, self.context).draw()

        col.separator()

        header = al.UI.row(col, align=False)
        al.UI.label(header, "Queue:")
        operators.Bake().draw_ui(header, al.UILabel('Baking...' if SanctusIsBaking.get(al.get_wm()).value else 'Bake'))
        if len(target.bake_maps()) > 0:
            operators.ClearBakingQueue().draw_ui(header, al.UIOptionsOperator(text='Clear', icon=al.BIcon.TRASH))
        
        maps_layout = al.UI.column(col, align=True)
        for x in target.bake_maps():
            row = al.UI.row(maps_layout.box(), align=True)
            BakeMapDrawer(x, row, self.context).draw(target)

        if target.has_map_overlap():
            al.UI.label(maps_layout, 'Overlapping map types. Cannot bake!', alert=True)

        operators.SelectSocketsForBaking().draw_ui(maps_layout)
        operators.AddNewEmptyMaps().draw_ui(maps_layout)




# TEXTURE SETS

class BakeTextureDrawer(al.PropertyDrawer[texture_sets.BakeTexture]):

    def draw(self, texture_set: texture_sets.TextureSet):
        from . import operators
        target = self.target
        row = al.UI.row(self.layout, align=True)

        if not target.is_valid():
            texture_set.textures.get_remove_element(target).draw_ui(al.UI.alert(row), al.UIOptionsOperator(text='Missing image. Data block has been removed', icon=al.BIcon.ERROR))
            return

        operators.PopupImage(image=target.texture()).draw_ui(row, al.UIOptionsOperator(text='', icon=target.texture().preview.icon_id))
        al.UI.label(row, target.map_id())


        operators.InstantiateImages(images=[target.texture()]).draw_ui(row, al.UIIcon(al.BIcon.NODE))
        operators.SaveBakeTexture(image=target.texture()).draw_ui(row, al.UIIcon(al.BIcon.DISC))
        texture_set.textures.get_remove_element(target).draw_ui(row, al.UIIcon(al.BIcon.REMOVE))


class TextureSetDrawer(al.PropertyDrawer[texture_sets.TextureSet]):
    
    def draw(self, manager: texture_sets.TextureSetManager):
        from . import operators

        target = self.target
        
        header_row = al.UI.row(self.layout, align=True)
        show_details = target.show_expanded.draw_as_dropdown(header_row, target.set_name(), f'{target.set_name()}...')
        al.UI.label(header_row, target.timecode.get_elapsed_time_formatted() + ' ago')

        buttons = al.UI.align(al.UI.row(header_row, align=True), al.UIAlignment.RIGHT)
        operators.InstantiateImages(images=[x.texture() for x in target.get_valid_textures()]).draw_ui(buttons, al.UIIcon(al.BIcon.NODE_SEL))
        operators.InstantiatePBRSetup(texture_set=target).draw_ui(buttons, al.UIIcon(al.BIcon.NODE_MATERIAL))
        operators.SaveTextureSet(texture_set=target).draw_ui(buttons, al.UIIcon(al.BIcon.FILE_TICK))
        manager.texture_sets.get_remove_element(target).draw_ui(buttons, al.UIIcon(al.BIcon.REMOVE))
        
        if not show_details:
            return

        col = al.UI.column(self.layout, align=True)
        for tex in target.textures():
            BakeTextureDrawer(tex, col, self.context).draw(target)


class TextureSetManagerDrawer(al.PropertyDrawer[texture_sets.TextureSetManager]):

    def draw(self):
        target = self.target
        obj = self.context.object

        header = al.UI.row(self.layout, align=True)
        al.UI.weighted_split(
            header,
            (lambda l: al.UI.label(l, 'Texture Sets:'), 0.6),
            (lambda l: al.UI.label(al.UI.align(l, al.UIAlignment.RIGHT), 'Sort by:'), 0.5),
            (lambda l: target.sorting.draw_ui(l, al.UILabel('')), 0.5),
            align=True
        )
        invert_sort = target.reverse_sorting.draw_as_icon_switch(header, al.BIcon.SORT_DESC, al.BIcon.SORT_ASC)
        header.separator()
        target.show_only_local_sets.draw_as_icon_switch(al.UI.row(header), al.BIcon.OBJECT_DATA, al.BIcon.WORLD, hide_highlighting=False)

        col = al.UI.column(self.layout, align=True)

        sort_method = target.sorting()

        sorted_sets = sorted(target.texture_sets(), key=lambda s: s.timecode.get_elapsed_time() if sort_method == utils.Sorting.DATE else s.set_name(), reverse=invert_sort)
        
        for texture_set in sorted_sets:
            if texture_set.set_name() != obj.name and target.show_only_local_sets():
                continue
            TextureSetDrawer(texture_set, col.box(), self.context).draw(target)




# SETTINGS

class BakingPreferencesDrawer(al.PropertyDrawer[settings.BakingPreferences]):
    
    def draw(self):
        target = self.target

        for x in (target.default_image_export_format,):
            al.UI.even_split(
                self.layout,
                lambda l: al.UI.label(l, x.ui_name + ':'),
                lambda l: x.draw_ui(l, al.UIOptionsProp(text=''))
            )

        self.layout.separator()
        col = al.UI.column(self.layout, align=True)
        al.UI.label(col, "Auto-detection of sockets for explicit bake map types:")
        col = al.UI.column(col.box(), align=True)
        for x in utils.MapType.explicit():
            row = al.UI.row(col, align=True)
            al.UI.label(row, f'{x.get_name()}:')
            al.UI.label(row, ', '.join(x.get_default_match().split(' ')))
