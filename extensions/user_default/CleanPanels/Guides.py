import os
import json
from typing import Union
from bpy.types import UILayout, ImagePreview, Context
import textwrap
import bpy
from pathlib import Path
from .modules.t3dn_bip import previews
from bpy.utils import previews as bpy_previews
def row_left_right(layout: UILayout):
    og_row = layout.row()
    rowl, rowr = og_row.row(), og_row.row()
    rowl.alignment = "LEFT"
    rowr.alignment = "RIGHT"
    return rowl, rowr


def message_box(layout, context, message, width=None):
    text_box = layout.column()
    text_box.alignment = "CENTER"
    width = width or context.region.width
    if not message:
        return
    for line in message.split("\n"):
        lines = textwrap.wrap(line, width / 10 if context else 100, break_long_words=False)
        for l in lines:
            trow = text_box.row()
            trow.alert=True
            trow.alignment = "CENTER"
            trow.label(text=l)
            # new_row.scale_x=0.3
            # new_row.label(text='',icon='FAKE_USER_OFF')


def button_with_icon(
    layout: UILayout,
    operator: str,
    text: str,
    emboss: bool = True,
    depress: bool = False,
    icon: str = None,
    icon_value: int = 0,
    icon_align="LEFT",
    props={},
):
    op = None

    layout = layout.row(align=True)
    layout.ui_units_x = 3
    if icon_align == "LEFT":
        if icon_value:
            op = layout.operator(operator, text="", emboss=emboss, depress=depress, icon_value=icon_value)
        else:
            op = layout.operator(
                operator,
                text="",
                icon=icon if icon else "NONE",
                emboss=emboss,
                depress=depress,
            )
        op2 = layout.operator(operator, text=text, emboss=False)
    else:
        op2 = layout.operator(operator, text=text, emboss=False)
        if icon_value:
            op = layout.operator(operator, text="", icon_value=icon_value, emboss=emboss, depress=depress)
        else:
            op = layout.operator(
                operator,
                text="",
                icon=icon if icon else "NONE",
                emboss=emboss,
                depress=depress,
            )
    for k, v in props.items():
        setattr(op, k, v)
        setattr(op2, k, v)
    return op


class GuidePage:
    def __init__(self, label, data: "Guides"):
        self.data = data
        self.label = label
        self.items = []
        self.hint_label = ""
        self.hint_text = ""
        self.hint_image: ImagePreview = None

    def add_operator(
        self,
        operator_string: str,
        op_props: dict = None,
        icon: str = "NONE",
        text: str = None,
    ):
        """
        Adds an operator to the page.

        Args:
            operator_string (str): The string representation of the operator.
            op_props (dict, optional): Additional properties of the operator. Defaults to None.
            icon (str, optional): The icon associated with the operator. Defaults to 'NONE'.
            text (Any, optional): The text associated with the operator. Defaults to None.

        Returns:
            None
        """
        if op_props is None:
            op_props = {}
        self.items.append(
            {
                "type": "operator",
                "operator_string": operator_string,
                "op_props": op_props,
                "icon": icon,
                "text": text,
            }
        )

    def add_property(self, prop_data, property: str, icon="NONE"):
        """
        Add a property to the page.

        Parameters:
            prop_data (dict): The property data to be added.
            property (str): The name of the property.
            icon (str): The icon associated with the property. Default is 'NONE'.
        """
        self.items.append(
            {
                "type": "property",
                "prop_data": prop_data,
                "property": property,
                "icon": icon,
            }
        )

    def add_label(self, label: str):
        """
        Adds a label to the page.

        Parameters:
            label (str): The label to be added.

        Returns:
            None
        """
        self.items.append({"type": "label", "label": label})

    def add_image(self, img_path: str):
        """
        Add an image to the page.

        Parameters:
            img_path (str): The path to the image file.

        Returns:
            None
        """
        name = os.path.basename(img_path)
        image = self.data.previews.load_safe(name, img_path, "IMAGE")
        self.items.append({"type": "image", "image": image})

    def set_hint_image(self, img_path: Union[str, Path]):
        """
        Set the hint image for the page.

        Parameters:
            img_path (str): The path to the image file.

        Returns:
            None
        """
        if os.path.exists(img_path):
            img_path = str(img_path)
            name = os.path.basename(img_path)
            self.hint_image = self.data.previews.load_safe(name, img_path, "IMAGE")

    def draw_hint(self, layout: UILayout, context: Context):
        """
        Draws a hint in the specified layout based on the context provided.

        Parameters:
            layout (UILayout): The layout in which the hint will be drawn.
            context: The context in which the hint is being drawn.

        Returns:
            None
        """
        ui_scale = bpy.context.preferences.view.ui_scale
        width = min(context.region.width, context.region.height)
        region_width = min(600, int(width / 2)) / ui_scale
        scale = region_width / 20
        if self.hint_text:
            message_box(
                layout,
                context,
                self.hint_text,
                width=min(600, int(width / (ui_scale * 1.2))),
            )
        if self.hint_image:
            if scale * ui_scale < 15:
                message_box(
                    layout,
                    context,
                    "Make the window bigger to see a larger image!Make the window bigger to see a larger image!",
                    width=min(600, int(width / (ui_scale * 1.2))),
                )
            layout.template_icon(icon_value=self.hint_image.icon_id, scale=scale)

    def draw(self, layout: UILayout, context: Context = None):
        """
        Draw the UI layout based on the given layout and context.

        Parameters:
            layout (UILayout): The UI layout to draw.
            context (Context, optional): The context to draw in. Defaults to None.
        """
        row = layout.row()
        row.alignment = "CENTER"
        for item in self.items:
            if item["type"] == "operator":
                if item["text"] != None:
                    op = row.operator(
                        item["operator_string"],
                        icon=item["icon"] if isinstance(item["icon"], str) else "NONE",
                        icon_value=item["icon"] if isinstance(item["icon"], int) else 0,
                        text=item["text"],
                    )
                else:
                    op = row.operator(
                        item["operator_string"],
                        icon=item["icon"] if isinstance(item["icon"], str) else "NONE",
                        icon_value=item["icon"] if isinstance(item["icon"], int) else 0,
                    )
                for k, v in item["op_props"].items():
                    setattr(op, k, v)
            elif item["type"] == "property":
                prop_data = item["prop_data"]
                if isinstance(prop_data, str):
                    prop_data = eval(prop_data)
                row.prop(prop_data, item["property"], icon=item["icon"])
            elif item["type"] == "label":
                row = layout.column()
                message_box(row, context, item["label"])
            elif item["type"] == "image":
                row = layout.column()
                ui_scale = bpy.context.preferences.view.ui_scale
                region_width = context.region.width * ui_scale
                scale = int(region_width / 100)
                row.template_icon(icon_value=item["image"].icon_id, scale=scale)


class Guide:
    def __init__(self, guide_id, data: "Guides"):
        self.data = data
        self.id = guide_id
        self.json_path = data.guides_json_dir / f"{self.id}.json"

        self.pages = []
        self.current_page_index = 0
        self.showing = False
        self.hidden = False
        self.started_once = False
        self.finished_once = False

    def add_page(self, label: str):
        page = GuidePage(label, self.data)
        self.pages.append(page)
        return page

    def draw(self, layout, context=None):
        if not self.showing:
            return
        layout = layout.box()
        if not self.pages:
            return
        rowl, rowr = row_left_right(layout)
        # rowl.operator("cp.guide_prev_page",icon_value=self.data.icons['prev'],text="Back",emboss=False).guide_id=self.id
        button_with_icon(
            rowl,
            "cp.guide_prev_page",
            icon_value=self.data.icons["prev"],
            text="Back",
            emboss=False,
            icon_align="LEFT",
            props={"guide_id": self.id},
        )
        if self.current_page_index == 0:
            rowl.enabled = False
        if self.current_page.hint_text:
            rowr.operator(
                "cp.show_guide_hint",
                icon="QUESTION",
                text=self.current_page.hint_label,
            ).guide_id = self.id
        button_with_icon(
            rowr,
            "cp.guide_next_page",
            icon_value=self.data.icons["next"],
            text="Next",
            emboss=False,
            icon_align="RIGHT",
            props={"guide_id": self.id},
        )
        # rowr.operator("cp.guide_next_page",icon_value=self.data.icons['next'],text="Next",emboss=False).guide_id=self.id
        if self.current_page_index >= len(self.pages) - 1:
            rowr.enabled = False
        

        current_page = self.pages[self.current_page_index]

        message_box(layout, context, current_page.label)
        current_page.draw(layout, context)
        rowl, rowr = row_left_right(layout)
        rowl.label(
            text=f"Guide (Page:{self.current_page_index+1}/{len(self.pages)})",
            icon_value=self.data.icons["guide"],
        )

        # rowr.operator("cp.exit_guide",icon_value=self.data.icons['exit'],text="Exit").guide_id=self.id
        rowr.alert = True
        rowr.operator("cp.exit_guide", icon="PANEL_CLOSE", text="").guide_id = self.id

    def next_page(self):
        self.current_page_index = (self.current_page_index + 1) % len(self.pages)
        self.to_json()

    def prev_page(self):
        self.current_page_index = (self.current_page_index - 1) % len(self.pages)
        self.to_json()
    def set_page(self, page_index: int):
        self.current_page_index = page_index
        self.to_json()
    def start(self):
        self.showing = True
        self.started_once = True
        self.to_json()

    def exit(self, force_end=False):
        self.showing = False
        self.hidden = True
        if force_end:
            self.current_page_index = len(self.pages) - 1
        if self.current_page_index >= len(self.pages) - 1:
            self.finished_once = True
        if self.current_page_index >= len(self.pages) - 1:
            self.current_page_index = 0
        self.to_json()

    def from_json(self, json_file=None):
        if json_file is None:
            json_file = self.json_path
        if not os.path.exists(json_file):
            return None
        with open(json_file, "r") as file:
            data = json.load(file)
            # self.pages = [GuidePage(page["label"]) for page in data['pages']]max_size
            # for page, page_data in zip(self.pages, data['pages']):
            #     for item in page_data['items']:
            #         page.items.append(item)
            self.current_page_index = data.get("current_page_index", 0)
            # self.showing=data.get('showing',True)
            self.started_once = data.get("started_once", True)
            self.finished_once = data.get("finished_once", False)
        return self

    def to_json(self):
        # data = {'showing':self.showing,'pages': [{"label": page.label, "items": page.items} for page in self.pages], 'current_page_index': self.current_page_index}
        data = {
            "showing": self.showing,
            "current_page_index": self.current_page_index,
            "started_once": self.started_once,
            "finished_once": self.finished_once,
        }
        if not os.path.isdir(os.path.dirname(self.json_path)):
            os.makedirs(os.path.dirname(self.json_path))
        with open(self.json_path, "w+") as file:
            json.dump(data, file)

    @property
    def current_page(self):
        return self.pages[self.current_page_index]


class Guides:
    def __init__(self, icon_dir=None, guides_json_dir: Union[str, Path] = None):
        self.guides = {}
        self.previews: previews.ImagePreviewCollection = previews.new(max_size=(1024,1024))
        self.icon_previews= bpy_previews.new()
        self.icons = {}
        self.icons_dir = icon_dir if icon_dir else Path(__file__).parent / "Guide Icons"
        self.guides_json_dir = (
            Path(__file__).parent.parent.parent / "CP Guides" if not guides_json_dir else Path(guides_json_dir)
        )
        self.load_icons()

    def new_guide(self, guide_id):
        guide = Guide(guide_id, self)
        self.add_guide(guide)
        return guide

    def add_guide(self, guide: Guide):
        self.guides[guide.id] = guide
        guide.data = self

    def load_icons(self):
        icons = ["next", "prev", "exit", "hint", "guide"]
        for icon in icons:
            if (self.icons_dir / f"{icon}.webp").exists():
                ic = self.icon_previews.load(icon, str(self.icons_dir / f"{icon}.webp"), "IMAGE")
                self.icons[icon] = ic.icon_id
    def get_icon(self, icon):
        return self.icons[icon]
    def remove_guide(self, guide: Union[str, Guide]):
        if isinstance(guide, str):
            guide = self.guides[guide]
        if guide in self.guides.values():
            del self.guides[guide.id]
        else:
            raise KeyError(f"Guide with id '{guide.id}' not found.")

    def __getattr__(self, attr):
        if attr in self.guides:
            return self.guides[attr]
        return None

    def __getitem__(self, key):
        return self.guides.get(key, None)

    def __iter__(self):
        return iter(self.guides.values())

    def __len__(self):
        return len(self.guides)

    def __delitem__(self, key):
        del self.guides[key]
