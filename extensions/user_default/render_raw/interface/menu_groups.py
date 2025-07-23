import bpy
from ..utilities.nodes import get_RR_groups

class GroupsMenu(bpy.types.Menu):
    bl_label = 'Render Raw Node Groups'
    bl_idname = 'RENDER_MT_render_raw_groups'

    def draw(self, context):
        GROUPS = get_RR_groups(context)

        col = self.layout.column()
        for group in GROUPS:
            op = col.operator('render.render_raw_refresh_active', text=group.name)
            op.Group = group.name

def register():
    bpy.utils.register_class(GroupsMenu)

def unregister():
    bpy.utils.unregister_class(GroupsMenu)