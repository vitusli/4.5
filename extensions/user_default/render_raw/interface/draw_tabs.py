import bpy

def draw_tabs(layout, prop_parent, prop):
    current_value = getattr(prop_parent, prop)

    col = layout.column(align=True)
    row = col.row()
    row.emboss = 'NORMAL' # 'NORMAL', 'NONE', 'PULLDOWN_MENU', 'RADIAL_MENU', 'NONE_OR_STATUS'

    for option in prop_parent.bl_rna.properties[prop].enum_items:
        is_active = option.identifier == current_value

        col2 = row.column(align=True)
        op = col2.operator(
            "render.render_raw_switch_tabs",
            text = option.name,
            emboss = is_active,
            depress = False
        )
        op.prop = prop
        op.active = option.value

    col.separator(type='LINE', factor=0.2)
