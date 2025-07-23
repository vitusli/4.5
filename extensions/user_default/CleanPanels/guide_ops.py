import bpy
from bpy.types import Event
from bpy.props import StringProperty
from .Guides import Guides
from pathlib import Path
from .utils import preferences,draw_category,split_keep_substring,ALL_ICONS
class CP_OT_GuideShowHint(bpy.types.Operator):
    """Navigate to the previous page in the guide"""

    bl_idname = "cp.show_guide_hint"
    bl_label = "Show Hint"
    bl_description = "Show Hint"
    guide_id: StringProperty()

    def draw(self, context):
        self.current_page.draw_hint(self.layout, context)

    def execute(self, context):
        return {"FINISHED"}

    def invoke(self, context, event):
        ui_scale = bpy.context.preferences.view.ui_scale
        self.current_page = cp_guides[self.guide_id].current_page
        width = min(context.region.width / ui_scale, context.region.height / ui_scale)
        return context.window_manager.invoke_popup(self, width=min(600, int(width / 2)))


class CP_OT_GuidePrevPage(bpy.types.Operator):
    """Navigate to the previous page in the guide"""

    bl_idname = "cp.guide_prev_page"
    bl_label = "Previous Page"
    guide_id: StringProperty()

    def execute(self, context):
        cp_guides[self.guide_id].prev_page()
        return {"FINISHED"}


class CP_OT_GuideNextPage(bpy.types.Operator):
    """Navigate to the next page in the guide"""

    bl_idname = "cp.guide_next_page"
    bl_label = "Next Page"
    guide_id: StringProperty()

    def execute(self, context):
        cp_guides[self.guide_id].next_page()
        return {"FINISHED"}


class CP_OT_StartGuide(bpy.types.Operator):
    """Start Guide"""

    bl_idname = "cp.start_guide"
    bl_label = "Start Guide"
    guide_id: StringProperty()

    def execute(self, context):
        # guide=create_guide(self.guide_id)
        guide = cp_guides[self.guide_id]
        guide.start()
        preferences().space_type='VIEW_3D'
        return {"FINISHED"}


class CP_OT_SkipGuide(bpy.types.Operator):
    """Start Guide"""

    bl_idname = "cp.skip_guide"
    bl_label = "Skip Guide"
    guide_id: StringProperty()

    def invoke(self, context, event: Event):
        return context.window_manager.invoke_confirm(self, event)

    def execute(self, context):
        # guide=create_guide(self.guide_id)
        guide = cp_guides[self.guide_id]
        guide.start()
        guide.exit(force_end=True)
        return {"FINISHED"}


class CP_OT_ExitGuide(bpy.types.Operator):
    """Navigate to the next page in the guide"""

    bl_idname = "cp.exit_guide"
    bl_label = "Exit Guide"
    guide_id: StringProperty()

    def execute(self, context):
        cp_guides[self.guide_id].exit()
        # del cp_guides[self.guide_id]
        return {"FINISHED"}


classes = (
    CP_OT_GuideShowHint,
    CP_OT_GuidePrevPage,
    CP_OT_GuideNextPage,
    CP_OT_StartGuide,
    CP_OT_ExitGuide,
    CP_OT_SkipGuide,
)
cp_guides=Guides(Path(__file__).parent/"icons")
def create_draw_function(draw_delete_buttons,highlight=''):
    from . import icon_collection
    pcoll = icon_collection["icons"]
    def draw_create_first_category(layout, context):
        row = layout.column()
        for index, a in enumerate(getattr(preferences(), f"workspace_categories")):
            
            row.separator(factor=0.2)
            box = row.box()
            top_row=box.row(align=True)
            name_row=top_row.row(align=True)
            name_row.alignment = "LEFT"
            name_row.label(text=a.name)
            row2=top_row.row(align=True)
            row2.alignment = "RIGHT"
            if highlight=='Icon':
                row2.alert=True
            if a.icon in ALL_ICONS:
                op=row2.operator("cp.change_icon",text="Icon",icon=a.icon if a.icon else None)
            else:
                op=row2.operator("cp.change_icon",text="Icon",icon_value=pcoll[a.icon].icon_id)
            op.index=index
            op.is_guide=True
            if highlight=='Icon':
                row2.alert=False
            if highlight=='X':
                row2.alert=True
            op = row2.operator(f'cp.remove_category_from_workspace', text='',
                                        icon='PANEL_CLOSE')
            op.index = index
            if highlight=='X':
                row2.alert=False
            op = row2.operator('cp.movecategory', text='',
                                        icon='TRIA_UP')
            op.index = index
            op.category = 'workspace'
            op.direction='UP'
            op = row2.operator('cp.movecategory', text='',
                                        icon='TRIA_DOWN')
            op.index = index
            op.category = 'workspace'
            op.direction='DOWN'
            
            
            row1 = box.row()
            row1.prop(a, 'name', text="")
            row2 = row1.split(factor=0.5)
            row1 = box.row()
            row1 = row1.split(factor=0.8)
            row2 = row1.row()
            row1 = row1.split(factor=0.77)
            row2.prop(a, 'panels')
            if not a.panels:
                row2.enabled = False
            row3 = row1
            if highlight=='Add':
                row3.alert=True
            op=row3.operator("cp.search_popup_for_workspace", text="", icon="ADD", depress=True)
            op.index=index
            op.is_guide=True
            if highlight=='Add':
                row3.alert=False
            op = row3.operator('cp.reordercategory', text='', icon_value=icon_collection["icons"]['reorder'].icon_id)
            op.index = index
            op.category = 'WORKSPACE'
            op.exclusion_list = False
            if draw_delete_buttons:
                grid = box.grid_flow(columns=4, row_major=True)
                grid.alert=True
                for panel in split_keep_substring(a.panels):
                    if panel:
                        op = grid.operator("cp.remove_panel", text=panel, icon='PANEL_CLOSE')
                        op.index = index
                        op.panel = panel
                        op.category = "Workspace"
            # if not highlight=='Reorder':
            break
        else:
            row = layout.row()
            row.separator(factor=1)
            button_row = row.row(align=True)
            button_row.alignment = 'CENTER'
            op=button_row.operator("cp.add_category", icon="ADD")
            op.to = "Workspace"
            op.is_guide=True
        # if preferences().workspace_categories:
        #     row = layout.row(align=True)
        #     row.alignment = 'CENTER'
        #     row.alert = True
        #     row.label(text="Great! You've got a category! Next up, let's add addons to it!")
    return draw_create_first_category
def draw_exclusion_list(layout, context):
    row=layout.row()
    row.separator(factor=1)
    row1=row.row()
    row1=row1.split(factor=0.9)
    row2=row1.row()
    row2.prop(preferences(),f"addons_to_exclude")
                
    if not preferences().addons_to_exclude:
        row2.enabled=False
    row1.operator("cp.search_popup_for_exclude_list",text="",icon="ADD",depress=True).is_guide=True
    grid=layout.grid_flow(columns=4,row_major=True)
    for panel in split_keep_substring(getattr(preferences(),f"addons_to_exclude")):
        if panel:
            op=grid.operator("cp.remove_panel",text=panel,icon='PANEL_CLOSE')
            op.panel=panel
            op.category="ExclusionList"
def create_guide(id, force_reload=False):
    from . import icon_collection
    pcoll=icon_collection["icons"]
    guide = cp_guides.new_guide(id)
    
    
    if not force_reload:
        guide.from_json()

    if id == "preferences":
        # Start your journey by setting up where your awesome assets are located!
        page = guide.add_page("🎉 Welcome to Clean Panels! Ready to supercharge your Blender experience? 🚀")
        page = guide.add_page("First things first, let’s create your first filtering category! 🛠️")
        page.draw = create_draw_function(False)

        page = guide.add_page("Awesome! 🎉 You’ve created a category! Now, let’s fill it up! Click the + button and pick the addons you want to include. 🚀")
        page.draw = create_draw_function(False, 'Add')
        
        page = guide.add_page("Changed your mind? 🌀 You can remove addons by hitting those little x buttons below!")
        page.draw = create_draw_function(True)
        
        page = guide.add_page("Great! Next up, let’s Give your category a makeover! 🎨 Pick an icon that’ll shine in your viewport header!")
        page.draw = create_draw_function(False, 'Icon')
        page = guide.add_page("Just so you know, you can delete the category using the X button. But don’t do it now—go ahead and click the Next button instead! 😉")
        page.draw = create_draw_function(False, 'X')
        page = guide.add_page("Congrats! 🎉 You’ve just created your first category. It’ll show up in the top right corner of the viewport, where you can easily enable it! 👍")
        page.add_image(str(Path(__file__).parent/"icons"/"guide_images"/"Categories.png"))
        page = guide.add_page("Got favorite addons? 🌟 Add them to the exclusion list to keep them always in sight!")

        page.draw = draw_exclusion_list
        page=guide.add_page("Great news! 🎉 Click the 'Magic Setup' button to let Clean Panels automatically generate categories based on your installed addons.")
        page.add_operator("cp.autosetup",icon="SETTINGS",text="Magic Setup",op_props={"is_guide":True})
        page = guide.add_page("Woohoo! 🎉 You’re all set to dive into the world of Clean Panels magic! 🌟\n'Easy Mode' is on by default to keep things nice and simple. Some features are tucked away for now, but once you’re feeling confident, you can turn it off in the config settings!")

        page.add_operator(
            "wm.url_open",
            icon='HELP',
            text="Visit Documentation!",
            op_props={"url": "https://rantools.github.io/clean-panels/"},
        )
        page.add_operator(
            "wm.url_open",
            icon=pcoll['youtube'].icon_id,
            text="Youtube Tutorials!",
            op_props={
                "url": "https://www.youtube.com/channel/UCKgXKh-_kOgzdV8Q12kraHA"
            },
        )
        page.add_operator(
            "wm.url_open",
            icon=pcoll['discord'].icon_id,
            text="Join Discord",
            op_props={"url": "https://discord.gg/Ta4P3uJXtQ"},
        )
        page.add_operator(
            "wm.url_open",
            icon=pcoll['bm'].icon_id,
            text="Other Addons",
            op_props={"url": "https://blendermarket.com/creators/amandeep?ref=929"},
        )
        page.add_operator(
            "cp.exit_guide",
            icon="CHECKMARK",
            text="Exit Guide",
            op_props={"guide_id": id},
        )

    guide.to_json()
    guide.from_json()
    return guide
def register():
    create_guide("preferences", force_reload=False)
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
