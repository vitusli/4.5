from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active as view3d_tools

from . property import step_list
from . registration import get_prefs

from .. items import tool_name_mapping_dict

def get_tools_from_context(context):
    tools = {}

    active = view3d_tools.tool_active_from_context(context)

    show_toolbar = getattr(context.space_data, 'show_region_toolbar', None) if getattr(context, 'space_data', False) else False

    if active:

        idx = 0

        for tool in view3d_tools.tools_from_context(context):
            if tool:
                if type(tool) is tuple:
                    sub_idx = 0

                    for subtool in tool:
                        if subtool:
                            tools[subtool.idname] = {'name': subtool.idname,
                                                     'label': subtool.label,
                                                     'icon': subtool.icon,
                                                     'icon_value': view3d_tools._icon_value_from_icon_handle(subtool.icon),
                                                     'active': subtool.idname == active.idname,
                                                     'idx': idx,
                                                     'is_grouped': True,

                                                     'active_within_group': view3d_tools._tool_group_active_get_from_item(tool) == sub_idx if show_toolbar else subtool.idname == active.idname if active.idname in [st.idname for st in tool] else sub_idx == 0}
                            sub_idx += 1

                else:
                    tools[tool.idname] = {'name': tool.idname,
                                          'label': tool.label,
                                          'icon': tool.icon,
                                          'icon_value': view3d_tools._icon_value_from_icon_handle(tool.icon),
                                          'active': tool.idname == active.idname,
                                          'idx': idx,
                                          'is_grouped': False,
                                          'active_within_group': False}

                idx += 1

    return tools

def get_active_tool(context):
    return view3d_tools.tool_active_from_context(context)

def get_tool_options(context, tool_idname, operator_idname):
    for tooldef in context.workspace.tools:
        if tooldef and tooldef.idname == tool_idname:
            if tooldef.mode == context.mode:
                try:
                    return tooldef.operator_properties(operator_idname)
                except:
                    return None

def get_next_switch_tool(context, active_tool=None, tools=None):
    if active_tool is None:
        active_tool = get_active_tool(context).idname

    if tools is None:
        tools = get_tools_from_context(context)

    name = 'builtin.select_box'

    switch_tools = [name.strip() for name in get_prefs().tools_switch_list.split(',') if name.strip() in tools]

    if switch_tools:

        if active_tool in switch_tools:
            name = step_list(active_tool, switch_tools, step=1, loop=True)

        elif switch_tools:
            name = switch_tools[0]

    return name, tools[name]['label'], tools[name]['icon_value']

def prettify_tool_name(name):
    if name in tool_name_mapping_dict:
        return tool_name_mapping_dict[name]
    return name
