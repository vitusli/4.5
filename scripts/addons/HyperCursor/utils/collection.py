import bpy

from . system import printd

def get_layer_collections_recursively(lcol, layer_collections):
    layer_collections.append(lcol)

    for lc in lcol.children:
        get_layer_collections_recursively(lc, layer_collections)

def is_collection_visible(col):
    C = bpy.context

    if col == C.scene.collection:
        return True

    if col.hide_viewport:
        return False

    viewlayer = C.view_layer

    layer_collections = []
    get_layer_collections_recursively(viewlayer.layer_collection, layer_collections)

    instances = [lcol for lcol in layer_collections if lcol.collection == col]

    return any(lcol.visible_get() for lcol in instances)

def get_scene_collections(context, debug=False):
    layer_collections = []
    get_layer_collections_recursively(context.view_layer.layer_collection, layer_collections)

    collections = {}

    for lcol in layer_collections:
        if lcol.collection == context.scene.collection:
            continue

        if (col := lcol.collection) in collections:
            collections[col]['layer_collections'].append(lcol)

        else:
            collections[col] = {'layer_collections': [lcol]}

    for col, data in collections.items():

        data['excluded'] = all(lcol.exclude for lcol in data['layer_collections'])

        data['hidden'] = col.hide_viewport or all(lcol.hide_viewport for lcol in data['layer_collections'])

        data['visible'] = any(lcol.visible_get() for lcol in data['layer_collections'])

    if debug:
        printd(collections)

    return collections

def get_wires_collection(context, name='_Wires', color_tag='COLOR_05', scene_collections=None, create=True, exclude=True, hide_viewport=None):
    if not scene_collections:
        scene_collections = get_scene_collections(context)

    wires_cols = [col for col in scene_collections if col.name.startswith('_Wires')]

    if wires_cols:
        return wires_cols[0]

    elif create:
        wcol = bpy.data.collections.new('_Wires')
        wcol.color_tag = color_tag
        context.scene.collection.children.link(wcol)

        set_collection_visibility(context, wcol, exclude=exclude, hide_viewport=hide_viewport)

        return wcol

def set_collection_visibility(context, collection, exclude=None, hide_viewport=None):
    if exclude is not None or hide_viewport is not None:
        layer_col = context.view_layer.layer_collection.children.get(collection.name)

        if not layer_col:
            scene_collections = get_scene_collections(context)

            for col, data in scene_collections.items():
                if col == collection:
                    layer_col = data['layer_collections'][0]
                    break

        if layer_col:
            if exclude is not None:
                layer_col.exclude = exclude

            if hide_viewport is not None:
                layer_col.hide_viewport = hide_viewport

        else:
            print(f"WARNING: Could not set visibility for collection {collection.name}, as no layer collection could be found on the view layer")

def ensure_visible_collection(context):
    active = context.view_layer.active_layer_collection

    if not active.visible_get():
        print(f"WARNING: Active Layer Collection '{active.name}' is hidden, switching to Scene Collection.")
        context.view_layer.active_layer_collection = context.view_layer.layer_collection
