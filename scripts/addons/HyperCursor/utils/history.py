from typing import Union
import bpy
import re

from mathutils import Matrix, Vector

from . property import get_biggest_index_among_names

def add_history_entry(mx:Union[Matrix, None]=None, name='', debug=False):
    context = bpy.context

    hc = context.scene.HC

    if mx is None:
        mx = context.scene.cursor.matrix

    loc, rot, _ = mx.decompose()

    h = hc.historyCOL.add()
    h.mx = Matrix.LocRotScale(loc, rot, Vector((1, 1, 1)))
    h.location = loc
    h.rotation = rot.to_matrix()

    if name:

        names = [h.name for h in hc.historyCOL if name in h.name]

        if names:
            idx = get_biggest_index_among_names(names)

            if idx:
                h.name = f"{name}.{str(idx + 1).zfill(3)}"

            else:
                h.name = f"{name}.001"
        else:
            h.name = name

    newidx = hc.historyIDX + 1

    hc.historyIDX = newidx

    if newidx != len(hc.historyCOL) - 1:
        hc.historyCOL.move(len(hc.historyCOL) - 1, newidx)

    prettify_history(context)

    if debug:
        print(f"INFO: Added new Cursor History entry at {hc.historyIDX}/{len(hc.historyCOL) - 1}")

def prettify_history(context):
    historyCOL = context.scene.HC.historyCOL

    nameidx = 0
    nameRegex = re.compile(r"Cursor\.[\d]{3}")

    for idx, entry in enumerate(historyCOL):
        entry.index = idx

        mo = nameRegex.match(entry.name)

        if not (entry.name and not mo):
            entry.name = f"Cursor.{str(nameidx).zfill(3)}"
            nameidx += 1
