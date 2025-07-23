
import bpy
from bpy.types import Context, Event
from bpy_extras.io_utils import ImportHelper,ExportHelper
import os
from .utils import *
import textwrap
import importlib
import subprocess
import os
import bpy
import addon_utils
import sys

preview_collections = {}
preview_list = {}

def install_fpdf():
    import pip
    pip.main(['install','fpdf'])
def check_fpdf():
    try:
        fpdf = importlib.import_module('fpdf')
    except ImportError:
        return False
    return True
def create_pdf(enabled_addons,disabled_addons, output_file):
    try:
        fpdf = importlib.import_module('fpdf')
    except ImportError:
        print("FPDF library not found. Installing...")
        install_fpdf()
        fpdf = importlib.import_module('fpdf')

    pdf = fpdf.FPDF()
    pdf.add_page()
        
    pdf.set_fill_color(192, 192, 192)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(5, 10, "Enabled Addons:",ln=1)
    # Create table header
    pdf.cell(60, 10, "Addon", 1, 0, "C", True)
    pdf.cell(130, 10, "Description", 1, 1, "C", True)

    # Set font style for table body
    pdf.set_fill_color(255, 255, 255)
    pdf.set_font("Arial", size=12)
    for title, description in enabled_addons:
        pdf.cell(60, 10, title, 1, 0, "L", True)
        pdf.multi_cell(130, 10, description, 1, "L", True)
    pdf.ln(5) 
    pdf.set_fill_color(192, 192, 192)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(5, 10, "Disabled Addons:",ln=1)
    pdf.cell(60, 10, "Addon", 1, 0, "C", True)
    pdf.cell(130, 10, "Description", 1, 1, "C", True)
    
    # Set font style for table body
    pdf.set_fill_color(255, 255, 255)
    pdf.set_font("Arial", size=12)
    for title, description in disabled_addons:
        pdf.cell(60, 10, title, 1, 0, "L", True)
        pdf.multi_cell(130, 10, description, 1, "L", True)

    # Save the PDF
    pdf.output(output_file)
def create_txt(enabled_addons,disabled_addons, output_file):
    
    with open(output_file,mode='w+',encoding='UTF-8') as file:
        file.write("Enabled Addons:\n\n\n\n")
        for title, description in enabled_addons:
            file.write(f"{title}:\n{description}\n\n")
        file.write("\n\n\n\n")
        file.write("Disabled Addons:\n\n\n\n")
        for title, description in disabled_addons:
            file.write(f"{title}:{description}\n\n")

def get_all_addon_names():
    enabled_addons=[(addon_utils.module_bl_info(a)['name'],addon_utils.module_bl_info(a)['description']) for a in addon_utils.modules() if addon_utils.check(a.__name__)[1]]
    disabled_addons=[(addon_utils.module_bl_info(a)['name'],addon_utils.module_bl_info(a)['description']) for a in addon_utils.modules() if not addon_utils.check(a.__name__)[1]]
    enabled_addons=sorted(enabled_addons,key=lambda x: x[1].lower())
    disabled_addons=sorted(disabled_addons,key=lambda x: x[1].lower())
    return enabled_addons,disabled_addons


class CP_OT_Export(bpy.types.Operator,ExportHelper):
    bl_idname = 'cp.exportaddonslist'
    bl_label = 'Export Addons List'
    bl_description = "Export addons list as txt or pdf file"
    bl_options = {'REGISTER', }
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Filepath used for exporting the file",
        subtype='FILE_PATH',
    )
    filename_ext:bpy.props.EnumProperty(items=[('.txt','Text','Text'),('.pdf','PDF','PDF')],default=".txt",options={'SKIP_SAVE','HIDDEN'})
    def draw(self,context):
        self.layout.label(text='Export as:')
        self.layout.prop(self,'filename_ext',expand=True)
        if self.filename_ext=='.pdf' and not check_fpdf():
            box=self.layout.box()

            lines = textwrap.wrap("FPDF module is not installed! Make sure Blender has been started with Admin Rights to allow for successful installation!",context.region.width/10 if context else 100, break_long_words=False)
            for i,l in enumerate(lines):
                box.label(text=l,icon='ERROR' if i==0 else 'NONE')
            box.alert=True
    def execute(self, context):
        if self.filename_ext=='.txt':
            create_txt(get_all_addon_names()[0],get_all_addon_names()[1], self.filepath)
        else:
            try:
                create_pdf(get_all_addon_names()[0],get_all_addon_names()[1], self.filepath)
            except ImportError:
                self.report({'WARNING'},'FPDF module could not be installed! Make sure Blender has been started with Admin Rights to allow for successful installation!')
        if os.path.exists(self.filepath):
            bpy.ops.wm.path_open(filepath=os.path.dirname(self.filepath))
        return {'FINISHED'}
    
def addToSideBar(self, context):
    layout=self.layout
    layout.operator("cp.exportaddonslist",icon='EXPORT')

classes = (
    CP_OT_Export,
)

icon_collection={}
addon_keymaps = []

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
    
    
    
    # bpy.types.USERPREF_PT_navigation_bar.append(addToSideBar)
def unregister():

    from bpy.utils import unregister_class

    for cls in reversed(classes):
        unregister_class(cls)
    # try:
    #     bpy.types.USERPREF_PT_navigation_bar.remove(addToSideBar)
    # except Exception:
    #     pass

