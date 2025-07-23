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
# (c) 2024 Jakub Uhlik

from . import debug

from . import config
from . import keys
from . import navigator
# from . import tools
from . import ops
from . import gizmos
from . import brushes

import bpy

classes = config.classes + keys.classes + navigator.classes + ops.classes + gizmos.classes + brushes.classes


# TODO: tools -->> to be moved and merged -->> curve.draw_bezier_area, related: ./curve/draw_bezier_area -->> update to multi surface?


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    keys.register_keyconfig()
    
    # TODO: maybe i could do it withou it? if so, i would have none of this register/unregister init/deinit stuff, which would be nice
    gizmos.init()
    
    # # NOTE: until module is merged, this need to be here
    # tools.init()


def unregister():
    # TODO: maybe i could do it withou it? if so, i would have none of this register/unregister init/deinit stuff, which would be nice
    gizmos.deinit()
    
    # # NOTE: until module is merged, this need to be here
    # tools.deinit()
    
    keys.unregister_keyconfig()
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


# NOTE $ pycodestyle --ignore=W293,E501,E741,E402 .
