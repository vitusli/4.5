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

################################################################################################
# ooooooooooooo                                         oooo                .
# 8'   888   `8                                         `888              .o8
#      888      oooo d8b  .oooo.   ooo. .oo.    .oooo.o  888   .oooo.   .o888oo  .ooooo.
#      888      `888""8P `P  )88b  `888P"Y88b  d88(  "8  888  `P  )88b    888   d88' `88b
#      888       888      .oP"888   888   888  `"Y88b.   888   .oP"888    888   888ooo888
#      888       888     d8(  888   888   888  o.  )88b  888  d8(  888    888 . 888    .o
#     o888o     d888b    `Y888""8o o888o o888o 8""888P' o888o `Y888""8o   "888" `Y8bod8P'
################################################################################################

import os
import re
import csv
from datetime import datetime

#Some Globals
TRSLGHERE, NOTINPLUG = "🟥🟥TRANSLATE_HERE🟥🟥", "🟧🟧NOT_IN_PLUGIN🟧🟧"
TRANSLATIONS, ACTIVE_LANG, ENUM_LANG_ITEMS = {}, None, []


def get_active_language():
    """get the active language from the stored '_user_active_language.txt'"""
    
    current_dir = os.path.dirname(__file__)
    active_lg_file = os.path.join(current_dir, "_user_active_language.txt")
    
    if (os.path.exists(active_lg_file)):
        content = None
        with open(active_lg_file, 'r', encoding='utf-8') as txtfile:
            content = txtfile.read()
        return content
    
    #create file if does not exist
    content = "English"
    with open(active_lg_file, 'w', encoding='utf-8') as txtfile:
        txtfile.write(content)
    
    return content

    
def load_translations_csv():
    """load all .csv translations into one giant global dict"""
    
    #fill global translation dict
        
    global TRANSLATIONS
    TRANSLATIONS.clear()
    
    current_dir = os.path.dirname(__file__)
    for root, _, files in os.walk(current_dir):
        for file in files:
            if file.endswith(".csv"):
                file_path = os.path.join(root, file)

                if (file in TRANSLATIONS.keys()):
                    print(f"ERROR: load_translations_csv(): {file} already in TRANSLATIONS.keys()?")
                    continue
                
                file_name = file.replace('.csv','')
                T = TRANSLATIONS[file_name] = {}

                with open(file_path, 'r', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    
                    for row in reader:
                        if (len(row)>=2):  # Make sure there are at least two columns
                            Tkey = row[0]
                            Tval = row[1]
                            T[Tkey] = Tval
                        else: print(f"ERROR: load_translations_csv(): {file_path} doesn't follow 'Translation.csv' format?")
    
    #dynamically create the gui pointer property items
    
    global ENUM_LANG_ITEMS
    ENUM_LANG_ITEMS.clear()
    
    if (TRANSLATIONS):
        ENUM_LANG_ITEMS.append(("English","English","Base plugin language"))
        for k in TRANSLATIONS.keys():
            ENUM_LANG_ITEMS.append((k,k,f"Traductions from '../Plugin/traductions/{k}.csv'"))
    else:
        ENUM_LANG_ITEMS.append(("English","No 'Language.csv' Found","We did not find any '.csv' files in '../Plugin/traductions/'"))
    
    #get the translation the user chose in his addon_prefs()
    
    if (TRANSLATIONS):
        global ACTIVE_LANG
        active_lg = get_active_language()
        if ((active_lg) and (ACTIVE_LANG!=active_lg)):
            ACTIVE_LANG = active_lg
    
    return None


def translate(txt, context=None):
    """translate this string"""
    
    global ACTIVE_LANG
    if ((not ACTIVE_LANG) or (ACTIVE_LANG=="English")):
        return txt
    if (not txt):
        return ''
    
    global TRANSLATIONS
    if (TRANSLATIONS):
        T = TRANSLATIONS.get(ACTIVE_LANG)
        if (T):
            normalized = repr(txt)[1:-1]
            translation = T.get(normalized)
            if ((translation) and (translation!=TRSLGHERE)):
                return translation
            else:
                print(f'ERROR: translte("{normalized}")->{translation}')
                        
    return txt


def upd_language(self, context):
    """when user change addon_prefs().language, it will change '.activelanguage' file in his folder"""
    
    active_lg = get_active_language()
    
    if (active_lg!=self.language):
        
        current_dir = os.path.dirname(__file__)
        active_lg_file = os.path.join(current_dir, "_user_active_language.txt")
        
        with open(active_lg_file, 'w', encoding='utf-8') as txtfile:
            txtfile.write(self.language)
    
    return None


if (__name__ == "__main__"):
    
    #EXECUTE THIS .PY FILE TO GENERATE OR UPDATE A .CSV TRANSLATION DICT
    
    # Function to recursively search for .py files and extract translation strings
    def scan_directory(directory):
        
        def extract_translations(file_path):
            """Function to extract all strings encapsulated between translate functions from a file"""
            
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # Regex pattern to capture strings
            pattern = re.compile(r'translate\("([^"]+)"\)')
            matches = pattern.findall(content)
            
            return matches
        
        translation_dict = {}

        # Traverse the directory and its subdirectories
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith(".py"):
                    file_path = os.path.join(root, file)
                    translations = extract_translations(file_path)

                    # Add translations to the dictionary with the filename
                    for translation in translations:
                        if translation not in translation_dict:
                            translation_dict[translation] = set()
                        translation_dict[translation].add(file)

        return translation_dict

    # Function to write the dictionary to a CSV file and update existing rows
    def write_to_csv(csv_file, translation_dict):
        
        existing_data = {}
        current_datetime = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # If the CSV file exists, read its content and update it
        if (os.path.exists(csv_file)):
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    if (row):  # To avoid empty rows
                        key = row[0]
                        translation = row[1] if row[1] else TRSLGHERE
                        files = set(row[2].split(' / ')) if len(row) > 2 else set()
                        date = row[3] if bool(row[3].strip()) else current_datetime
                        existing_data[key] = {'translation': translation, 'files': files, 'date':date, }

        # Update the CSV data with new translations
        for key, files in translation_dict.items():
            if (key in existing_data):
                  existing_data[key]['files'].update(files)  # Merge file lists
            else: existing_data[key] = {'translation': TRSLGHERE, 'files': files, 'date':current_datetime}

        # Tag keys that are no linker in plugin
        for key in existing_data.keys():
            if (key not in translation_dict):
                existing_data[key]['files'] = NOTINPLUG
        
        # Sort the keys alphabetically
        sorted_keys = sorted(existing_data.keys())

        # Write the updated and alphabetically sorted data to the CSV file
        with open(csv_file, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            for key in sorted_keys:
                r_english = key
                r_translt = existing_data[key]['translation']
                r_files   = NOTINPLUG if (existing_data[key]['files']==NOTINPLUG) else ' / '.join(existing_data[key]['files'])
                r_date    = existing_data[key]['date']
                
                writer.writerow([r_english, r_translt, r_files, r_date])
                continue
            
        return None
    
    current_dir = os.path.dirname(__file__)
    plugin_path = os.path.dirname(current_dir)
    csv_path    = os.path.join(current_dir, "Français.csv")
    
    # Get the translations
    translation_dict = scan_directory(plugin_path)
    
    # Write the translations to a CSV file, update csv with new inputs if needed
    write_to_csv(csv_path, translation_dict)
        