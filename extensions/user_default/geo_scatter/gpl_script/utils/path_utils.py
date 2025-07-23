"""
• Script License: 

    This python script file is licensed under GPL 3.0
    
    This program is free software; you can redistribute it and/or modify it under 
    the terms of the GNU General Public License as published by the Free Software
    Foundation; either version 3 of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
    without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
    See the GNU General Public License for more details.
    
    See full license on 'https://www.gnu.org/licenses/gpl-3.0.en.html#license-text'

• Additonal Information: 

    The components in this archive are a mere aggregation of independent works. 
    The GPL-licensed scripts included here serve solely as a control and/or interface for 
    the Geo-Scatter geometry-node assets.

    The content located in the 'PluginFolder/non_gpl/' directory is NOT licensed under 
    the GPL. For details, please refer to the LICENSES.txt file within this folder.

    The non-GPL components and assets can function fully without the scripts and vice versa. 
    They do not form a derivative work, and are distributed together for user convenience.

    Redistribution, modification, or unauthorized use of the content in the 'non_gpl' folder,
    including .blend files or image files, is prohibited without prior written consent 
    from BD3D DIGITAL DESIGN, SLU.
        
• Trademark Information:

    Geo-Scatter® name & logo is a trademark or registered trademark of “BD3D DIGITAL DESIGN, SLU” 
    in the U.S. and/or European Union and/or other countries. We reserve all rights to this trademark. 
    For further details, please review our trademark and logo policies at “www.geoscatter.com/legal”. The 
    use of our brand name, logo, or marketing materials to distribute content through any non-official
    channels not listed on “www.geoscatter.com/download” is strictly prohibited. Such unauthorized use 
    falsely implies endorsement or affiliation with third-party activities, which has never been granted. We 
    reserve all rights to protect our brand integrity & prevent any associations with unapproved third parties.
    You are not permitted to use our brand to promote your unapproved activities in a way that suggests official
    endorsement or affiliation. As a reminder, the GPL license explicitly excludes brand names from the freedom,
    our trademark rights remain distinct and enforceable under trademark laws.

"""
# A product of “BD3D DIGITAL DESIGN, SLU”
# Authors:
# (c) 2024 Dorian Borremans


import bpy

import os
import json
import glob
import shlex
import platform
import subprocess
        
from .. translations import translate


#NOTE extension of the os.path module i guess? 

def dict_to_json(d, path="", file_name="", extension=".json", ):
    """ dict > .json, will write json to disk"""

    json_path = os.path.join( path, f"{file_name}{extension}" ) #filename = w o extension!!!
    with open(json_path, 'w') as f:
        json.dump(d, f, indent=4)

    return None

def json_to_dict(path="", file_name=""):
    """.json -> dict"""

    json_path = os.path.join( path, file_name )

    if (not os.path.exists(json_path)):
        print(f"path_utils.json_to_dict() -> it seems that the json file do not exists? [{json_path}]")
        return {}

    with open(json_path) as f:
        d = json.load(f)

    return d

def get_direct_folder_paths(main):
    """get all directories paths within given path"""
    
    for _, dirnames, _ in os.walk(main):
        return [os.path.join(main,d) for d in dirnames]
    
    return []

def get_direct_files_paths(main):
    """get all files paths within given path"""
    
    for _, _, files in os.walk(main):
        return [os.path.join(main,d) for d in files]

def get_subpaths(folder, file_type="", excluded_files=[], excluded_folders=[".git","__pycache__",],):
    """get all existing files paths within the given folder"""
    
    r = []
    
    for main, dirs, files in os.walk(folder, topdown=True):
        dirs[:] = [d for d in dirs if d not in excluded_folders]
        
        if (excluded_files!=[]):
            files = [f for f in files if f not in excluded_files]
            
        for file in files:
            if ( (file_type!="") and (not file.endswith(file_type)) ):
                continue
            r.append(os.path.join(main,file))
            continue
        
    return r

def get_parentfolder(folder="", depth=1,):
    """get parent folder from given depth"""

    for _ in range(depth):
        folder = os.path.dirname(folder)

    return folder

def glob_subfolders(folder="", depth="all",):
    """get list of folders at given depths"""

    folder = glob.escape(folder) #sanatize user string, in case of special character

    if (depth=="all"):
        
        arg = os.path.join(folder,"**/")

        return glob.glob(arg, recursive=True,)

    elif (depth>=0):

        lvl = "*/"*(depth+1)
        arg = os.path.join(folder,lvl)

        return glob.glob(arg, recursive=True,)
    
    elif (depth<0):

        depth = abs(depth)
        folder = get_parentfolder(folder, depth=depth)
        arg = os.path.join(folder,"*/")

        return glob.glob(arg, recursive=True,)

    raise Exception("glob_subfolders() -> bad depth arg")  

def folder_match_search(folder="C:/", folderdepth=0, file="file.txt",):
    """search by overviewing all folders and checking if file exists at these locations
    is faster method, as simply doing os.exists check instead of systematic full file search"""

    if (folderdepth==0):
        filepath = os.path.join(folder,file)
        if (os.path.exists(filepath)):
            return filepath

    for f in glob_subfolders(folder=folder, depth=folderdepth,):
        f = os.path.normpath(f)
        filepath = os.path.join(f,file)
        
        if (os.path.exists(filepath)):
            return filepath
        
        continue

    return ""

def search_for_path(keyword="", search_first=None, full_search_folder=None, search_others=None, search_others_depth=3, file_type="",):
    """search everywhere for a file, if found, return it's path else return None, 
    the search order is the following:
       1) "search_first" check if exists in level 0 & 1
       2) "search_first" check if exists in level -1
       3) "full_search_folder" check if exists in all subfolders
       4) "search_others" check if exists in folder levels, 0 to 3 level
    """

    #TODO could improve this function, used consistently in biome loading!

    if (file_type):
        if (not keyword.endswith(file_type)):
            keyword += file_type

    #first try to search in priority folder
    if (search_first is not None):

        if (not os.path.exists(search_first)):
            raise Exception("The path you gave doesn't exists (search_first)")

        #file exists in +1 level or level 0?
        p = folder_match_search(folder=search_first, folderdepth=0, file=keyword,)
        if (p):
            return p

        #in parent folder? level -1?
        p = os.path.join(os.path.dirname(search_first),keyword)
        if (os.path.exists(p)):
            return p

    #else search everywhere in main library
    if (full_search_folder is not None):
        
        if (not os.path.exists(full_search_folder)):
            raise Exception("The path you gave doesn't exists")

        p = folder_match_search(folder=full_search_folder, folderdepth="all", file=keyword,)
        if (p):
            return p

    #else search in collection of other paths given
    if (search_others is not None):
        
        search_others = [pt for pt in search_others if (os.path.exists(pt))]
        
        if (len(search_others)==0):
            print("WARNING: search_for_path(): search_others list is empty")
            
        #exists in level 0 or level 1 ? or above
        for dep in range(search_others_depth+1):
            for pt in search_others:
                p = folder_match_search(folder=pt, folderdepth=dep, file=keyword,)
                if (p):
                    return p

    return "" #nothing found 


# def search_for_paths(search_paths, keywords,):
#     """https://stackoverflow.com/questions/74113035/fastest-way-to-search-many-files-in-many-directories/74113561#74113561"""

#     for p in search_paths:
#         if (not os.path.exists(p)):
#             raise Exception(f"following path do not exists: {p}")

#     def process_directory(directory):
#         output = []
#         for root, _, files in os.walk(directory):
#             for file in files:
#                 if (file in keywords):
#                     output.append(os.path.join(root, file))
#                     keywords.remove(file)
#         return output

#     paths = []

#     from concurrent.futures import ThreadPoolExecutor

#     with ThreadPoolExecutor() as executor:
#         for rv in executor.map(process_directory, search_paths):
#             paths.extend(rv)

#     return keywords, paths



#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


class SCATTER5_OT_open_directory(bpy.types.Operator):

    bl_idname      = "scatter5.open_directory"
    bl_label       = translate("Open Directory")
    bl_description = translate("Open a new file explorer window with a new path")

    folder : bpy.props.StringProperty(default="", options={"SKIP_SAVE",},)

    def execute(self, context):
                    
        if (os.path.exists(self.folder)):
            match platform.system():
                case 'Windows':
                    os.startfile(self.folder)
                case 'Linux':
                    subprocess.call(['xdg-open', self.folder])
                case 'Darwin':
                    os.system('open {}'.format(shlex.quote(self.folder)))
                case _:
                    print("WARNING: SCATTER5_OT_open_directory(): Unsupported OS")
        else:
            bpy.ops.scatter5.popup_menu(msgs=translate("The folder you are trying to open does not exist")+f"\n{self.folder}",title=translate("Error!"),icon="ERROR")
            return {'CANCELLED'}             

        return {'FINISHED'} 


#   .oooooo.   oooo
#  d8P'  `Y8b  `888
# 888           888   .oooo.    .oooo.o  .oooo.o  .ooooo.   .oooo.o
# 888           888  `P  )88b  d88(  "8 d88(  "8 d88' `88b d88(  "8
# 888           888   .oP"888  `"Y88b.  `"Y88b.  888ooo888 `"Y88b.
# `88b    ooo   888  d8(  888  o.  )88b o.  )88b 888    .o o.  )88b
#  `Y8bood8P'  o888o `Y888""8o 8""888P' 8""888P' `Y8bod8P' 8""888P'


classes = (

    SCATTER5_OT_open_directory,

    )
