from ..utilities.version import get_addon_version, get_RR_node_version

def draw_upgrade_panel(self, layout, context, RR):
    VIEW = context.scene.view_settings

    layout.prop(VIEW, 'view_transform')
    layout.prop(VIEW, 'look')
    layout.prop(VIEW, 'exposure')
    layout.prop(VIEW, 'gamma')
    layout.separator()
    panel = layout.box()
    col = panel.column(align=False)
    row = col.row()
    row.alignment = 'CENTER'

    if not RR.group or (context.scene.use_nodes and not RR.in_scene):
        row.label(text='Node setup not found', icon='ERROR')
    else:
        row.label(text='Legacy node setup detected', icon='ERROR')
        row = col.row()
        row.alignment = 'CENTER'
        row.label(text=(
            f'Nodes are v{(get_RR_node_version(RR.group, pretty=True))} ' 
        ))
        row = col.row()
        row.alignment = 'CENTER'
        row.label(text=(
            f'Render Raw is v{get_addon_version(pretty=True)}'
        ))

    col.separator()
    col.operator('render.render_raw_upgrade_nodes', text='Upgrade Nodes', icon='FILE_REFRESH')
    col.operator('render.render_raw_disable', text='Disable Render Raw', icon='CHECKBOX_HLT')
    # col.operator('render.render_raw_disable', text='Delete Nodes and Disable', icon='TRASH')