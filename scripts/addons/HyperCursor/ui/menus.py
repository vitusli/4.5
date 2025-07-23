import bpy

from .. utils.workspace import get_3dview_area

from .. utils.asset import get_import_method_from_library_path
from .. utils.registration import get_prefs
from .. utils.tools import active_tool_is_hypercursor, get_active_tool
from .. utils.ui import get_icon

class MenuHyperCursorMeshContext(bpy.types.Menu):
    bl_idname = "MACHIN3_MT_hypercursor_mesh_context_menu"
    bl_label = "HyperCursor"

    def draw(self, context):
        layout = self.layout

        is_preview = context.active_object.HC.geometry_gizmos_show_previews
        select_mode = 'Face' if tuple(bpy.context.scene.tool_settings.mesh_select_mode) == (False, False, True) else 'Edge'

        layout.operator('machin3.toggle_gizmo_data_layer_preview', text=f"{'Disable' if is_preview else 'Enable'} Gizmo Preview")
        layout.operator('machin3.toggle_gizmo', text=f"Toggle {select_mode} Gizmo")

def mesh_context_menu(self, context):
    layout = self.layout

    valid_select_mode = tuple(bpy.context.scene.tool_settings.mesh_select_mode) in [(False, True, False), (False, False, True)]

    if get_active_tool(context).idname in ['machin3.tool_hyper_cursor', 'machin3.tool_hyper_cursor_simple'] and valid_select_mode:

        layout.menu("MACHIN3_MT_hypercursor_mesh_context_menu")
        layout.separator()

def modifier_buttons(self, context):
    if get_prefs().show_mod_panel:
        layout = self.layout

        active = context.active_object

        if active and active.modifiers:
            box = layout.box()
            column = box.column(align=True)

            if active.library or (active.data and active.data.library):
                split = column.split(factor=0.25, align=True)
                split.separator()

                row = split.row()
                row.alignment = 'CENTER'
                row.label(text=f"Object {'Data ' if not active.library and active.data and active.data.library else ''}is Linked", icon_value=get_icon('error'))

            row = column.split(factor=0.25, align=True)
            row.label(text='All')
            op = row.operator('machin3.toggle_all_modifiers', text='Toggle', icon='RESTRICT_VIEW_OFF')
            op.active_only = False
            op = row.operator('machin3.apply_all_modifiers', text='Apply', icon='IMPORT')
            op.active_only = False
            op = row.operator('machin3.remove_all_modifiers', text='Remove', icon='X')
            op.active_only = False

            active = context.active_object
            booleans = [mod for mod in active.modifiers if mod.type == 'BOOLEAN']

            if booleans:
                row = column.split(factor=0.24, align=True)
                row.label(text='Boolean')
                row.operator('machin3.remove_unused_booleans', text='Remove Unused', icon='MOD_BOOLEAN')

def asset_browser_import_method_warning(self, context):
    is_hypercursor_active = False

    area = get_3dview_area(context)

    if area:
        try:
            with context.temp_override(area=area):
                is_hypercursor_active = active_tool_is_hypercursor(context)
        except:
            pass

    if is_hypercursor_active:
        space = context.space_data

        libref = space.params.asset_library_reference
        libpath = space.params.directory.decode('utf-8')
        import_method = space.params.import_method

        if libref == 'HyperCursor Examples':

            if import_method == 'FOLLOW_PREFS':
                import_method = get_import_method_from_library_path(context, libpath)

            if import_method == 'LINK':
                self.layout.separator(factor=1)
                row = self.layout.row(align=True)
                row.scale_x = 1.3
                row.operator('machin3.set_asset_import_method_append', text='', icon_value=get_icon('error'))

            elif import_method == 'APPEND_REUSE':
                self.layout.separator(factor=1)
                row = self.layout.row(align=True)
                row.scale_x = 1.3
                row.operator('machin3.set_asset_import_method_append', text='', icon='INFO_LARGE')
